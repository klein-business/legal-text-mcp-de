# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from copy import deepcopy
from pathlib import Path

from legal_text_mcp_de.legal_texts.eu_neighbors import (
    DEFAULT_EU_NEIGHBOR_SOURCES_PATH,
    build_eu_neighbor_law,
    eu_neighbor_source_limitation,
    load_eu_neighbor_source_records,
    parse_eu_neighbor_fixture,
    validate_eu_neighbor_source_records,
)
from legal_text_mcp_de.legal_texts.eurlex_xml import parse_dsgvo_xml, parse_eurlex_act_xml
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
from scripts.verify_eu_neighbor_sources import build_artifact, main as verify_eu_neighbor_sources_main


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "eurlex_neighbors"


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_has_error(errors: list[str], expected: str) -> None:
    assert any(expected in error for error in errors), errors


def test_eu_neighbor_source_records_are_seed_bound_to_ai_act_and_data_act():
    seed = load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)
    records = load_eu_neighbor_source_records(DEFAULT_EU_NEIGHBOR_SOURCES_PATH)

    assert validate_eu_neighbor_source_records(records, seed) == []
    assert {record["celex"] for record in records} == {"32024R1689", "32023R2854"}
    assert {record["canonical_id"] for record in records} == {"ai_act_eu_2024_1689", "data_act_eu_2023_2854"}
    assert all(record["language"] == "de" for record in records)
    assert records_by_celex()["32024R1689"]["source_url"] == (
        "https://publications.europa.eu/resource/cellar/dc8116a1-3fe6-11ef-865a-01aa75ed71a1.0004.02/DOC_1"
    )
    assert records_by_celex()["32023R2854"]["source_metadata"] == {
        "celex": "32023R2854",
        "cellar_work": "ef51c6ab-a06c-11ee-b164-01aa75ed71a1",
        "expression": "0004.02",
        "language": "de",
        "document": "DOC_1",
    }


def test_eu_neighbor_source_records_reject_unseeded_celex():
    seed = load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)
    records = load_eu_neighbor_source_records(DEFAULT_EU_NEIGHBOR_SOURCES_PATH)
    extra = deepcopy(records[0])
    extra["canonical_id"] = "digital_services_act_eu_2022_2065"
    extra["celex"] = "32022R2065"
    extra["source_identifier"] = "CELEX:32022R2065"
    records.append(extra)

    errors = validate_eu_neighbor_source_records(records, seed)

    assert_has_error(errors, "CELEX 32022R2065 is not present in privacy scope seed")


def test_eu_neighbor_source_records_reject_missing_required_seed():
    seed = load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)
    seed["source_limitations"] = [
        limitation for limitation in seed["source_limitations"] if limitation.get("celex") != "32023R2854"
    ]
    seed["official_targets"]["laws"] = [
        target for target in seed["official_targets"]["laws"] if target.get("celex") != "32023R2854"
    ]
    seed["official_targets"]["norms"] = [
        target for target in seed["official_targets"]["norms"] if target.get("celex") != "32023R2854"
    ]
    records = load_eu_neighbor_source_records(DEFAULT_EU_NEIGHBOR_SOURCES_PATH)

    errors = validate_eu_neighbor_source_records(records, seed)

    assert_has_error(errors, "required EU neighbor CELEX 32023R2854 is missing from privacy scope seed")


def test_eu_neighbor_source_records_reject_placeholder_cellar_metadata():
    seed = load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)
    records = load_eu_neighbor_source_records(DEFAULT_EU_NEIGHBOR_SOURCES_PATH)
    records[0]["source_metadata"]["cellar_work"] = "fixture-work-32024R1689"
    records[0]["source_metadata"]["expression"] = "fixture-de"

    errors = validate_eu_neighbor_source_records(records, seed)

    assert_has_error(errors, "placeholder source_metadata.cellar_work is not allowed")
    assert_has_error(errors, "placeholder source_metadata.expression is not allowed")


def test_eu_neighbor_source_records_reject_html_source_url():
    seed = load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)
    records = load_eu_neighbor_source_records(DEFAULT_EU_NEIGHBOR_SOURCES_PATH)
    records[0]["source_url"] = "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32024R1689"

    errors = validate_eu_neighbor_source_records(records, seed)

    assert_has_error(errors, "source_url must be official Publications/Cellar DOC_1 URL")


def test_eu_neighbor_source_records_reject_seed_metadata_mismatch():
    seed = load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)
    records = load_eu_neighbor_source_records(DEFAULT_EU_NEIGHBOR_SOURCES_PATH)
    seed["source_limitations"][0]["work"] = "wrong-work"

    errors = validate_eu_neighbor_source_records(records, seed)

    assert_has_error(errors, "seed limitation work wrong-work does not match source metadata")


