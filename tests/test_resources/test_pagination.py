# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for legal://laws pagination (B13).

FastMCP 1.27.x cannot route query-string parameters as URI template
variables — only path components are supported.  Pagination is therefore
exposed via path components:

    legal://laws                       → first page (cursor=0, limit=50)
    legal://laws/page/{cursor}/{limit} → explicit page
"""

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


def _text(out) -> str:
    contents = out if isinstance(out, list) else [out]
    first = contents[0]
    return getattr(first, "content", None) or getattr(first, "text", None) or str(first)


# ---------------------------------------------------------------------------
# Default handler — legal://laws stays backward-compatible (returns first page)
# ---------------------------------------------------------------------------


def test_legal_laws_default_returns_first_page():
    """legal://laws returns a paginated envelope — backward-compat with B3."""
    app = _fixture_app()
    raw = _text(_read(app, "legal://laws"))
    page = json.loads(raw)
    assert "entries" in page, f"missing 'entries' key: {list(page)}"
    assert isinstance(page["entries"], list)
    # Default limit is 50; fixture corpus has 10 laws
    assert len(page["entries"]) <= 50
    assert "next_cursor" in page
    assert "total" in page


# ---------------------------------------------------------------------------
# Paginated handler — legal://laws/page/{cursor}/{limit}
# ---------------------------------------------------------------------------


def test_legal_laws_page_cursor_and_limit():
    """Page 1 of 2 (cursor=0, limit=2) has at most 2 entries and carries next_cursor."""
    app = _fixture_app()
    raw = _text(_read(app, "legal://laws/page/0/2"))
    page1 = json.loads(raw)
    assert "entries" in page1, f"missing 'entries': {list(page1)}"
    assert len(page1["entries"]) <= 2
    assert "next_cursor" in page1
    assert "total" in page1


def test_legal_laws_page_disjoint_pages():
    """Two consecutive pages must not overlap."""
    app = _fixture_app()
    raw1 = _text(_read(app, "legal://laws/page/0/2"))
    page1 = json.loads(raw1)

    if page1["next_cursor"] is None:
        # Corpus too small to have a second page — skip disjoint check
        return

    raw2 = _text(_read(app, f"legal://laws/page/{page1['next_cursor']}/2"))
    page2 = json.loads(raw2)

    ids1 = {e.get("canonical_id") for e in page1["entries"]}
    ids2 = {e.get("canonical_id") for e in page2["entries"]}
    assert ids1.isdisjoint(ids2), f"pages overlap: {ids1 & ids2}"


def test_legal_laws_page_limit_clamped_to_500():
    """limit > 500 is silently clamped to 500."""
    app = _fixture_app()
    raw = _text(_read(app, "legal://laws/page/0/9999"))
    page = json.loads(raw)
    # With fixture corpus of 10 laws, limit=9999 → returns all 10 (≤ 500)
    assert len(page["entries"]) <= 500


def test_legal_laws_page_second_page_has_no_overlap_with_full_default():
    """The paginated handler and the default handler agree on total count."""
    app = _fixture_app()
    default_raw = _text(_read(app, "legal://laws"))
    default_page = json.loads(default_raw)
    total_from_default = default_page["total"]

    paged_raw = _text(_read(app, "legal://laws/page/0/500"))
    paged_page = json.loads(paged_raw)
    assert paged_page["total"] == total_from_default, (
        f"total mismatch: default={total_from_default} paged={paged_page['total']}"
    )
