# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from legal_text_mcp_de.legal_texts.relationships import (
    DEFAULT_PRIVACY_SCOPE_SEED_PATH,
    DEFAULT_SCOPE_POLICY_PATH,
    load_privacy_scope_seed,
    load_scope_policy,
    seed_limitations_to_package_records,
    seed_relationship_source_to_manifest_record,
    seed_relationships_to_package_records,
    validate_privacy_scope_seed,
)
from legal_text_mcp_de.legal_texts.validation import validate_generated_package


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_policy_and_seed() -> tuple[dict, dict]:
    return load_scope_policy(DEFAULT_SCOPE_POLICY_PATH), load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)


def assert_has_error(errors: list[str], expected: str) -> None:
    assert any(expected in error for error in errors), errors


def test_seed_graph_contains_minimum_eu_celex_and_canonical_privacy_targets():
    policy, seed = valid_policy_and_seed()

    assert validate_privacy_scope_seed(seed, policy) == []
    celex_values = {record.get("celex") for record in seed["source_limitations"]}
    law_ids = {record["id"] for record in seed["official_targets"]["laws"]}

    assert {"32024R1689", "32023R2854"} <= celex_values
    assert {"bdsg_2018", "tdddg", "dsgvo_eu_2016_679"} <= law_ids
    assert "ttdsg" not in law_ids


def test_seed_graph_relationships_transform_to_phase2_package_records():
    policy, seed = valid_policy_and_seed()

    relationships = seed_relationships_to_package_records(seed)
    limitations = seed_limitations_to_package_records(seed)
    relationship_source = seed_relationship_source_to_manifest_record(seed)

    assert relationships
    assert limitations
    assert relationship_source["source_family"] == "third-party-scope"
    assert all(relationship["source_family"] == "third-party-scope" for relationship in relationships)
    assert all(relationship["provenance"]["source_url"].startswith("https://") for relationship in relationships)
    assert all(endpoint["kind"] != "external_source" for relationship in relationships for endpoint in (relationship["subject"], relationship["object"]))
    assert {limitation["limitation_id"] for limitation in limitations} >= {
        "lim-eu-ai-act-32024r1689",
        "lim-eu-data-act-32023r2854",
        "lim-state-be-dsg-source-pending",
    }
    assert validate_privacy_scope_seed(seed, policy) == []


def test_seed_relationship_transform_can_resolve_eu_limitations_to_imported_laws():
    _, seed = valid_policy_and_seed()

    relationships = seed_relationships_to_package_records(
        seed,
        resolved_limitations={
            "lim-eu-ai-act-32024r1689": {"kind": "law", "id": "ai_act_eu_2024_1689"},
        },
    )

    ai_relationship = next(relationship for relationship in relationships if relationship["relationship_id"] == "rel-scope-dsgvo-art5-ai-act")
    data_relationship = next(relationship for relationship in relationships if relationship["relationship_id"] == "rel-scope-dsgvo-art5-data-act")
    assert ai_relationship["object"] == {"kind": "law", "id": "ai_act_eu_2024_1689"}
    assert data_relationship["object"] == {"kind": "source_limitation", "id": "lim-eu-data-act-32023r2854"}


def test_seed_graph_rejects_duplicate_relationship_ids():
    policy, seed = valid_policy_and_seed()
    seed["relationships"].append(deepcopy(seed["relationships"][0]))

    errors = validate_privacy_scope_seed(seed, policy)

    assert_has_error(errors, "duplicate relationship_id")


def test_seed_graph_rejects_unsupported_relationship_type():
    policy, seed = valid_policy_and_seed()
    seed["relationships"][0]["relationship_type"] = "summarizes"

    errors = validate_privacy_scope_seed(seed, policy)

    assert_has_error(errors, "unsupported relationship_type summarizes")


def test_seed_graph_rejects_missing_relationship_provenance():
    policy, seed = valid_policy_and_seed()
    seed["relationships"][0].pop("provenance")

    errors = validate_privacy_scope_seed(seed, policy)

    assert_has_error(errors, "missing relationship fields ['provenance']")