def test_generic_eurlex_parser_extracts_ai_act_articles_and_recitals():
    records = records_by_celex()
    norms = parse_eu_neighbor_fixture(FIXTURE_DIR / "ai_act_de_sample.xml", records["32024R1689"])

    assert [norm["norm_id"] for norm in norms] == ["art:4", "recital:1"]
    article = norms[0]
    recital = norms[1]
    assert article["canonical_id"] == "ai_act_eu_2024_1689/art:4"
    assert article["unit"] == "art"
    assert "KI-Kompetenz" in article["text"]
    assert recital["canonical_id"] == "ai_act_eu_2024_1689/recital:1"
    assert recital["unit"] == "recital"
    assert recital["source"]["source_metadata"]["celex"] == "32024R1689"


def test_generic_eurlex_parser_extracts_data_act_articles():
    records = records_by_celex()
    norms = parse_eu_neighbor_fixture(FIXTURE_DIR / "data_act_de_sample.xml", records["32023R2854"])

    assert [norm["norm_id"] for norm in norms] == ["art:1", "recital:1"]
    assert norms[0]["canonical_id"] == "data_act_eu_2023_2854/art:1"
    assert norms[0]["source"]["source_metadata"]["celex"] == "32023R2854"


def test_generic_parser_rejects_missing_german_official_act_xml():
    records = records_by_celex()

    try:
        parse_eu_neighbor_fixture(FIXTURE_DIR / "missing_german_text.xml", records["32024R1689"])
        assert False
    except ValueError as exc:
        assert "German article-bearing" in str(exc)


def test_dsgvo_parser_wrapper_remains_compatible(tmp_path):
    xml_path = tmp_path / "dsgvo.xml"
    xml_path.write_text(
        '<ROOT><LG.DOC>DE</LG.DOC><ACT><ARTICLE IDENTIFIER="005"><TI.ART>Artikel 5</TI.ART><P>Text.</P></ARTICLE></ACT></ROOT>',
        encoding="utf-8",
    )
    source = {"source_url": "https://publications.europa.eu/resource/cellar/fixture/DOC_2", "source_kind": "eur-lex-cellar"}

    direct = parse_eurlex_act_xml(xml_path, {"canonical_id": "dsgvo_eu_2016_679"}, source)
    wrapped = parse_dsgvo_xml(xml_path, {"canonical_id": "dsgvo_eu_2016_679"}, source)

    assert wrapped == direct
    assert wrapped[0]["norm_id"] == "art:5"


def test_eu_neighbor_source_limitation_is_first_class_package_outcome():
    records = records_by_celex()

    limitation = eu_neighbor_source_limitation(
        records["32023R2854"],
        terminal_state="unsupported_format",
        reason="fixture unsupported",
        details={"content_type": "text/html"},
        retrieved_at="2026-05-15T00:00:00Z",
    )

    assert limitation["limitation_id"] == "lim-eu-data-act-32023r2854"
    assert limitation["source_family"] == "eur-lex-cellar"
    assert limitation["source_id"] == "eur-lex-cellar:32023R2854"
    assert limitation["terminal_state"] == "unsupported_format"
    assert limitation["details"] == {"content_type": "text/html"}


