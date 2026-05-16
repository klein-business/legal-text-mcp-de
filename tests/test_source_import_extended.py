# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Extended tests for legal_text_mcp_de.legal_texts.importer.

Lifts the importer.py coverage from 63% to >=90% by exercising the
default-fetch HTTP path, the snapshot-write path, the error branches,
and the metadata builder. These complement the smoke tests in
test_source_import.py without duplicating them.
"""

from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from legal_text_mcp_de.legal_texts.importer import (
    default_fetch,
    diff_manifests,
    import_snapshot,
    probe_known_invalid,
    probe_source,
    sha256_bytes,
    source_metadata,
    utc_now,
    validate_dsgvo_doc2,
    validate_eurlex_german_act_xml,
)
from legal_text_mcp_de.legal_texts.sources import SOURCE_SPECS


# ---------- pure helpers ----------


def test_sha256_bytes_known_value() -> None:
    # "abc" -> sha256 = ba7816bf...
    assert sha256_bytes(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_utc_now_returns_iso_z_format() -> None:
    value = utc_now()
    # ends with Z, no fractional seconds, parseable
    assert value.endswith("Z")
    assert "." not in value
    assert "T" in value


# ---------- source_metadata ----------


def test_source_metadata_includes_hash_and_known_issues_list() -> None:
    spec = SOURCE_SPECS["bgb"]
    meta = source_metadata(spec, b"payload", "2026-05-16T00:00:00Z")
    assert meta["content_hash"] == sha256_bytes(b"payload")
    assert meta["source_kind"] == spec.source_kind
    assert meta["source_identifier"] == spec.source_identifier
    assert meta["retrieved_at"] == "2026-05-16T00:00:00Z"
    assert meta["known_issues"] == []
    assert meta["stand_date_status"] == "not_exposed"


# ---------- validate_eurlex_german_act_xml ----------


def test_validate_eurlex_german_act_xml_accepts_well_formed() -> None:
    payload = (
        b'<LG.DOC>DE</LG.DOC>'
        b'<ACT><ARTICLE IDENTIFIER="001">Artikel 1</ARTICLE></ACT>'
    )
    # Should not raise.
    validate_eurlex_german_act_xml(payload, celex="32016R0679", content_type="application/xml")


def test_validate_eurlex_german_act_xml_rejects_missing_article() -> None:
    payload = b"<LG.DOC>DE</LG.DOC><ACT>no articles</ACT>"
    with pytest.raises(Exception) as exc_info:
        validate_eurlex_german_act_xml(
            payload, celex="32016R0679", label="DSGVO Cellar DOC_2"
        )
    # Either the label or the missing-marker name appears in the error.
    assert "ARTICLE" in str(exc_info.value) or "DOC_2" in str(exc_info.value)


def test_validate_dsgvo_doc2_delegates_to_eurlex_validator() -> None:
    with pytest.raises(Exception):
        validate_dsgvo_doc2(b"<LG.DOC>DE</LG.DOC>missing markers")


# ---------- default_fetch (HTTP path) ----------


class _FakeResponse:
    """Minimal urlopen-compatible context manager."""

    def __init__(self, status: int, headers: dict[str, str], body: bytes) -> None:
        self.status = status
        self.headers = headers
        self._body = body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def test_default_fetch_returns_status_headers_body() -> None:
    fake_resp = _FakeResponse(200, {"Content-Type": "application/xml"}, b"<xml/>")
    with patch("urllib.request.urlopen", return_value=fake_resp):
        status, headers, body = default_fetch("https://example.invalid/test")
    assert status == 200
    assert headers["content-type"] == "application/xml"
    assert body == b"<xml/>"


def test_default_fetch_returns_http_error_payload_on_404() -> None:
    err = urllib.error.HTTPError(
        url="https://example.invalid/missing",
        code=404,
        msg="Not Found",
        hdrs={"Content-Type": "text/html"},  # type: ignore[arg-type]
        fp=io.BytesIO(b"<html>not found</html>"),
    )
    with patch("urllib.request.urlopen", side_effect=err):
        status, headers, body = default_fetch("https://example.invalid/missing")
    assert status == 404
    assert headers["content-type"] == "text/html"
    assert body == b"<html>not found</html>"


# ---------- probe_source error path ----------


def test_probe_source_raises_when_status_not_200() -> None:
    def failing_fetch(_url: str) -> tuple[int, dict[str, str], bytes]:
        return 503, {"content-type": "text/plain"}, b"upstream error"

    with pytest.raises(Exception) as exc_info:
        probe_source(SOURCE_SPECS["bgb"], fetch=failing_fetch)
    assert "503" in str(exc_info.value) or "unavailable" in str(exc_info.value).lower()


def test_probe_known_invalid_lists_all_invalid_paths() -> None:
    def always_404(_url: str) -> tuple[int, dict[str, str], bytes]:
        return 404, {"content-type": "text/html"}, b""

    results = probe_known_invalid(fetch=always_404)
    # The result count must equal the total invalid_urls across all SOURCE_SPECS.
    expected = sum(len(spec.invalid_urls) for spec in SOURCE_SPECS.values())
    assert len(results) == expected
    assert {r["status"] for r in results} == {404}
    assert all(r["expected_status"] == 404 for r in results)


# ---------- import_snapshot (write path + dsgvo validation branch) ----------


def _stub_fetch_for_snapshot(url: str) -> tuple[int, dict[str, str], bytes]:
    """Return well-formed bodies so import_snapshot succeeds for every SOURCE_SPEC."""

    if "DOC_2" in url or "celex/32016R0679" in url:
        body = (
            b'<LG.DOC>DE</LG.DOC>'
            b'<ACT><ARTICLE IDENTIFIER="005">Artikel 5</ARTICLE></ACT>'
        )
        return 200, {"content-type": "application/xml"}, body
    # Non-cellar sources return arbitrary bytes (treated as a zip)
    return 200, {"content-type": "application/zip"}, b"zip-payload"


def test_import_snapshot_writes_manifest_and_raw_files(tmp_path: Path) -> None:
    manifest = import_snapshot(
        tmp_path,
        snapshot_id="testsnap",
        fetch=_stub_fetch_for_snapshot,
    )
    assert manifest["snapshot_id"] == "testsnap"
    assert manifest["validation"]["state"] == "ready"
    assert manifest["validation"]["entry_count"] == len(manifest["entries"])
    # Manifest file is on disk.
    manifest_file = tmp_path / "testsnap" / "manifest.json"
    assert manifest_file.exists()
    on_disk: dict[str, Any] = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert on_disk["dataset_id"] == "testsnap"
    # Every entry must have a corresponding raw file with the recorded byte size.
    for entry in manifest["entries"]:
        raw_path = Path(entry["raw_path"])
        assert raw_path.exists()
        assert raw_path.stat().st_size == entry["bytes"]
    # Raw filenames carry the canonical id and the right suffix.
    raw_names = sorted(p.name for p in (tmp_path / "testsnap").iterdir() if p.is_file())
    assert any(name.endswith(".xml") for name in raw_names)  # at least one cellar source
    assert any(name.endswith(".zip") for name in raw_names)  # at least one gii source


def test_import_snapshot_auto_generates_snapshot_id(tmp_path: Path) -> None:
    manifest = import_snapshot(tmp_path, fetch=_stub_fetch_for_snapshot)
    assert manifest["snapshot_id"]
    # Auto id matches the YYYYMMDDTHHMMSSZ pattern (15 chars + 'Z' = 16 chars).
    assert len(manifest["snapshot_id"]) == 16
    assert manifest["snapshot_id"].endswith("Z")


def test_import_snapshot_raises_when_source_is_unavailable(tmp_path: Path) -> None:
    def failing_fetch(_url: str) -> tuple[int, dict[str, str], bytes]:
        return 502, {"content-type": "text/plain"}, b"upstream bad gateway"

    with pytest.raises(Exception) as exc_info:
        import_snapshot(tmp_path, fetch=failing_fetch)
    assert "502" in str(exc_info.value) or "unavailable" in str(exc_info.value).lower()


# ---------- diff_manifests edge cases ----------


def test_diff_manifests_detects_added_and_removed() -> None:
    """An added entry counts as both 'added' and 'changed' (vs absent old hash).

    This documents the current diff_manifests behaviour: 'changed' is computed
    against old_hashes.get(law_id) so a newly-added law also appears in 'changed'.
    Callers that want strict diff semantics should subtract 'added' from 'changed'.
    """

    old = {
        "entries": [
            {"canonical_id": "bgb", "source": {"content_hash": "h1"}},
            {"canonical_id": "egbgb", "source": {"content_hash": "h2"}},
        ]
    }
    new = {
        "entries": [
            {"canonical_id": "bgb", "source": {"content_hash": "h1"}},
            {"canonical_id": "tdddg", "source": {"content_hash": "h3"}},
        ]
    }
    result = diff_manifests(old, new)
    assert result["added"] == ["tdddg"]
    assert result["removed"] == ["egbgb"]
    # Newly-added entries also appear in 'changed' (old_hash is missing).
    assert "tdddg" in result["changed"]
    assert "bgb" not in result["changed"]  # unchanged hash


def test_diff_manifests_empty_inputs() -> None:
    assert diff_manifests({}, {}) == {"added": [], "removed": [], "changed": []}
