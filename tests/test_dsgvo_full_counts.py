# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from legal_text_mcp_de.legal_texts.dataset import NormalizedDataset
from legal_text_mcp_de.legal_texts.eurlex_xml import parse_dsgvo_xml
from legal_text_mcp_de.legal_texts.resolver import get_norm, resolve_citation
from legal_text_mcp_de.legal_texts.search import SearchService
from legal_text_mcp_de.legal_texts.validation import validate_generated_package
from scripts.verify_dsgvo_full_counts import main as verify_dsgvo_full_counts_main


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "eurlex_dsgvo"
XML_FIXTURE = FIXTURE_DIR / "dsgvo_articles_recitals.xml"
POLICY_FIXTURE = FIXTURE_DIR / "source_policy.json"


def dsgvo_source() -> dict:
    return {
        "source_kind": "eur-lex-cellar",
        "source_identifier": "CELEX:32016R0679",
        "source_url": "https://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0004.02/DOC_2",
        "retrieved_at": "2026-05-15T00:00:00Z",
        "stand_date": None,
        "stand_date_status": "official",
        "content_hash": "fixture-content-hash",
        "source_metadata": {
            "celex": "32016R0679",
            "cellar_work": "3e485e15-11bd-11e6-ba9a-01aa75ed71a1",
            "expression": "0004.02",
            "language": "de",
            "document": "DOC_2",
            "version_policy": "official-eurlex-cellar-doc2-german-expression",
            "consolidation_policy": "fixture-represents-selected-official-expression",
        },
    }


def parse_fixture_norms() -> list[dict]:
    return parse_dsgvo_xml(
        XML_FIXTURE,
        {"canonical_id": "dsgvo_eu_2016_679"},
        dsgvo_source(),
    )


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_package(package_dir: Path, norms: list[dict]) -> None:
    package_dir.mkdir()
    laws = [
        {
            "canonical_id": "dsgvo_eu_2016_679",
            "display_code": "DSGVO",
            "display_name": "Datenschutz-Grundverordnung",
            "source": dsgvo_source(),
            "aliases": ["dsgvo", "gdpr"],
            "norm_count": len(norms),
        }
    ]
    manifest = {
        "schema_version": "corpus-manifest.v1",
        "dataset_id": "dsgvo-fixture",
        "package_id": "dsgvo-fixture",
        "created_at": "2026-05-15T00:00:00Z",
        "validation_mode": "terminal",
        "generator": {"name": "dsgvo-fixture", "version": "test"},
        "parser_versions": {"eurlex": "test"},
        "discovered_sources": [
            {
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
                "source_url": dsgvo_source()["source_url"],
                "content_sha256": "fixture-content-hash",
                "retrieved_at": "2026-05-15T00:00:00Z",
                "parser_version": "test",
                "generated_law_ids": ["dsgvo_eu_2016_679"],
                "generated_norm_ids": [norm["canonical_id"] for norm in norms],
            }
        ],
        "canonical_ids": [
            {
                "canonical_id": "dsgvo_eu_2016_679",
                "source_family": "eur-lex-cellar",
                "source_id": "eur-lex-cellar:32016R0679",
                "celex": "32016R0679",
            }
        ],
        "relationship_sources": [],
        "source_limitations": [],
    }
    files = {
        "laws.json": laws,
        "norms.json": norms,
        "manifest.json": manifest,
        "source-limitations.json": [],
        "relationships.json": [],
        "readiness.json": {
            "stage": "normalized_dataset",
            "state": "ready",
            "details": {"law_count": 1, "norm_count": len(norms)},
        },
        "search-index.json": {"documents": []},
    }
    for name, data in files.items():
        write_json(package_dir / name, data)
    package = {
        "schema_version": "generated-package.v1",
        "dataset_id": "dsgvo-fixture",
        "package_id": "dsgvo-fixture",
        "generated_at": "2026-05-15T00:00:00Z",
        "generator": {"name": "dsgvo-fixture", "version": "test"},
        "manifest_path": "manifest.json",
        "readiness_path": "readiness.json",
        "record_counts": {
            "laws": 1,
            "norms": len(norms),
            "relationships": 0,
            "source_limitations": 0,
            "discovered_sources": 1,
            "imported_sources": 1,
        },
        "content_hashes": {name: f"sha256:{file_hash(package_dir / name)}" for name in files},
        "validation_mode": "terminal",
        "source_families": ["eur-lex-cellar"],
    }
    write_json(package_dir / "package.json", package)