def test_eu_neighbor_imported_or_limited_records_resolve_relationship_targets_in_package(tmp_path):
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    seed = load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)
    policy = load_scope_policy(DEFAULT_SCOPE_POLICY_PATH)
    records = records_by_celex()
    ai_norms = parse_eu_neighbor_fixture(FIXTURE_DIR / "ai_act_de_sample.xml", records["32024R1689"])
    data_limitation = eu_neighbor_source_limitation(
        records["32023R2854"],
        terminal_state="source_unavailable",
        reason="fixture source unavailable",
        details={"error_code": "fixture-missing"},
        retrieved_at="2026-05-15T00:00:00Z",
    )
    relationships = seed_relationships_to_package_records(
        seed,
        resolved_limitations={
            "lim-eu-ai-act-32024r1689": {"kind": "law", "id": "ai_act_eu_2024_1689"},
            "lim-eu-data-act-32023r2854": {"kind": "source_limitation", "id": "lim-eu-data-act-32023r2854"},
        },
    )
    limitations = [
        limitation
        for limitation in seed_limitations_to_package_records(seed)
        if limitation["limitation_id"] == "lim-state-be-dsg-source-pending"
    ] + [data_limitation]
    relationship_source = seed_relationship_source_to_manifest_record(seed)
    dsgvo_norm_ids = ["dsgvo_eu_2016_679/art:5", "dsgvo_eu_2016_679/recital:1"]
    laws = [
        law_record("dsgvo_eu_2016_679", "DSGVO", "Datenschutz-Grundverordnung", "eur-lex-cellar", "32016R0679", len(dsgvo_norm_ids)),
        law_record("bdsg_2018", "BDSG", "Bundesdatenschutzgesetz", "gesetze-im-internet", "bdsg_2018", 0),
        law_record("tdddg", "TDDDG", "Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz", "gesetze-im-internet", "ttdsg", 0),
        build_eu_neighbor_law(records["32024R1689"], norm_count=len(ai_norms)),
    ]
    norms = [
        norm_record("dsgvo_eu_2016_679", "art:5", "art", "5", "Rechtmaessigkeit der Verarbeitung"),
        norm_record("dsgvo_eu_2016_679", "recital:1", "recital", "1", "Datenschutz als Grundrecht"),
        *ai_norms,
    ]
    manifest = {
        "schema_version": "corpus-manifest.v1",
        "dataset_id": "eu-neighbor-fixture",
        "package_id": "eu-neighbor-fixture",
        "created_at": "2026-05-15T00:00:00Z",
        "validation_mode": "terminal",
        "generator": {"name": "eu-neighbor-fixture", "version": "test"},
        "parser_versions": {"eurlex": "test", "scope_seed": "test"},
        "discovered_sources": [
            eurlex_imported_source("32016R0679", "dsgvo_eu_2016_679", dsgvo_norm_ids),
            gii_imported_source("bdsg_2018", "bdsg_2018"),
            gii_imported_source("ttdsg", "tdddg"),
            eu_neighbor_imported_source(records["32024R1689"], [norm["canonical_id"] for norm in ai_norms]),
        ],
        "canonical_ids": [
            {"canonical_id": "dsgvo_eu_2016_679", "source_family": "eur-lex-cellar", "source_id": "eur-lex-cellar:32016R0679", "celex": "32016R0679"},
            {"canonical_id": "bdsg_2018", "source_family": "gii", "source_id": "gii:bdsg_2018"},
            {"canonical_id": "tdddg", "source_family": "gii", "source_id": "gii:ttdsg"},
            {"canonical_id": "ai_act_eu_2024_1689", "source_family": "eur-lex-cellar", "source_id": "eur-lex-cellar:32024R1689", "celex": "32024R1689"},
        ],
        "relationship_sources": [relationship_source],
        "source_limitations": limitations,
    }
    files = {
        "laws.json": laws,
        "norms.json": norms,
        "manifest.json": manifest,
        "source-limitations.json": limitations,
        "relationships.json": relationships,
        "readiness.json": {"stage": "normalized_dataset", "state": "ready", "details": {"law_count": len(laws), "norm_count": len(norms)}},
        "search-index.json": {"documents": []},
    }
    for name, data in files.items():
        write_json(package_dir / name, data)
    write_json(
        package_dir / "package.json",
        {
            "schema_version": "generated-package.v1",
            "dataset_id": "eu-neighbor-fixture",
            "package_id": "eu-neighbor-fixture",
            "generated_at": "2026-05-15T00:00:00Z",
            "generator": {"name": "eu-neighbor-fixture", "version": "test"},
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
        },
    )

    assert validate_privacy_scope_seed(seed, policy) == []
    assert validate_generated_package(package_dir, require_search_index=True) == []


def test_verify_eu_neighbor_sources_writes_fixture_backed_artifact(tmp_path):
    output = tmp_path / "eu-neighbors.json"

    exit_code = verify_eu_neighbor_sources_main([
        "--seed",
        str(DEFAULT_PRIVACY_SCOPE_SEED_PATH),
        "--sources",
        str(DEFAULT_EU_NEIGHBOR_SOURCES_PATH),
        "--fixture-dir",
        str(FIXTURE_DIR),
        "--output",
        str(output),
    ])

    assert exit_code == 0
    artifact = json.loads(output.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "eu-neighbor-sources.v1"
    assert artifact["counts"]["seeded_sources"] == 2
    assert artifact["counts"]["imported"] == 2
    assert artifact["validation_errors"] == []


def test_verify_eu_neighbor_sources_live_mode_parses_official_fmx4_zip_without_network():
    seed = load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)
    records = load_eu_neighbor_source_records(DEFAULT_EU_NEIGHBOR_SOURCES_PATH)
    xml = (FIXTURE_DIR / "ai_act_de_sample.xml").read_bytes()
    zip_bytes = zip_with_member("nested/act.xml", xml)

    def fake_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
        assert url.startswith("https://publications.europa.eu/resource/cellar/")
        return 200, {"content-type": "application/zip"}, zip_bytes

    artifact = build_artifact(records, seed, fixture_dir=None, fetch=fake_fetch)

    assert artifact["counts"] == {"seeded_sources": 2, "imported": 2, "limited": 0}
    assert artifact["source_results"][0]["terminal_state"] == "imported"
    assert artifact["source_results"][0]["content_sha256"] == hashlib.sha256(zip_bytes).hexdigest()
    assert artifact["validation_errors"] == []


