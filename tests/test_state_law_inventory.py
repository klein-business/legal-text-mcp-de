# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import json
from copy import deepcopy

from legal_text_mcp_de.legal_texts.manifest import validate_corpus_manifest
from legal_text_mcp_de.legal_texts.state_law_inventory import (
    DEFAULT_STATE_LAW_INVENTORY_PATH,
    DEFAULT_STATE_LAW_LIMITATIONS_PATH,
    FIXED_STATE_CODES,
    derive_state_law_id,
    inventory_records_to_manifest_sources,
    load_state_law_inventory,
    load_state_law_limitations,
    validate_state_law_inventory,
)
from scripts.verify_state_law_inventory import build_artifact, main as verify_state_law_inventory_main


def assert_has_error(errors: list[str], expected: str) -> None:
    assert any(expected in error for error in errors), errors


def valid_inventory_and_limitations() -> tuple[dict, list[dict]]:
    return load_state_law_inventory(DEFAULT_STATE_LAW_INVENTORY_PATH), load_state_law_limitations(
        DEFAULT_STATE_LAW_LIMITATIONS_PATH
    )


def test_state_law_inventory_covers_exact_fixed_state_set():
    inventory, limitations = valid_inventory_and_limitations()

    assert validate_state_law_inventory(inventory, limitations) == []
    assert {record["state_code"] for record in inventory["states"]} == set(FIXED_STATE_CODES)
    assert len(inventory["states"]) == 16


def test_state_law_inventory_matches_reachability_classification_rework():
    inventory, limitations = valid_inventory_and_limitations()
    by_state = {record["state_code"]: record for record in inventory["states"]}

    assert by_state["NI"]["adapter_class"] == "limitation_only"
    assert by_state["NI"]["source_limitation_id"] == "lim-state-ni-dsg-source-limitation"
    assert {limitation["limitation_id"] for limitation in limitations} >= {"lim-state-ni-dsg-source-limitation"}
    for state_code in ("MV", "ST", "NW"):
        assert by_state[state_code]["adapter_class"] == "stable_html"
        assert by_state[state_code]["source_format"] == "html"
        assert by_state[state_code]["reachability"]["content_type"] == "text/html"


def test_derive_state_law_id_uses_lowercase_state_code_and_stable_slug():
    assert derive_state_law_id("BE", "berliner-datenschutzgesetz") == "state:be/berliner-datenschutzgesetz"


def test_state_law_inventory_rejects_missing_state():
    inventory, limitations = valid_inventory_and_limitations()
    inventory["states"] = [record for record in inventory["states"] if record["state_code"] != "BE"]

    errors = validate_state_law_inventory(inventory, limitations)

    assert_has_error(errors, "missing state inventory records ['BE']")


def test_state_law_inventory_rejects_duplicate_state():
    inventory, limitations = valid_inventory_and_limitations()
    inventory["states"].append(deepcopy(inventory["states"][0]))

    errors = validate_state_law_inventory(inventory, limitations)

    assert_has_error(errors, "duplicate state inventory record BW")


def test_state_law_inventory_rejects_unknown_state_code():
    inventory, limitations = valid_inventory_and_limitations()
    inventory["states"][0]["state_code"] = "XX"

    errors = validate_state_law_inventory(inventory, limitations)

    assert_has_error(errors, "unknown state_code XX")


def test_state_law_inventory_rejects_malformed_law_id():
    inventory, limitations = valid_inventory_and_limitations()
    inventory["states"][0]["law_id"] = "bw/bad"

    errors = validate_state_law_inventory(inventory, limitations)

    assert_has_error(errors, "law_id bw/bad does not match expected state:bw/")


def test_state_law_inventory_rejects_bad_adapter_class():
    inventory, limitations = valid_inventory_and_limitations()
    inventory["states"][0]["adapter_class"] = "crawler"

    errors = validate_state_law_inventory(inventory, limitations)

    assert_has_error(errors, "unsupported adapter_class crawler")


def test_state_law_inventory_rejects_missing_official_sources():
    inventory, limitations = valid_inventory_and_limitations()
    inventory["states"][0]["official_sources"] = []

    errors = validate_state_law_inventory(inventory, limitations)

    assert_has_error(errors, "official_sources must contain at least one source")


def test_limitation_only_requires_matching_limitation_record():
    inventory, limitations = valid_inventory_and_limitations()
    limitation_state = next(record for record in inventory["states"] if record["adapter_class"] == "limitation_only")
    limitations = [
        limitation
        for limitation in limitations
        if limitation["limitation_id"] != limitation_state["source_limitation_id"]
    ]

    errors = validate_state_law_inventory(inventory, limitations)

    assert_has_error(
        errors,
        f"{limitation_state['state_code']}: source_limitation_id {limitation_state['source_limitation_id']} not found",
    )