def test_eurlex_parser_extracts_articles_and_formex_considerations_as_first_class_norms():
    norms = parse_fixture_norms()

    assert [norm["norm_id"] for norm in norms] == ["art:1", "art:99", "recital:1", "recital:173"]
    recital = next(norm for norm in norms if norm["norm_id"] == "recital:1")
    assert recital["unit"] == "recital"
    assert recital["value"] == "1"
    assert recital["canonical_id"] == "dsgvo_eu_2016_679/recital:1"
    assert "Grundrecht" in recital["text"]
    assert next(norm for norm in norms if norm["norm_id"] == "recital:173")["value"] == "173"
    article = next(norm for norm in norms if norm["norm_id"] == "art:1")
    assert article["unit"] == "art"
    assert article["subdivisions"][0]["path"] == "abs:1"


def test_eurlex_parser_preserves_reduced_recital_fixture_support(tmp_path):
    xml_path = tmp_path / "legacy-recital.xml"
    xml_path.write_text(
        """<ROOT>
  <LG.DOC>DE</LG.DOC>
  <ACT>
    <RECITAL IDENTIFIER="001">
      <NO.P>1</NO.P>
      <P>Legacy reduced recital fixture text.</P>
    </RECITAL>
  </ACT>
</ROOT>
""",
        encoding="utf-8",
    )

    norms = parse_dsgvo_xml(xml_path, {"canonical_id": "dsgvo_eu_2016_679"}, dsgvo_source())

    assert [norm["norm_id"] for norm in norms] == ["recital:1"]
    assert norms[0]["unit"] == "recital"
    assert norms[0]["text"].endswith("Legacy reduced recital fixture text.")


def test_recital_resolver_and_search_are_additive(tmp_path):
    package_dir = tmp_path / "package"
    write_package(package_dir, parse_fixture_norms())

    dataset = NormalizedDataset.load(package_dir, require_search_index=True)
    exact = get_norm(dataset, "DSGVO", "recital:1")
    structured = resolve_citation(dataset, "DSGVO", "recital", "173")
    search = SearchService(dataset).search_laws("Grundrecht", codes=["DSGVO"])

    assert exact["norm"]["canonical_id"] == "dsgvo_eu_2016_679/recital:1"
    assert structured["citation"]["label"] == "DSGVO ErwG 173"
    assert search["results"][0]["norm_id"] == "recital:1"


def test_generated_dsgvo_fixture_package_passes_strict_validation(tmp_path):
    package_dir = tmp_path / "package"
    write_package(package_dir, parse_fixture_norms())

    assert validate_generated_package(package_dir, require_search_index=True) == []


def test_dsgvo_source_policy_fixture_defines_full_count_contract():
    policy = json.loads(POLICY_FIXTURE.read_text(encoding="utf-8"))

    assert policy["celex"] == "32016R0679"
    assert policy["cellar_work"] == "3e485e15-11bd-11e6-ba9a-01aa75ed71a1"
    assert policy["expression"] == "0004.02"
    assert policy["language"] == "de"
    assert policy["document"] == "DOC_2"
    assert policy["version_policy"]
    assert policy["consolidation_policy"]
    assert policy["content_hash"]
    assert policy["article_count"] == 99
    assert policy["recital_count"] == 173


