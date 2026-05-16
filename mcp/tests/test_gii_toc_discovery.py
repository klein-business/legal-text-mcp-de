# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import json
from pathlib import Path

from legal_texts.gii_toc import (
    DEFAULT_GII_TOC_URL,
    GII_DISCOVERY_ARTIFACT_SCHEMA_VERSION,
    FetchResult,
    artifact_has_failures,
    build_gii_discovery_artifact,
    fetch_gii_discovery_artifact,
    parse_gii_toc,
    write_gii_discovery_artifact,
)
from legal_texts.manifest import validate_corpus_manifest


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "gii_toc"


def read_fixture(name: str) -> bytes:
    return (FIXTURE_DIR / name).read_bytes()


def assert_has_error(errors: list[str], expected: str) -> None:
    assert any(expected in error for error in errors), errors


def manifest_with_source_limitation(limitation: dict) -> dict:
    return {
        "schema_version": "corpus-manifest.v1",
        "dataset_id": "test",
        "package_id": "test",
        "created_at": "2026-05-15T00:00:00Z",
        "validation_mode": "discovery",
        "generator": {"name": "test", "version": "test"},
        "parser_versions": {},
        "discovered_sources": [],
        "canonical_ids": [],
        "relationship_sources": [],
        "source_limitations": [limitation],
    }


def test_parse_valid_gii_toc_builds_discovery_manifest_records():
    artifact = build_gii_discovery_artifact(
        read_fixture("valid_toc.xml"),
        toc_url=DEFAULT_GII_TOC_URL,
        retrieved_at="2026-05-15T00:00:00Z",
        parser_version="test",
        discovery_artifact_id="artifact:test",
    )

    assert artifact["schema_version"] == GII_DISCOVERY_ARTIFACT_SCHEMA_VERSION
    assert artifact["toc_url"] == DEFAULT_GII_TOC_URL
    assert artifact["discovered_gii_items"] == 3
    assert artifact["source_path_count"] == 3
    assert artifact["duplicate_count"] == 0
    assert artifact["source_paths"] == ["abc_2024", "bgb", "ttdsg"]
    assert artifact["malformed_items"] == []
    assert artifact["validation_errors"] == []

    discovered = artifact["discovered_gii_records"]
    bgb = next(item for item in discovered if item["source_path"] == "bgb")
    assert bgb["source_family"] == "gii"
    assert bgb["source_id"] == "gii:bgb"
    assert bgb["xml_zip_url"] == "https://www.gesetze-im-internet.de/bgb/xml.zip"
    assert bgb["index_url"] == "https://www.gesetze-im-internet.de/bgb/index.html"
    assert bgb["toc_sha256"] == artifact["toc_sha256"]
    assert bgb["source_metadata"]["original_title"] == "Buergerliches Gesetzbuch"
    assert bgb["source_metadata"]["original_link"] == "http://www.gesetze-im-internet.de/bgb/xml.zip"
    assert "bgb" in bgb["alias_candidates"]

    ttdsg = next(item for item in discovered if item["source_path"] == "ttdsg")
    assert ttdsg["source_metadata"]["original_link"] == "/ttdsg/xml.zip"
    assert ttdsg["xml_zip_url"] == "https://www.gesetze-im-internet.de/ttdsg/xml.zip"
    assert ttdsg["index_url"] == "https://www.gesetze-im-internet.de/ttdsg/index.html"
    assert "tdddg" in ttdsg["alias_candidates"]
    assert "TDDDG" in ttdsg["alias_candidates"]

    encoded = next(item for item in discovered if item["source_path"] == "abc_2024")
    assert encoded["source_metadata"]["original_link"] == "https://www.gesetze-im-internet.de/ABC%5F2024/xml.zip"
    assert encoded["xml_zip_url"] == "https://www.gesetze-im-internet.de/abc_2024/xml.zip"

    manifest = artifact["manifest"]
    assert manifest["schema_version"] == "corpus-manifest.v1"
    assert manifest["validation_mode"] == "discovery"
    assert manifest["discovered_sources"] == discovered
    assert validate_corpus_manifest(manifest, require_terminal_states=False) == []


def test_parse_gii_toc_reports_duplicate_source_paths_as_validation_errors():
    artifact = build_gii_discovery_artifact(
        read_fixture("duplicate_toc.xml"),
        toc_url=DEFAULT_GII_TOC_URL,
        retrieved_at="2026-05-15T00:00:00Z",
        parser_version="test",
    )

    assert_has_error(artifact["validation_errors"], "duplicate GII source_path bgb")
    assert artifact["duplicate_count"] == 1