def test_state_law_limitations_are_phase1_manifest_compatible():
    inventory, limitations = valid_inventory_and_limitations()
    sources = inventory_records_to_manifest_sources(inventory, limitations)
    manifest = {
        "schema_version": "corpus-manifest.v1",
        "dataset_id": "state-law-inventory-fixture",
        "package_id": "state-law-inventory-fixture",
        "created_at": "2026-05-15T00:00:00Z",
        "validation_mode": "terminal",
        "generator": {"name": "state-law-inventory-fixture", "version": "test"},
        "parser_versions": {"state_law_inventory": "test"},
        "discovered_sources": sources,
        "canonical_ids": [],
        "relationship_sources": [],
        "source_limitations": limitations,
    }

    assert validate_state_law_inventory(inventory, limitations) == []
    assert validate_corpus_manifest(manifest, require_terminal_states=True) == []


def test_reachability_artifact_records_fake_fetch_results_without_network(tmp_path):
    inventory, limitations = valid_inventory_and_limitations()

    def fake_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
        if "unavailable" in url:
            return 503, {"content-type": "text/plain"}, b"unavailable"
        return 200, {"content-type": "text/html; charset=utf-8"}, b"<html>official state law</html>"

    artifact = build_artifact(inventory, limitations, fetch=fake_fetch, checked_at="2026-05-15T00:00:00Z")

    assert artifact["schema_version"] == "state-law-inventory-reachability.v1"
    assert artifact["state_count"] == 16
    assert len(artifact["results"]) == 16
    assert artifact["validation_errors"] == []
    fetched = [result for result in artifact["results"] if result["adapter_class"] != "limitation_only"]
    assert fetched
    assert all("content_sha256" in result["sources"][0] for result in fetched if result["sources"][0]["status"] == 200)


def test_reachability_artifact_records_fetch_exception_without_network():
    inventory, limitations = valid_inventory_and_limitations()

    def fake_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
        raise TimeoutError("fixture timeout")

    artifact = build_artifact(inventory, limitations, fetch=fake_fetch, checked_at="2026-05-15T00:00:00Z")

    non_limitation = next(result for result in artifact["results"] if result["adapter_class"] != "limitation_only")
    assert non_limitation["sources"][0]["error_code"] == "fetch_exception"
    assert "fixture timeout" in non_limitation["sources"][0]["error"]
    assert_has_error(artifact["validation_errors"], "non-limitation source")


def test_reachability_artifact_rejects_non_limitation_non_200_source():
    inventory, limitations = valid_inventory_and_limitations()

    def fake_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
        return 404, {"content-type": "text/html"}, b"missing"

    artifact = build_artifact(inventory, limitations, fetch=fake_fetch, checked_at="2026-05-15T00:00:00Z")

    assert_has_error(artifact["validation_errors"], "non-limitation source")


def test_reachability_artifact_rejects_pdf_source_served_as_html():
    inventory, limitations = valid_inventory_and_limitations()
    inventory["states"][0]["source_format"] = "pdf"
    inventory["states"][0]["adapter_class"] = "pdf"
    inventory["states"][0]["official_sources"][0]["format"] = "pdf"

    def fake_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
        return 200, {"content-type": "text/html"}, b"<html>not pdf</html>"

    artifact = build_artifact(inventory, limitations, fetch=fake_fetch, checked_at="2026-05-15T00:00:00Z")

    assert_has_error(artifact["validation_errors"], "source_format pdf does not match content_type text/html")


def test_reachability_artifact_rejects_xml_source_served_as_html():
    inventory, limitations = valid_inventory_and_limitations()
    inventory["states"][0]["source_format"] = "xml"
    inventory["states"][0]["adapter_class"] = "machine_readable"
    inventory["states"][0]["official_sources"][0]["format"] = "xml"

    def fake_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
        return 200, {"content-type": "text/html"}, b"<html>not xml</html>"

    artifact = build_artifact(inventory, limitations, fetch=fake_fetch, checked_at="2026-05-15T00:00:00Z")

    assert_has_error(artifact["validation_errors"], "source_format xml does not match content_type text/html")


def test_verify_state_law_inventory_writes_artifact_with_fake_fetch(tmp_path):
    output = tmp_path / "inventory-reachability.json"

    exit_code = verify_state_law_inventory_main(
        [
            "--inventory",
            str(DEFAULT_STATE_LAW_INVENTORY_PATH),
            "--limitations",
            str(DEFAULT_STATE_LAW_LIMITATIONS_PATH),
            "--write-artifact",
            str(output),
            "--fixture-mode",
        ]
    )

    assert exit_code == 0
    artifact = json.loads(output.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "state-law-inventory-reachability.v1"
    assert artifact["state_count"] == 16
    assert artifact["validation_errors"] == []