def test_seed_graph_rejects_dangling_state_law_placeholder():
    policy, seed = valid_policy_and_seed()
    seed["relationships"][0]["object"] = {"kind": "law", "id": "LDSG"}

    errors = validate_privacy_scope_seed(seed, policy)

    assert_has_error(errors, "object target law:LDSG is not declared as an official target")


def test_seed_graph_rejects_missing_minimum_eu_neighbor_celex():
    policy, seed = valid_policy_and_seed()
    seed["source_limitations"] = [
        limitation for limitation in seed["source_limitations"] if limitation.get("celex") != "32024R1689"
    ]
    seed["official_targets"]["laws"] = [
        target for target in seed["official_targets"]["laws"] if target.get("celex") != "32024R1689"
    ]
    seed["official_targets"]["norms"] = [
        target for target in seed["official_targets"]["norms"] if target.get("celex") != "32024R1689"
    ]

    errors = validate_privacy_scope_seed(seed, policy)

    assert_has_error(errors, "minimum EU neighbor CELEX 32024R1689 is missing")


def test_transformed_seed_records_pass_generated_package_relationship_validation(tmp_path):
    policy, seed = valid_policy_and_seed()
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    relationships = seed_relationships_to_package_records(seed)
    limitations = seed_limitations_to_package_records(seed)
    relationship_source = seed_relationship_source_to_manifest_record(seed)
    norm_ids = ["dsgvo_eu_2016_679/art:5", "dsgvo_eu_2016_679/recital:1"]
    laws = [
        law_record("dsgvo_eu_2016_679", "DSGVO", "Datenschutz-Grundverordnung", "eur-lex-cellar", "CELEX:32016R0679", len(norm_ids)),
        law_record("bdsg_2018", "BDSG", "Bundesdatenschutzgesetz", "gesetze-im-internet", "bdsg_2018", 0),
        law_record("tdddg", "TDDDG", "Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz", "gesetze-im-internet", "ttdsg", 0),
    ]
    norms = [
        norm_record("dsgvo_eu_2016_679", "art:5", "art", "5", "Rechtmaessigkeit der Verarbeitung"),
        norm_record("dsgvo_eu_2016_679", "recital:1", "recital", "1", "Datenschutz als Grundrecht"),
    ]
    manifest = {
        "schema_version": "corpus-manifest.v1",
        "dataset_id": "scope-seed-fixture",
        "package_id": "scope-seed-fixture",
        "created_at": "2026-05-15T00:00:00Z",
        "validation_mode": "terminal",
        "generator": {"name": "scope-seed-fixture", "version": "test"},
        "parser_versions": {"scope_seed": "test"},
        "discovered_sources": [
            eurlex_imported_source(norm_ids),
            gii_imported_source("bdsg_2018", "bdsg_2018"),
            gii_imported_source("ttdsg", "tdddg"),
        ],
        "canonical_ids": [
            {"canonical_id": "dsgvo_eu_2016_679", "source_family": "eur-lex-cellar", "source_id": "eur-lex-cellar:32016R0679", "celex": "32016R0679"},
            {"canonical_id": "bdsg_2018", "source_family": "gii", "source_id": "gii:bdsg_2018"},
            {"canonical_id": "tdddg", "source_family": "gii", "source_id": "gii:ttdsg"},
        ],
        "relationship_sources": [relationship_source],
        "source_limitations": limitations,
    }
    readiness = {"stage": "normalized_dataset", "state": "ready", "details": {"law_count": len(laws), "norm_count": len(norms)}}
    files = {
        "laws.json": laws,
        "norms.json": norms,
        "manifest.json": manifest,
        "source-limitations.json": limitations,
        "relationships.json": relationships,
        "readiness.json": readiness,
        "search-index.json": {"documents": []},
    }
    for name, data in files.items():
        write_json(package_dir / name, data)
    package = {
        "schema_version": "generated-package.v1",
        "dataset_id": "scope-seed-fixture",
        "package_id": "scope-seed-fixture",
        "generated_at": "2026-05-15T00:00:00Z",
        "generator": {"name": "scope-seed-fixture", "version": "test"},
        "manifest_path": "manifest.json",
        "readiness_path": "readiness.json",
        "record_counts": {
            "laws": len(laws),
            "norms": len(norms),
            "relationships": len(relationships),
            "source_limitations": len(limitations),
            "discovered_sources": len(manifest["discovered_sources"]),
            "imported_sources": len(manifest["discovered_sources"]),
        },
        "content_hashes": {name: f"sha256:{file_hash(package_dir / name)}" for name in files},
        "validation_mode": "terminal",
        "source_families": ["eur-lex-cellar", "gii", "state-law", "third-party-scope"],
    }
    write_json(package_dir / "package.json", package)

    assert validate_privacy_scope_seed(seed, policy) == []
    assert validate_generated_package(package_dir, require_search_index=True) == []