def test_verify_eu_neighbor_sources_live_mode_limits_non_200_without_network():
    seed = load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)
    records = load_eu_neighbor_source_records(DEFAULT_EU_NEIGHBOR_SOURCES_PATH)

    def fake_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
        return 503, {"content-type": "text/plain"}, b"unavailable"

    artifact = build_artifact(records, seed, fixture_dir=None, fetch=fake_fetch)

    assert artifact["counts"] == {"seeded_sources": 2, "imported": 0, "limited": 2}
    assert artifact["source_results"][0]["terminal_state"] == "source_unavailable"
    assert artifact["source_results"][0]["limitation"]["limitation_id"] == "lim-eu-ai-act-32024r1689"
    assert artifact["validation_errors"] == []


def test_verify_eu_neighbor_sources_live_mode_limits_zip_without_german_act_xml():
    seed = load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)
    records = load_eu_neighbor_source_records(DEFAULT_EU_NEIGHBOR_SOURCES_PATH)
    zip_bytes = zip_with_member("readme.txt", b"not xml")

    def fake_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
        return 200, {"content-type": "application/zip"}, zip_bytes

    artifact = build_artifact(records, seed, fixture_dir=None, fetch=fake_fetch)

    assert artifact["counts"] == {"seeded_sources": 2, "imported": 0, "limited": 2}
    assert artifact["source_results"][0]["terminal_state"] == "parse_failed"
    assert "No parseable German act XML" in artifact["source_results"][0]["limitation"]["diagnostic_text"]
    assert artifact["validation_errors"] == []


def records_by_celex() -> dict[str, dict]:
    return {record["celex"]: record for record in load_eu_neighbor_source_records(DEFAULT_EU_NEIGHBOR_SOURCES_PATH)}


def zip_with_member(name: str, content: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, content)
    return buffer.getvalue()


def law_record(canonical_id: str, display_code: str, display_name: str, source_kind: str, source_identifier: str, norm_count: int) -> dict:
    if source_kind == "gesetze-im-internet":
        source_url = f"https://www.gesetze-im-internet.de/{source_identifier}/xml.zip"
        source_metadata = {"source_path": source_identifier}
        source_identifier_value = source_identifier
    else:
        source_url = f"https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:{source_identifier}"
        source_metadata = {
            "celex": source_identifier,
            "cellar_work": f"fixture-work-{source_identifier}",
            "expression": "fixture-de",
            "language": "de",
            "document": "DOC_2",
        }
        source_identifier_value = f"CELEX:{source_identifier}"
    return {
        "canonical_id": canonical_id,
        "display_code": display_code,
        "display_name": display_name,
        "source": {
            "source_kind": source_kind,
            "source_identifier": source_identifier_value,
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
        "source": law_record(law_id, "DSGVO", "Datenschutz-Grundverordnung", "eur-lex-cellar", "32016R0679", 0)["source"],
        "subdivisions": [],
    }


def eurlex_imported_source(celex: str, canonical_id: str, norm_ids: list[str]) -> dict:
    return {
        "source_family": "eur-lex-cellar",
        "source_id": f"eur-lex-cellar:{celex}",
        "celex": celex,
        "language": "de",
        "official_eurlex_url": f"https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:{celex}",
        "work": f"fixture-work-{celex}",
        "expression": "fixture-de",
        "document": "DOC_2",
        "version_policy": "fixture",
        "terminal_state": "imported",
        "canonical_id": canonical_id,
        "source_url": f"https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:{celex}",
        "content_sha256": "fixture-content",
        "retrieved_at": "2026-05-15T00:00:00Z",
        "parser_version": "test",
        "generated_law_ids": [canonical_id],
        "generated_norm_ids": norm_ids,
    }


def eu_neighbor_imported_source(record: dict, norm_ids: list[str]) -> dict:
    source = eurlex_imported_source(record["celex"], record["canonical_id"], norm_ids)
    source["work"] = record["source_metadata"]["cellar_work"]
    source["expression"] = record["source_metadata"]["expression"]
    source["document"] = record["source_metadata"]["document"]
    source["version_policy"] = record["version_policy"]
    return source


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
