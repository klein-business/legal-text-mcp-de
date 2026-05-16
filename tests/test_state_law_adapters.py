# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import json
from pathlib import Path

from legal_text_mcp_de.legal_texts.dataset import NormalizedDataset
from legal_text_mcp_de.legal_texts import state_law as state_law_module
from legal_text_mcp_de.legal_texts.state_law import (
    STATE_LAW_ADAPTER_SCHEMA_VERSION,
    build_state_law_adapter_gate_artifact,
    eligible_state_law_records,
    parse_state_law_html,
    run_state_law_adapters,
    write_state_law_adapter_gate_artifact,
)
from legal_text_mcp_de.legal_texts.state_law_inventory import (
    DEFAULT_STATE_LAW_INVENTORY_PATH,
    DEFAULT_STATE_LAW_LIMITATIONS_PATH,
    load_state_law_inventory,
    load_state_law_limitations,
)
from legal_text_mcp_de.legal_texts.validation import validate_generated_package
from scripts.verify_state_law_adapters import main as verify_state_law_adapters_main


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "state_law"


def valid_inventory_and_limitations() -> tuple[dict, list[dict]]:
    return load_state_law_inventory(DEFAULT_STATE_LAW_INVENTORY_PATH), load_state_law_limitations(
        DEFAULT_STATE_LAW_LIMITATIONS_PATH
    )


def stable_html_body() -> bytes:
    return (FIXTURE_DIR / "stable_html_law.html").read_bytes()


def malformed_html_body() -> bytes:
    return (FIXTURE_DIR / "malformed_html_law.html").read_bytes()


def official_like_bb_body() -> bytes:
    return (FIXTURE_DIR / "official_like_bb.html").read_bytes()


def nw_meta_refresh_body() -> bytes:
    return (FIXTURE_DIR / "nw_meta_refresh.html").read_bytes()


def official_like_nw_body() -> bytes:
    return (FIXTURE_DIR / "official_like_nw.html").read_bytes()


def official_like_nw_action_chrome_body() -> bytes:
    return (FIXTURE_DIR / "official_like_nw_action_chrome.html").read_bytes()


def official_like_duplicate_help_body() -> bytes:
    return (FIXTURE_DIR / "official_like_duplicate_help.html").read_bytes()


def official_like_portal_chrome_body() -> bytes:
    return (FIXTURE_DIR / "official_like_portal_chrome.html").read_bytes()


def fake_fetch_all_importable(url: str) -> tuple[int, dict[str, str], bytes]:
    return 200, {"content-type": "text/html; charset=utf-8"}, stable_html_body()


def test_eligible_state_law_records_are_derived_from_current_inventory():
    inventory, _limitations = valid_inventory_and_limitations()

    eligible = eligible_state_law_records(inventory)

    assert len(eligible) == 13
    assert {record["adapter_class"] for record in eligible} == {"stable_html"}
    assert {record["state_code"] for record in eligible}.isdisjoint({"HB", "NI", "SL"})


def test_stable_html_fixture_parses_to_state_law_records_with_provenance():
    inventory, _limitations = valid_inventory_and_limitations()
    record = next(item for item in eligible_state_law_records(inventory) if item["state_code"] == "BW")

    parsed = parse_state_law_html(
        stable_html_body(),
        record,
        source_url=record["official_sources"][0]["url"],
        retrieved_at="2026-05-15T00:00:00Z",
    )

    assert parsed.law["canonical_id"] == "state:bw/landesdatenschutzgesetz"
    assert parsed.law["display_code"] == "BW LDSG"
    assert parsed.law["norm_count"] == 2
    assert [norm["norm_id"] for norm in parsed.norms] == ["par:1", "par:2"]
    assert parsed.norms[0]["canonical_id"] == "state:bw/landesdatenschutzgesetz/par:1"
    assert parsed.norms[0]["subdivisions"][0]["path"] == "abs:1"
    assert parsed.norms[0]["source"]["source_kind"] == "state-law"
    assert parsed.norms[0]["source"]["source_metadata"]["state_code"] == "bw"
    assert parsed.norms[0]["source"]["source_metadata"]["adapter_class"] == "stable_html"