def test_verify_dsgvo_full_counts_script_writes_artifact(tmp_path):
    package_dir = tmp_path / "package"
    output = tmp_path / "full-counts.json"
    write_package(package_dir, parse_fixture_norms())
    policy = json.loads(POLICY_FIXTURE.read_text(encoding="utf-8"))
    policy["article_count"] = 2
    policy["recital_count"] = 2
    policy_path = tmp_path / "policy.json"
    write_json(policy_path, policy)

    exit_code = verify_dsgvo_full_counts_main(
        [
            "--package",
            str(package_dir),
            "--policy",
            str(policy_path),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    artifact = json.loads(output.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "dsgvo-full-counts.v1"
    assert artifact["policy"]["cellar_work"] == "3e485e15-11bd-11e6-ba9a-01aa75ed71a1"
    assert artifact["policy"]["expression"] == "0004.02"
    assert artifact["policy"]["content_hash"] == "fixture-content-hash"
    assert artifact["selected_source"]["content_hash"] == "fixture-content-hash"
    assert artifact["counts"] == {"articles": 2, "recitals": 2}
    assert artifact["actual_counts"] == {"articles": 2, "recitals": 2}
    assert artifact["expected_counts"] == {"articles": 2, "recitals": 2}
    assert artifact["boundary_samples"]["articles"]["missing"] == []
    assert artifact["boundary_samples"]["recitals"]["missing"] == []
    assert artifact["validation_errors"] == []


def test_verify_dsgvo_full_counts_rejects_cellar_work_mismatch(tmp_path):
    package_dir = tmp_path / "package"
    output = tmp_path / "full-counts.json"
    write_package(package_dir, parse_fixture_norms())
    policy = json.loads(POLICY_FIXTURE.read_text(encoding="utf-8"))
    policy["article_count"] = 2
    policy["recital_count"] = 2
    policy["cellar_work"] = "unexpected-cellar-work"
    policy_path = tmp_path / "policy.json"
    write_json(policy_path, policy)

    exit_code = verify_dsgvo_full_counts_main(
        [
            "--package",
            str(package_dir),
            "--policy",
            str(policy_path),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 1
    artifact = json.loads(output.read_text(encoding="utf-8"))
    assert artifact["policy"]["cellar_work"] == "unexpected-cellar-work"
    assert (
        "source metadata cellar_work 3e485e15-11bd-11e6-ba9a-01aa75ed71a1 "
        "does not match expected unexpected-cellar-work"
    ) in artifact["validation_errors"]


def test_verify_dsgvo_full_counts_rejects_expression_mismatch(tmp_path):
    package_dir = tmp_path / "package"
    output = tmp_path / "full-counts.json"
    write_package(package_dir, parse_fixture_norms())
    policy = json.loads(POLICY_FIXTURE.read_text(encoding="utf-8"))
    policy["article_count"] = 2
    policy["recital_count"] = 2
    policy["expression"] = "9999.99"
    policy_path = tmp_path / "policy.json"
    write_json(policy_path, policy)

    exit_code = verify_dsgvo_full_counts_main(
        [
            "--package",
            str(package_dir),
            "--policy",
            str(policy_path),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 1
    artifact = json.loads(output.read_text(encoding="utf-8"))
    assert artifact["policy"]["expression"] == "9999.99"
    assert "source metadata expression 0004.02 does not match expected 9999.99" in artifact["validation_errors"]


def test_verify_dsgvo_full_counts_rejects_missing_policy_content_hash(tmp_path):
    package_dir = tmp_path / "package"
    output = tmp_path / "full-counts.json"
    write_package(package_dir, parse_fixture_norms())
    policy = json.loads(POLICY_FIXTURE.read_text(encoding="utf-8"))
    policy["article_count"] = 2
    policy["recital_count"] = 2
    policy.pop("content_hash")
    policy_path = tmp_path / "policy.json"
    write_json(policy_path, policy)

    exit_code = verify_dsgvo_full_counts_main(
        [
            "--package",
            str(package_dir),
            "--policy",
            str(policy_path),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 1
    artifact = json.loads(output.read_text(encoding="utf-8"))
    assert "policy missing content_hash" in artifact["validation_errors"]
