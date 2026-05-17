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