def test_official_like_html_fallback_imports_norms_without_synthetic_markers():
    inventory, _limitations = valid_inventory_and_limitations()
    record = next(item for item in eligible_state_law_records(inventory) if item["state_code"] == "BB")

    parsed = parse_state_law_html(
        official_like_bb_body(),
        record,
        source_url=record["official_sources"][0]["url"],
        retrieved_at="2026-05-15T00:00:00Z",
    )

    assert [norm["norm_id"] for norm in parsed.norms] == ["par:1", "par:2"]
    assert "Dieses Gesetz schützt personenbezogene Daten" in parsed.norms[0]["text"]
    assert "§ 1 Zweck § 2 Anwendungsbereich" not in parsed.norms[0]["text"]
    assert parsed.norms[0]["subdivisions"][0]["path"] == "abs:1"


def test_official_html_fallback_prefers_later_real_norm_over_duplicate_portal_help():
    inventory, _limitations = valid_inventory_and_limitations()
    record = next(item for item in eligible_state_law_records(inventory) if item["state_code"] == "BB")

    parsed = parse_state_law_html(
        official_like_duplicate_help_body(),
        record,
        source_url=record["official_sources"][0]["url"],
        retrieved_at="2026-05-15T00:00:00Z",
    )

    norm = next(item for item in parsed.norms if item["norm_id"] == "par:35")
    assert norm["text"].startswith("(1) Verfahren, die vor dem Inkrafttreten")
    assert "Hilfe - Detailansicht" not in norm["text"]
    assert "Inhaltsübersicht" not in norm["text"]
    assert "Reiter" not in norm["text"]


def test_official_html_fallback_sanitizes_portal_chrome_and_uses_legal_title():
    inventory, _limitations = valid_inventory_and_limitations()
    record = next(item for item in eligible_state_law_records(inventory) if item["state_code"] == "BB")

    parsed = parse_state_law_html(
        official_like_portal_chrome_body(),
        record,
        source_url=record["official_sources"][0]["url"],
        retrieved_at="2026-05-15T00:00:00Z",
    )

    assert parsed.law["display_name"] == "Brandenburgisches Datenschutzgesetz"
    assert [norm["norm_id"] for norm in parsed.norms] == ["par:1", "par:2"]
    assert all("Einzelnorm" not in norm["text"] for norm in parsed.norms)
    assert all("nach oben" not in norm["text"] for norm in parsed.norms)
    assert "Dieses Gesetz schützt personenbezogene Daten" in parsed.norms[0]["text"]


def test_meta_refresh_is_followed_and_preserved_in_import_metadata(tmp_path):
    inventory, limitations = valid_inventory_and_limitations()
    record = next(item for item in inventory["states"] if item["state_code"] == "NW")
    original_url = record["official_sources"][0]["url"]
    resolved_url = "https://recht.nrw.de/lrgv/gesetz/01042026-datenschutzgesetz-nordrhein-westfalen"

    def fake_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
        if url == original_url:
            return 200, {"content-type": "text/html; charset=utf-8"}, nw_meta_refresh_body()
        if url == resolved_url:
            return 200, {"content-type": "text/html; charset=utf-8"}, official_like_nw_body()
        raise AssertionError(f"unexpected URL {url}")

    result = run_state_law_adapters(
        {"schema_version": inventory["schema_version"], "states": [record]},
        limitations,
        package_dir=tmp_path / "package",
        retrieved_at="2026-05-15T00:00:00Z",
        fetch=fake_fetch,
    )

    assert result.terminal_state_counts == {"imported": 1}
    norm = result.norms[0]
    metadata = norm["source"]["source_metadata"]
    assert norm["canonical_id"] == "state:nw/datenschutzgesetz/par:1"
    assert norm["source"]["source_url"] == resolved_url
    assert metadata["official_source_url"] == original_url
    assert metadata["original_source_url"] == original_url
    assert metadata["resolved_source_url"] == resolved_url
    assert result.source_outcomes["state:nw/datenschutzgesetz"]["resolved_source_url"] == resolved_url


