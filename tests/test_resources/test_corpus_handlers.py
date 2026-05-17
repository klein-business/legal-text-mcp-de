# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for corpus-wide legal:// MCP resource handlers (B9, B10)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from legal_text_mcp_de.legal_texts.dataset import NormalizedDataset
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime
from legal_text_mcp_de.server import create_mcp_app


FIXTURE_DATASET = Path(__file__).parent.parent / "fixtures" / "normalized"


def _fixture_app():
    dataset = NormalizedDataset.load(FIXTURE_DATASET, require_search_index=True)
    return create_mcp_app(LegalTextRuntime.from_dataset(dataset))


def _read(app, uri: str):
    try:
        result = app.read_resource(uri)
    except TypeError:
        result = asyncio.get_event_loop().run_until_complete(app.read_resource(uri))
    if asyncio.iscoroutine(result):
        result = asyncio.get_event_loop().run_until_complete(result)
    return result


def _text(result) -> str:
    contents = result if isinstance(result, list) else [result]
    first = contents[0]
    # FastMCP mcp.server.lowlevel.helper_types.ReadResourceContents uses .content
    # Newer mcp[cli] ResourceContents use .text
    return getattr(first, "content", None) or getattr(first, "text", str(first))


# ---------------------------------------------------------------------------
# B9: legal://corpus/coverage
# ---------------------------------------------------------------------------


def test_corpus_coverage_returns_json():
    app = _fixture_app()
    result = _read(app, "legal://corpus/coverage")
    text = _text(result)
    data = json.loads(text)
    assert isinstance(data, dict)


def test_corpus_coverage_has_counts():
    app = _fixture_app()
    result = _read(app, "legal://corpus/coverage")
    text = _text(result)
    data = json.loads(text)
    assert "counts" in data
    counts = data["counts"]
    assert "laws" in counts
    assert counts["laws"] > 0


def test_corpus_coverage_has_source_families():
    app = _fixture_app()
    result = _read(app, "legal://corpus/coverage")
    text = _text(result)
    data = json.loads(text)
    assert "source_families" in data
    assert isinstance(data["source_families"], list)


# ---------------------------------------------------------------------------
# B10: legal://corpus/limitations
# ---------------------------------------------------------------------------


def test_corpus_limitations_returns_json():
    app = _fixture_app()
    result = _read(app, "legal://corpus/limitations")
    text = _text(result)
    data = json.loads(text)
    assert isinstance(data, dict)


def test_corpus_limitations_has_source_limitations_key():
    app = _fixture_app()
    result = _read(app, "legal://corpus/limitations")
    text = _text(result)
    data = json.loads(text)
    assert "source_limitations" in data


# ---------------------------------------------------------------------------
# B11: legal://corpus/manifest (improved)
# ---------------------------------------------------------------------------


def test_corpus_manifest_returns_json_with_bundle_fields():
    app = _fixture_app()
    result = _read(app, "legal://corpus/manifest")
    text = _text(result)
    data = json.loads(text)
    # Manifest must expose bundle-level keys (even if values are None in fixture mode)
    assert "generated_package_present" in data
    assert "counts" in data
    assert "source_families" in data


def test_corpus_manifest_counts_has_laws():
    app = _fixture_app()
    result = _read(app, "legal://corpus/manifest")
    text = _text(result)
    data = json.loads(text)
    assert "counts" in data
    assert "laws" in data["counts"]
    assert data["counts"]["laws"] > 0
