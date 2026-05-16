# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import json
from pathlib import Path

from legal_text_mcp_de.legal_texts.state_law import run_state_law_adapters
from legal_text_mcp_de.legal_texts.state_law_inventory import (
    DEFAULT_STATE_LAW_LIMITATIONS_PATH,
    DEFAULT_STATE_LAW_INVENTORY_PATH,
    load_state_law_inventory,
    load_state_law_limitations,
)
from scripts.verify_state_law_pdf_sources import main as verify_state_law_pdf_sources_main


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "state_law"


def build_phase9_fixture(tmp_path: Path) -> tuple[dict, Path]:
    inventory = load_state_law_inventory(DEFAULT_STATE_LAW_INVENTORY_PATH)
    limitations = load_state_law_limitations(DEFAULT_STATE_LAW_LIMITATIONS_PATH)
    bb = (FIXTURE_DIR / "official_like_bb.html").read_bytes()
    nw = (FIXTURE_DIR / "official_like_nw.html").read_bytes()
    malformed = (FIXTURE_DIR / "malformed_html_law.html").read_bytes()
    by_url = {
        next(record for record in inventory["states"] if record["state_code"] == "BB")["official_sources"][0]["url"]: bb,
        next(record for record in inventory["states"] if record["state_code"] == "NW")["official_sources"][0]["url"]: nw,
    }

    def fake_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
        return 200, {"content-type": "text/html; charset=utf-8"}, by_url.get(url, malformed)

    result = run_state_law_adapters(
        inventory,
        limitations,
        package_dir=tmp_path / "package",
        retrieved_at="2026-05-15T00:00:00Z",
        fetch=fake_fetch,
    )
    artifact = {
        "schema_version": "state-law-adapter-gate.v1",
        "generated_at": "2026-05-15T00:00:00Z",
        "counts": {
            "imported": result.terminal_state_counts.get("imported", 0),
            "source_limitations": len(result.source_limitations),
        },
        "source_outcomes": result.source_outcomes,
        "validation_errors": result.validation_errors,
    }
    return artifact, tmp_path / "package"


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_state_law_pdf_gate_writes_zero_pdf_coverage_without_manual_text(tmp_path):
    phase9, package_dir = build_phase9_fixture(tmp_path)
    phase9_path = tmp_path / "adapter-gate.json"
    output = tmp_path / "pdf-gate.json"
    write_json(phase9_path, phase9)
    before_laws = (package_dir / "laws.json").read_text(encoding="utf-8")
    before_norms = (package_dir / "norms.json").read_text(encoding="utf-8")

    exit_code = verify_state_law_pdf_sources_main([
        "--inventory",
        str(DEFAULT_STATE_LAW_INVENTORY_PATH),
        "--phase9-outcomes",
        str(phase9_path),
        "--package-dir",
        str(package_dir),
        "--output",
        str(output),
    ])

    assert exit_code == 0
    gate = json.loads(output.read_text(encoding="utf-8"))
    coverage = json.loads((package_dir / "state-law-coverage.json").read_text(encoding="utf-8"))
    assert gate["schema_version"] == "state-law-pdf-source-gate.v1"
    assert gate["counts"]["total_states"] == 16
    assert gate["counts"]["imported"] == 2
    assert gate["counts"]["limited"] == 14
    assert gate["counts"]["pdf_source_count"] == 0
    assert gate["counts"]["pdf_extraction_count"] == 0
    assert gate["validation_errors"] == []
    assert coverage["counts"] == gate["counts"]
    assert (package_dir / "laws.json").read_text(encoding="utf-8") == before_laws
    assert (package_dir / "norms.json").read_text(encoding="utf-8") == before_norms


def test_state_law_pdf_gate_fails_missing_terminal_coverage(tmp_path):
    phase9, package_dir = build_phase9_fixture(tmp_path)
    phase9["source_outcomes"].pop("state:bb/brandenburgisches-datenschutzgesetz")
    phase9_path = tmp_path / "adapter-gate.json"
    output = tmp_path / "pdf-gate.json"
    write_json(phase9_path, phase9)

    exit_code = verify_state_law_pdf_sources_main([
        "--inventory",
        str(DEFAULT_STATE_LAW_INVENTORY_PATH),
        "--phase9-outcomes",
        str(phase9_path),
        "--package-dir",
        str(package_dir),
        "--output",
        str(output),
    ])

    assert exit_code == 1
    gate = json.loads(output.read_text(encoding="utf-8"))
    assert any("missing phase9 outcome for state:bb/brandenburgisches-datenschutzgesetz" in error for error in gate["validation_errors"])
