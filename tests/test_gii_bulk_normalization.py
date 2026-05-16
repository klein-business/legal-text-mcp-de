# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import json
from pathlib import Path

from legal_text_mcp_de.legal_texts.dataset import NormalizedDataset
from legal_text_mcp_de.legal_texts.gii_bulk import (
    CRITICAL_GII_SOURCE_PATHS,
    build_gii_corpus_gate_artifact,
    critical_law_gate_errors,
    run_gii_bulk_normalization,
    write_gii_corpus_gate_artifact,
)
from legal_text_mcp_de.legal_texts.gii_toc import DEFAULT_GII_TOC_URL
from legal_text_mcp_de.legal_texts.manifest import validate_corpus_manifest
from legal_text_mcp_de.legal_texts.validation import validate_generated_package
from scripts.verify_gii_corpus_gate import main as verify_gii_corpus_gate_main


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "gii_bulk"
PAYLOAD_DIR = FIXTURE_DIR / "payloads"
PARSER_MATRIX = FIXTURE_DIR / "parser_variant_matrix.json"
UPSTREAM_LIMITATIONS = FIXTURE_DIR / "upstream_limitations.json"


def discovery_artifact() -> dict:
    records = [
        discovered("bgb"),
        discovered("bdsg_2018"),
        discovered("ttdsg"),
        discovered("bgbeg"),
        discovered("missing-law"),
        discovered("unsupported-law"),
        discovered("parsefail"),
    ]
    return {
        "schema_version": "gii-discovery-artifact.v1",
        "toc_url": DEFAULT_GII_TOC_URL,
        "retrieved_at": "2026-05-15T00:00:00Z",
        "toc_sha256": "fixture-toc",
        "parser_version": "test",
        "discovered_gii_items": len(records),
        "discovered_gii_records": records,
        "source_paths": sorted(record["source_path"] for record in records),
        "source_path_count": len(records),
        "duplicate_count": 0,
        "malformed_items": [],
        "toc_limitation": None,
        "validation_errors": [],
    }


def discovered(source_path: str) -> dict:
    xml_zip_url = f"https://www.gesetze-im-internet.de/{source_path}/xml.zip"
    return {
        "source_family": "gii",
        "source_id": f"gii:{source_path}",
        "source_path": source_path,
        "index_url": f"https://www.gesetze-im-internet.de/{source_path}/index.html",
        "xml_zip_url": xml_zip_url,
        "toc_url": DEFAULT_GII_TOC_URL,
        "toc_sha256": "fixture-toc",
        "source_metadata": {
            "source_path": source_path,
            "index_url": f"https://www.gesetze-im-internet.de/{source_path}/index.html",
            "xml_zip_url": xml_zip_url,
            "toc_url": DEFAULT_GII_TOC_URL,
            "original_link": xml_zip_url,
        },
        "alias_candidates": [source_path],
    }


def assert_has_error(errors: list[str], expected: str) -> None:
    assert any(expected in error for error in errors), errors


def test_bulk_normalization_assigns_terminal_states_and_validates_generated_package(tmp_path):
    package_dir = tmp_path / "package"

    result = run_gii_bulk_normalization(
        discovery_artifact(),
        payload_dir=PAYLOAD_DIR,
        package_dir=package_dir,
        retrieved_at="2026-05-15T00:00:00Z",
    )

    assert result.terminal_state_counts == {
        "imported": 4,
        "source_unavailable": 1,
        "unsupported_format": 1,
        "parse_failed": 1,
    }
    assert sorted(law["canonical_id"] for law in result.laws) == ["bdsg_2018", "bgb", "egbgb", "tdddg"]
    assert {law["canonical_id"]: law["norm_count"] for law in result.laws}["egbgb"] == 2
    assert len(result.source_limitations) == 3
    assert validate_corpus_manifest(result.manifest, require_terminal_states=True) == []
    assert validate_generated_package(package_dir, require_search_index=True) == []

    dataset = NormalizedDataset.load(package_dir, require_search_index=True)
    assert dataset.get_norm_by_id("bdsg_2018", "par:1")["text"]
    assert dataset.get_norm_by_id("tdddg", "par:25")["text"]
    assert dataset.get_norm_by_id("egbgb", "art:246a")["unit"] == "container"
    assert dataset.get_norm_by_id("egbgb", "art:246a/par:1")["text"]