def test_official_html_fallback_sanitizes_nrw_action_chrome_from_text_and_subdivisions():
    inventory, _limitations = valid_inventory_and_limitations()
    record = next(item for item in eligible_state_law_records(inventory) if item["state_code"] == "NW")
    forbidden = (
        "Mehr Paragraph",
        "ausdrucken",
        "Link kopieren",
        "Link kopiert",
        "Pragraph",
        "Zum Textanfang",
        "Textanfang",
    )

    parsed = parse_state_law_html(
        official_like_nw_action_chrome_body(),
        record,
        source_url=record["official_sources"][0]["url"],
        retrieved_at="2026-05-15T00:00:00Z",
    )

    norm = parsed.norms[0]
    assert norm["text"].startswith("(1) Zweck dieses Gesetzes")
    assert norm["text"].endswith("Datenschutz-Grundverordnung.")
    assert all(term not in norm["text"] for term in forbidden)
    assert norm["subdivisions"]
    assert all(term not in subdivision["text"] for subdivision in norm["subdivisions"] for term in forbidden)


def test_adapter_gate_validation_rejects_imported_portal_chrome(monkeypatch, tmp_path):
    inventory, limitations = valid_inventory_and_limitations()
    record = next(item for item in inventory["states"] if item["state_code"] == "NW")
    original_parse = state_law_module.parse_state_law_html

    def contaminated_parse(*args, **kwargs):
        parsed = original_parse(*args, **kwargs)
        parsed.norms[0]["text"] = f"{parsed.norms[0]['text']} Zum Textanfang"
        parsed.norms[0]["subdivisions"][0]["text"] = f"{parsed.norms[0]['subdivisions'][0]['text']} Link kopieren"
        return parsed

    monkeypatch.setattr(state_law_module, "parse_state_law_html", contaminated_parse)

    result = run_state_law_adapters(
        {"schema_version": inventory["schema_version"], "states": [record]},
        limitations,
        package_dir=tmp_path / "package",
        retrieved_at="2026-05-15T00:00:00Z",
        fetch=lambda url: (200, {"content-type": "text/html; charset=utf-8"}, official_like_nw_body()),
    )

    assert any("contains portal chrome phrase 'Zum Textanfang'" in error for error in result.validation_errors)
    assert any("contains portal chrome phrase 'Link kopieren'" in error for error in result.validation_errors)


def test_adapter_gate_imports_fixture_html_and_writes_valid_generated_package(tmp_path):
    inventory, limitations = valid_inventory_and_limitations()
    package_dir = tmp_path / "package"

    result = run_state_law_adapters(
        inventory,
        limitations,
        package_dir=package_dir,
        retrieved_at="2026-05-15T00:00:00Z",
        fetch=fake_fetch_all_importable,
    )

    assert result.terminal_state_counts == {"imported": 13, "source_unavailable": 3}
    assert len(result.laws) == 13
    assert len(result.source_limitations) == 3
    assert result.validation_errors == []
    assert validate_generated_package(package_dir, require_search_index=True) == []

    dataset = NormalizedDataset.load(package_dir, require_search_index=True)
    imported_law = dataset.laws_by_id["state:bw/landesdatenschutzgesetz"]
    assert imported_law["display_code"] == "BW LDSG"
    assert dataset.get_norm_by_id("state:bw/landesdatenschutzgesetz", "par:1")["text"]