def test_parse_gii_toc_reports_malformed_xml_as_toc_limitation():
    artifact = build_gii_discovery_artifact(
        read_fixture("malformed_toc.xml"),
        toc_url=DEFAULT_GII_TOC_URL,
        retrieved_at="2026-05-15T00:00:00Z",
        parser_version="test",
    )

    assert artifact["discovered_gii_items"] == 0
    assert artifact["discovered_gii_records"] == []
    assert artifact["toc_limitation"]["terminal_state"] == "parse_failed"
    assert artifact["toc_limitation"]["limitation_id"] == "gii-toc-parse-failed"
    assert artifact["toc_limitation"]["parser_version"] == "test"
    assert "XML parse failed" in artifact["toc_limitation"]["diagnostic"]
    assert artifact["toc_limitation"]["details"]["toc_url"] == DEFAULT_GII_TOC_URL
    assert "XML parse failed" in artifact["toc_limitation"]["reason"]
    assert_has_error(artifact["validation_errors"], "TOC XML parse failed")
    assert validate_corpus_manifest(manifest_with_source_limitation(artifact["toc_limitation"])) == []


def test_parse_gii_toc_reports_malformed_items_without_silently_dropping():
    result = parse_gii_toc(read_fixture("malformed_item_toc.xml"), toc_url=DEFAULT_GII_TOC_URL)

    assert [item["source_path"] for item in result.items] == ["bgb"]
    assert len(result.malformed_items) == 1
    assert result.malformed_items[0]["reason"] == "missing xml.zip link"


def test_build_gii_discovery_artifact_fails_when_malformed_items_exist():
    artifact = build_gii_discovery_artifact(
        read_fixture("malformed_item_toc.xml"),
        toc_url=DEFAULT_GII_TOC_URL,
        retrieved_at="2026-05-15T00:00:00Z",
        parser_version="test",
    )

    assert artifact["discovered_gii_items"] == 1
    assert artifact["malformed_items"]
    assert_has_error(artifact["validation_errors"], "malformed GII TOC item at index")
    assert artifact_has_failures(artifact)


def test_fetch_gii_discovery_artifact_records_non_200_response():
    artifact = fetch_gii_discovery_artifact(
        toc_url=DEFAULT_GII_TOC_URL,
        fetcher=lambda url: FetchResult(status=503, content=b"temporarily unavailable", url=url),
        retrieved_at="2026-05-15T00:00:00Z",
        parser_version="test",
    )

    assert artifact["toc_limitation"]["terminal_state"] == "source_unavailable"
    assert artifact["toc_limitation"]["limitation_id"] == "gii-toc-source-unavailable"
    assert artifact["toc_limitation"]["details"]["toc_url"] == DEFAULT_GII_TOC_URL
    assert artifact["toc_limitation"]["retryable"] is True
    assert artifact["toc_limitation"]["http_status"] == 503
    assert_has_error(artifact["validation_errors"], "GII TOC fetch failed with HTTP status 503")
    assert artifact_has_failures(artifact)
    assert validate_corpus_manifest(manifest_with_source_limitation(artifact["toc_limitation"])) == []


def test_fetch_gii_discovery_artifact_records_fetch_exception():
    def failing_fetcher(url: str) -> FetchResult:
        raise TimeoutError("network timeout")

    artifact = fetch_gii_discovery_artifact(
        toc_url=DEFAULT_GII_TOC_URL,
        fetcher=failing_fetcher,
        retrieved_at="2026-05-15T00:00:00Z",
        parser_version="test",
    )

    assert artifact["toc_limitation"]["terminal_state"] == "source_unavailable"
    assert artifact["toc_limitation"]["limitation_id"] == "gii-toc-source-unavailable"
    assert artifact["toc_limitation"]["details"]["toc_url"] == DEFAULT_GII_TOC_URL
    assert artifact["toc_limitation"]["retryable"] is True
    assert artifact["toc_limitation"]["error_code"] == "TimeoutError"
    assert_has_error(artifact["validation_errors"], "GII TOC fetch raised TimeoutError")
    assert artifact_has_failures(artifact)
    assert validate_corpus_manifest(manifest_with_source_limitation(artifact["toc_limitation"])) == []


def test_write_gii_discovery_artifact_writes_stable_json(tmp_path):
    artifact = build_gii_discovery_artifact(
        read_fixture("valid_toc.xml"),
        toc_url=DEFAULT_GII_TOC_URL,
        retrieved_at="2026-05-15T00:00:00Z",
        parser_version="test",
    )
    output = tmp_path / "artifact.json"

    write_gii_discovery_artifact(artifact, output)

    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["schema_version"] == GII_DISCOVERY_ARTIFACT_SCHEMA_VERSION
    assert written["discovered_gii_items"] == 3
    assert written["source_paths"] == ["abc_2024", "bgb", "ttdsg"]