def test_generated_gii_package_preserves_existing_canonical_aliases_and_source_path_provenance(tmp_path):
    package_dir = tmp_path / "package"
    result = run_gii_bulk_normalization(
        discovery_artifact(),
        payload_dir=PAYLOAD_DIR,
        package_dir=package_dir,
        retrieved_at="2026-05-15T00:00:00Z",
    )

    dataset = NormalizedDataset.load(package_dir, require_search_index=True)
    assert dataset.get_law("TDDDG")["law"]["canonical_id"] == "tdddg"
    assert dataset.get_law("BDSG")["law"]["canonical_id"] == "bdsg_2018"
    tdddg_norm = dataset.get_norm_by_id("tdddg", "par:25")
    assert tdddg_norm["law_id"] == "tdddg"
    assert tdddg_norm["canonical_id"] == "tdddg/par:25"
    assert tdddg_norm["source"]["source_metadata"]["source_path"] == "ttdsg"

    tdddg_law = next(law for law in result.laws if law["canonical_id"] == "tdddg")
    assert tdddg_law["source"]["source_identifier"] == "ttdsg"
    assert tdddg_law["source"]["source_metadata"]["source_path"] == "ttdsg"
    imported_manifest = next(record for record in result.manifest["discovered_sources"] if record["source_path"] == "ttdsg")
    assert imported_manifest["source_id"] == "gii:ttdsg"
    assert imported_manifest["generated_law_ids"] == ["tdddg"]
    assert imported_manifest["generated_norm_ids"] == ["tdddg/par:25"]


def test_generated_gii_package_preserves_structural_article_container(tmp_path):
    package_dir = tmp_path / "package"
    run_gii_bulk_normalization(
        discovery_artifact(),
        payload_dir=PAYLOAD_DIR,
        package_dir=package_dir,
        retrieved_at="2026-05-15T00:00:00Z",
    )

    dataset = NormalizedDataset.load(package_dir, require_search_index=True)
    container = dataset.get_norm_by_id("egbgb", "art:246a")
    child = dataset.get_norm_by_id("egbgb", "art:246a/par:1")
    assert container["unit"] == "container"
    assert container["status"] == "container"
    assert "text" not in container
    assert container["children"] == ["egbgb/art:246a/par:1"]
    assert child["law_id"] == "egbgb"


def test_source_limitations_represent_failures_without_fake_laws(tmp_path):
    result = run_gii_bulk_normalization(
        discovery_artifact(),
        payload_dir=PAYLOAD_DIR,
        package_dir=tmp_path / "package",
        retrieved_at="2026-05-15T00:00:00Z",
    )

    law_ids = {law["canonical_id"] for law in result.laws}
    assert "missing-law" not in law_ids
    assert "unsupported-law" not in law_ids
    assert "parsefail" not in law_ids
    limitations = {item["source_id"]: item for item in result.source_limitations}
    assert limitations["gii:missing-law"]["terminal_state"] == "source_unavailable"
    assert limitations["gii:unsupported-law"]["terminal_state"] == "unsupported_format"
    assert limitations["gii:parsefail"]["terminal_state"] == "parse_failed"


def test_critical_law_gate_passes_for_imported_resolvable_laws(tmp_path):
    result = run_gii_bulk_normalization(
        discovery_artifact(),
        payload_dir=PAYLOAD_DIR,
        package_dir=tmp_path / "package",
        retrieved_at="2026-05-15T00:00:00Z",
    )

    assert CRITICAL_GII_SOURCE_PATHS == {"bdsg_2018", "ttdsg"}
    assert critical_law_gate_errors(result) == []


def test_critical_law_gate_fails_missing_local_payload_by_default(tmp_path):
    artifact = discovery_artifact()
    payload_dir = tmp_path / "payloads"
    payload_dir.mkdir()
    for path in ("bgb", "ttdsg"):
        (payload_dir / f"{path}.zip").write_bytes((PAYLOAD_DIR / f"{path}.zip").read_bytes())

    result = run_gii_bulk_normalization(
        artifact,
        payload_dir=payload_dir,
        package_dir=tmp_path / "package",
        retrieved_at="2026-05-15T00:00:00Z",
    )

    errors = critical_law_gate_errors(result)
    assert_has_error(errors, "critical law bdsg_2018 has forbidden terminal_state source_unavailable")