def test_adapter_gate_does_not_create_fake_laws_for_parse_failures(tmp_path):
    inventory, limitations = valid_inventory_and_limitations()

    def fake_fetch_parse_failure(url: str) -> tuple[int, dict[str, str], bytes]:
        return 200, {"content-type": "text/html; charset=utf-8"}, malformed_html_body()

    result = run_state_law_adapters(
        inventory,
        limitations,
        package_dir=tmp_path / "package",
        retrieved_at="2026-05-15T00:00:00Z",
        fetch=fake_fetch_parse_failure,
    )

    assert result.terminal_state_counts == {"parse_failed": 13, "source_unavailable": 3}
    assert result.laws == []
    assert len(result.source_limitations) == 16
    first_limitation = next(
        item for item in result.source_limitations if item["source_id"] == "state-law:bw/landesdatenschutzgesetz"
    )
    assert first_limitation["terminal_state"] == "parse_failed"
    assert first_limitation["details"]["implementation_evidence"] is True
    assert validate_generated_package(tmp_path / "package", require_search_index=True) == []


def test_adapter_gate_emits_source_unavailable_for_fetch_exception(tmp_path):
    inventory, limitations = valid_inventory_and_limitations()

    def fake_fetch_exception(url: str) -> tuple[int, dict[str, str], bytes]:
        raise TimeoutError("fixture timeout")

    result = run_state_law_adapters(
        inventory,
        limitations,
        package_dir=tmp_path / "package",
        retrieved_at="2026-05-15T00:00:00Z",
        fetch=fake_fetch_exception,
    )

    limitation = next(
        item for item in result.source_limitations if item["source_id"] == "state-law:bw/landesdatenschutzgesetz"
    )
    assert limitation["terminal_state"] == "source_unavailable"
    assert limitation["error_code"] == "fetch_exception"
    assert "fixture timeout" in limitation["details"]["diagnostic"]


def test_state_law_ids_do_not_collide_with_non_state_sources(tmp_path):
    inventory, limitations = valid_inventory_and_limitations()
    result = run_state_law_adapters(
        inventory,
        limitations,
        package_dir=tmp_path / "package",
        retrieved_at="2026-05-15T00:00:00Z",
        fetch=fake_fetch_all_importable,
    )

    assert all(law["canonical_id"].startswith("state:") for law in result.laws)
    assert all(norm["law_id"].startswith("state:") for norm in result.norms)
    assert not {law["canonical_id"] for law in result.laws} & {"bdsg_2018", "tdddg", "dsgvo_eu_2016_679"}


def test_state_law_adapter_gate_artifact_writes_counts_and_package_reference(tmp_path):
    inventory, limitations = valid_inventory_and_limitations()
    package_dir = tmp_path / "package"
    gate = build_state_law_adapter_gate_artifact(
        inventory,
        limitations,
        package_dir=package_dir,
        retrieved_at="2026-05-15T00:00:00Z",
        fetch=fake_fetch_all_importable,
    )
    output = tmp_path / "adapter-gate.json"

    write_state_law_adapter_gate_artifact(gate, output)

    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["schema_version"] == STATE_LAW_ADAPTER_SCHEMA_VERSION
    assert written["counts"]["eligible_sources"] == 13
    assert written["counts"]["imported"] == 13
    assert written["counts"]["source_limitations"] == 3
    assert written["generated_package"]["path"] == str(package_dir)
    assert written["generated_package"]["sha256"]
    assert written["validation_errors"] == []


def test_verify_state_law_adapters_script_runs_fixture_mode_without_network(tmp_path):
    output = tmp_path / "adapter-gate.json"

    exit_code = verify_state_law_adapters_main(
        [
            "--inventory",
            str(DEFAULT_STATE_LAW_INVENTORY_PATH),
            "--limitations",
            str(DEFAULT_STATE_LAW_LIMITATIONS_PATH),
            "--package-dir",
            str(tmp_path / "package"),
            "--output",
            str(output),
            "--fixture-mode",
        ]
    )

    assert exit_code == 0
    artifact = json.loads(output.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == STATE_LAW_ADAPTER_SCHEMA_VERSION
    assert artifact["validation_errors"] == []