def law_record(canonical_id: str, display_code: str, display_name: str, source_kind: str, source_identifier: str, norm_count: int) -> dict:
    source_url = "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679"
    source_metadata = {
        "celex": "32016R0679",
        "cellar_work": "3e485e15-11bd-11e6-ba9a-01aa75ed71a1",
        "expression": "0004.02",
        "language": "de",
        "document": "DOC_2",
    }
    if source_kind == "gesetze-im-internet":
        source_url = f"https://www.gesetze-im-internet.de/{source_identifier}/xml.zip"
        source_metadata = {"source_path": source_identifier}
    return {
        "canonical_id": canonical_id,
        "display_code": display_code,
        "display_name": display_name,
        "source": {
            "source_kind": source_kind,
            "source_identifier": source_identifier,
            "source_url": source_url,
            "retrieved_at": "2026-05-15T00:00:00Z",
            "stand_date": None,
            "stand_date_status": "official",
            "content_hash": "fixture-content",
            "source_metadata": source_metadata,
        },
        "aliases": [display_code, canonical_id],
        "norm_count": norm_count,
    }


def norm_record(law_id: str, norm_id: str, unit: str, value: str, text: str) -> dict:
    return {
        "canonical_id": f"{law_id}/{norm_id}",
        "law_id": law_id,
        "norm_id": norm_id,
        "unit": unit,
        "value": value,
        "title": norm_id,
        "text": text,
        "status": "active",
        "url": f"https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679#{norm_id.replace(':', '_')}",
        "source": law_record(law_id, "DSGVO", "Datenschutz-Grundverordnung", "eur-lex-cellar", "CELEX:32016R0679", 0)["source"],
        "subdivisions": [],
    }


def eurlex_imported_source(norm_ids: list[str]) -> dict:
    return {
        "source_family": "eur-lex-cellar",
        "source_id": "eur-lex-cellar:32016R0679",
        "celex": "32016R0679",
        "language": "de",
        "cellar_uri": "cellar:work",
        "work": "cellar:work",
        "expression": "0004.02",
        "document": "DOC_2",
        "version_policy": "fixture",
        "terminal_state": "imported",
        "canonical_id": "dsgvo_eu_2016_679",
        "source_url": "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679",
        "content_sha256": "fixture-content",
        "retrieved_at": "2026-05-15T00:00:00Z",
        "parser_version": "test",
        "generated_law_ids": ["dsgvo_eu_2016_679"],
        "generated_norm_ids": norm_ids,
    }


def gii_imported_source(source_path: str, canonical_id: str) -> dict:
    return {
        "source_family": "gii",
        "source_id": f"gii:{source_path}",
        "source_path": source_path,
        "index_url": f"https://www.gesetze-im-internet.de/{source_path}/",
        "xml_zip_url": f"https://www.gesetze-im-internet.de/{source_path}/xml.zip",
        "toc_url": "https://www.gesetze-im-internet.de/gii-toc.xml",
        "toc_sha256": "fixture-toc",
        "terminal_state": "imported",
        "canonical_id": canonical_id,
        "source_url": f"https://www.gesetze-im-internet.de/{source_path}/xml.zip",
        "content_sha256": "fixture-content",
        "retrieved_at": "2026-05-15T00:00:00Z",
        "parser_version": "test",
        "generated_law_ids": [canonical_id],
    }
