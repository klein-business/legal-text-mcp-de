# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for law-specific legal:// MCP resource handlers (B3-B8)."""

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


def _mime(result) -> str | None:
    contents = result if isinstance(result, list) else [result]
    first = contents[0]
    return getattr(first, "mimeType", None) or getattr(first, "mime_type", None)


# ---------------------------------------------------------------------------
# B3: legal://laws
# ---------------------------------------------------------------------------


def test_legal_laws_returns_json_list():
    app = _fixture_app()
    result = _read(app, "legal://laws")
    text = _text(result)
    data = json.loads(text)
    assert "laws" in data
    assert isinstance(data["laws"], list)
    assert len(data["laws"]) > 0


def test_legal_laws_list_contains_bgb():
    app = _fixture_app()
    result = _read(app, "legal://laws")
    text = _text(result)
    data = json.loads(text)
    codes = [law.get("canonical_id") for law in data["laws"]]
    assert "bgb" in codes


# ---------------------------------------------------------------------------
# B4: legal://laws/{code}
# ---------------------------------------------------------------------------


def test_legal_laws_code_returns_markdown_with_h1():
    app = _fixture_app()
    result = _read(app, "legal://laws/bgb")
    text = _text(result)
    assert text.startswith("#")
    assert "BGB" in text or "bgb" in text.lower()


def test_legal_laws_code_contains_normen_section():
    app = _fixture_app()
    result = _read(app, "legal://laws/bgb")
    text = _text(result)
    assert "## Normen" in text


def test_legal_laws_code_unknown_returns_error_markdown():
    app = _fixture_app()
    result = _read(app, "legal://laws/does-not-exist")
    text = _text(result)
    assert "Error" in text or "error" in text


# ---------------------------------------------------------------------------
# B5: legal://laws/{code}/full
# ---------------------------------------------------------------------------


def test_legal_laws_code_full_returns_markdown():
    app = _fixture_app()
    result = _read(app, "legal://laws/bgb/full")
    text = _text(result)
    assert text.startswith("#")


def test_legal_laws_code_full_contains_multiple_headings():
    app = _fixture_app()
    result = _read(app, "legal://laws/bgb/full")
    text = _text(result)
    # Should have at least the law heading + one norm heading
    heading_count = text.count("\n# ")
    assert heading_count >= 1 or text.startswith("# ")


def test_legal_laws_code_full_contains_norm_text():
    app = _fixture_app()
    result = _read(app, "legal://laws/bgb/full")
    text = _text(result)
    # fixture BGB has norms par:309, par:312, par:355
    assert "312" in text or "309" in text or "355" in text


# ---------------------------------------------------------------------------
# B6: legal://laws/{code}/norms/{norm_id}
# ---------------------------------------------------------------------------


def test_legal_laws_norms_norm_id_returns_markdown():
    app = _fixture_app()
    result = _read(app, "legal://laws/bgb/norms/par:312")
    text = _text(result)
    assert text.startswith("#")


def test_legal_laws_norms_norm_id_contains_stand():
    app = _fixture_app()
    result = _read(app, "legal://laws/bgb/norms/par:312")
    text = _text(result)
    assert "Stand" in text or "Retrieved" in text


def test_legal_laws_norms_norm_id_unknown_returns_error():
    app = _fixture_app()
    result = _read(app, "legal://laws/bgb/norms/par:9999")
    text = _text(result)
    assert "Error" in text or "error" in text


# ---------------------------------------------------------------------------
# B7: legal://laws/{code}/norms/{norm_id}/relationships
# ---------------------------------------------------------------------------


def test_legal_laws_norms_relationships_returns_json():
    app = _fixture_app()
    result = _read(app, "legal://laws/bgb/norms/par:312/relationships")
    text = _text(result)
    data = json.loads(text)
    assert "relationships" in data
    assert "norm" in data


def test_legal_laws_norms_relationships_unknown_returns_error_json():
    app = _fixture_app()
    result = _read(app, "legal://laws/bgb/norms/par:9999/relationships")
    text = _text(result)
    data = json.loads(text)
    assert "error" in data


# ---------------------------------------------------------------------------
# B8: legal://laws/{code}/source
# ---------------------------------------------------------------------------


def test_legal_laws_code_source_returns_json():
    app = _fixture_app()
    result = _read(app, "legal://laws/bgb/source")
    text = _text(result)
    data = json.loads(text)
    assert "sources" in data


def test_legal_laws_code_source_unknown_returns_error_json():
    app = _fixture_app()
    result = _read(app, "legal://laws/does-not-exist/source")
    text = _text(result)
    data = json.loads(text)
    assert "error" in data