def test_critical_law_gate_allows_explicit_release_blocking_upstream_unavailable(tmp_path):
    artifact = discovery_artifact()
    payload_dir = tmp_path / "payloads"
    payload_dir.mkdir()
    for path in ("bgb", "ttdsg"):
        (payload_dir / f"{path}.zip").write_bytes((PAYLOAD_DIR / f"{path}.zip").read_bytes())

    result = run_gii_bulk_normalization(
        artifact,
        payload_dir=payload_dir,
        package_dir=tmp_path / "package",
        retrieved_at="2026-05-15T00:00:00Z",
        upstream_limitations=json.loads(UPSTREAM_LIMITATIONS.read_text(encoding="utf-8")),
    )

    errors = critical_law_gate_errors(result)
    assert not any("bdsg_2018" in error for error in errors)


def test_critical_law_gate_rejects_upstream_limitation_without_required_evidence(tmp_path):
    artifact = discovery_artifact()
    payload_dir = tmp_path / "payloads"
    payload_dir.mkdir()
    for path in ("bgb", "ttdsg"):
        (payload_dir / f"{path}.zip").write_bytes((PAYLOAD_DIR / f"{path}.zip").read_bytes())
    limitations = json.loads(UPSTREAM_LIMITATIONS.read_text(encoding="utf-8"))
    limitations[0]["details"]["official_upstream_evidence"] = False

    result = run_gii_bulk_normalization(
        artifact,
        payload_dir=payload_dir,
        package_dir=tmp_path / "package",
        retrieved_at="2026-05-15T00:00:00Z",
        upstream_limitations=limitations,
    )

    errors = critical_law_gate_errors(result)
    assert_has_error(errors, "critical law bdsg_2018 has forbidden terminal_state source_unavailable")


def test_critical_law_gate_fails_for_reachable_parse_failed_or_unsupported(tmp_path):
    artifact = discovery_artifact()
    payload_dir = tmp_path / "payloads"
    payload_dir.mkdir()
    for source, target in (("parsefail", "bdsg_2018"), ("unsupported", "ttdsg")):
        suffix = ".zip" if source == "parsefail" else ".txt"
        (payload_dir / f"{target}{suffix}").write_bytes((PAYLOAD_DIR / f"{source}{suffix}").read_bytes())

    result = run_gii_bulk_normalization(
        artifact,
        payload_dir=payload_dir,
        package_dir=tmp_path / "package",
        retrieved_at="2026-05-15T00:00:00Z",
    )

    errors = critical_law_gate_errors(result)
    assert_has_error(errors, "critical law bdsg_2018 has forbidden terminal_state parse_failed")
    assert_has_error(errors, "critical law ttdsg has forbidden terminal_state unsupported_format")


def test_gii_corpus_gate_artifact_writes_counts_and_errors(tmp_path):
    package_dir = tmp_path / "package"
    gate = build_gii_corpus_gate_artifact(
        discovery_artifact(),
        payload_dir=PAYLOAD_DIR,
        package_dir=package_dir,
        retrieved_at="2026-05-15T00:00:00Z",
        parser_variant_matrix_path=PARSER_MATRIX,
    )
    output = tmp_path / "gate.json"

    write_gii_corpus_gate_artifact(gate, output)

    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["schema_version"] == "gii-corpus-gate.v1"
    assert written["counts"]["discovered_sources"] == 7
    assert written["counts"]["imported_sources"] == 4
    assert written["generated_package"]["path"] == str(package_dir)
    assert written["generated_package"]["sha256"]
    assert written["parser_variant_matrix"]["version"] == "fixture-v1"
    assert written["parser_variant_matrix"]["path"] == str(PARSER_MATRIX)
    assert written["parser_variant_matrix"]["sha256"]
    variants = {item["variant"] for item in written["parser_variant_matrix"]["covered_variants"]}
    assert {"paragraph", "article_child_paragraph", "structural_container"} <= variants
    assert written["validation_errors"] == []


def test_verify_gii_corpus_gate_script_runs_fixture_mode_without_network(tmp_path):
    discovery_path = tmp_path / "discovery.json"
    discovery_path.write_text(json.dumps(discovery_artifact(), ensure_ascii=False), encoding="utf-8")
    output = tmp_path / "gate.json"

    exit_code = verify_gii_corpus_gate_main([
        "--discovery",
        str(discovery_path),
        "--payload-dir",
        str(PAYLOAD_DIR),
        "--package-dir",
        str(tmp_path / "package"),
        "--output",
        str(output),
        "--retrieved-at",
        "2026-05-15T00:00:00Z",
        "--parser-variant-matrix",
        str(PARSER_MATRIX),
    ])

    assert exit_code == 0
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["schema_version"] == "gii-corpus-gate.v1"
