# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Resource handlers for legal:// URIs.

This module is the registration entry point. All URI handlers for the
legal:// namespace are registered inside register_resources().
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime
from legal_text_mcp_de.resources.markdown_render import render_law, render_norm


def register_resources(app: FastMCP, runtime: LegalTextRuntime) -> None:
    """Register all legal:// MCP resources on the given FastMCP app."""

    # ------------------------------------------------------------------
    # B3 / B13: legal://laws — paginated list of laws as JSON
    #
    # FastMCP 1.27.x URI template variables map only to *path* components,
    # not query-string parameters.  Registering "legal://laws?cursor=..." is
    # not routable.  We therefore expose pagination through path components:
    #
    #   legal://laws               → page 1 (cursor=0, limit=50)  [default]
    #   legal://laws/page/{cursor}/{limit}  → explicit page
    # ------------------------------------------------------------------

    def _serve_laws_page(cursor: int, limit: int) -> str:
        """Return a JSON page from the laws list.

        Response shape::

            {
                "entries":     [...],   # law objects for this page
                "cursor":      N,       # requested cursor
                "limit":       M,       # effective limit (clamped 1–500)
                "next_cursor": N+M | null,
                "total":       T
            }
        """
        limit = max(1, min(limit, 500))
        try:
            data = runtime.list_laws(None)
        except Exception as exc:
            return json.dumps({"error": str(exc), "entries": [], "next_cursor": None}, ensure_ascii=False)
        entries = data.get("laws", data.get("entries", []))
        total = len(entries)
        page = entries[cursor : cursor + limit]
        next_cursor: int | None = cursor + limit if (cursor + limit) < total else None
        return json.dumps(
            {
                "entries": page,
                "cursor": cursor,
                "limit": limit,
                "next_cursor": next_cursor,
                "total": total,
            },
            indent=2,
            ensure_ascii=False,
        )

    @app.resource("legal://laws")
    def list_laws() -> str:
        """First page of laws (cursor=0, limit=50).

        Use ``legal://laws/page/{cursor}/{limit}`` for subsequent pages.
        """
        return _serve_laws_page(0, 50)

    @app.resource("legal://laws/page/{cursor}/{limit}")
    def list_laws_page(cursor: int, limit: int) -> str:
        """Paginated law list.  cursor is a zero-based integer offset; limit is page size (1–500)."""
        return _serve_laws_page(cursor, limit)

    # ------------------------------------------------------------------
    # B4: legal://laws/{code} — law header + norm index as Markdown
    # ------------------------------------------------------------------

    @app.resource("legal://laws/{code}")
    def read_law(code: str) -> str:
        """Law header + norm index as Markdown."""
        try:
            data = runtime.get_law(code)
        except Exception as exc:
            return f"# Error\n\nFailed to load law `{code}`: {exc}"
        return render_law(data)

    # ------------------------------------------------------------------
    # B5: legal://laws/{code}/full — full law text (all norms) as Markdown
    # ------------------------------------------------------------------

    @app.resource("legal://laws/{code}/full")
    def read_law_full(code: str) -> str:
        """Full law text — law header followed by each norm's full text."""
        try:
            law_data = runtime.get_law(code)
        except Exception as exc:
            return f"# Error\n\nFailed to load law `{code}`: {exc}"

        law = law_data.get("law", {})
        norms = law_data.get("norms", []) or []
        canonical_id = law.get("canonical_id", code)

        sections: list[str] = [render_law(law_data)]

        for norm_entry in norms:
            norm_id = norm_entry.get("norm_id", "")
            try:
                norm_data = runtime.get_norm(canonical_id, norm_id)
                sections.append(render_norm(norm_data))
            except Exception:
                display_id = norm_entry.get("display_id", norm_id)
                sections.append(f"## {display_id}\n\n*(Text nicht verfügbar)*")

        return "\n\n---\n\n".join(sections)

    # ------------------------------------------------------------------
    # B6: legal://laws/{code}/norms/{norm_id} — single norm as Markdown
    # ------------------------------------------------------------------

    @app.resource("legal://laws/{code}/norms/{norm_id}")
    def read_norm(code: str, norm_id: str) -> str:
        """Single norm as Markdown."""
        try:
            data = runtime.get_norm(code, norm_id)
        except Exception as exc:
            return f"# Error\n\nFailed to load norm `{norm_id}` of `{code}`: {exc}"
        return render_norm(data)

    # ------------------------------------------------------------------
    # B7: legal://laws/{code}/norms/{norm_id}/relationships — JSON
    # ------------------------------------------------------------------

    @app.resource("legal://laws/{code}/norms/{norm_id}/relationships")
    def read_norm_relationships(code: str, norm_id: str) -> str:
        """Related norms for a norm as JSON."""
        try:
            data = runtime.get_related_norms(code, norm_id)
        except Exception as exc:
            data = {"error": str(exc), "code": code, "norm_id": norm_id}
        return json.dumps(data, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # B8: legal://laws/{code}/source — source metadata as JSON
    # ------------------------------------------------------------------

    @app.resource("legal://laws/{code}/source")
    def read_law_source(code: str) -> str:
        """Source metadata for a law as JSON."""
        try:
            data = runtime.get_source_metadata(code)
        except Exception as exc:
            data = {"error": str(exc), "code": code}
        return json.dumps(data, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # B9: legal://corpus/coverage — per-law inventory as JSON
    # ------------------------------------------------------------------

    @app.resource("legal://corpus/coverage")
    def corpus_coverage() -> str:
        """Corpus coverage — per-law inventory, counts, and source families."""
        try:
            data = runtime.get_corpus_coverage()
        except Exception as exc:  # pragma: no cover
            data = {"error": str(exc)}
        return json.dumps(data, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # B10: legal://corpus/limitations — source limitations as JSON
    # ------------------------------------------------------------------

    @app.resource("legal://corpus/limitations")
    def corpus_limitations() -> str:
        """Known source limitations (gaps, caveats) for the corpus."""
        try:
            data = runtime.get_source_limitations()
        except Exception as exc:  # pragma: no cover
            data = {"error": str(exc)}
        return json.dumps(data, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # B11: legal://corpus/manifest — bundle-level manifest as JSON
    # ------------------------------------------------------------------

    @app.resource("legal://corpus/manifest")
    def corpus_manifest() -> str:
        """Bundle manifest: bundle-id, version, source-versions, retrieval timestamps.

        Focuses on bundle-level provenance fields. For the full per-law
        inventory see legal://corpus/coverage.
        """
        try:
            coverage = runtime.get_corpus_coverage()
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": str(exc)}, indent=2, ensure_ascii=False)

        # Extract bundle-level fields; fall back to coverage summary if the
        # generated package metadata is absent (fixture / dev mode).
        manifest: dict[str, Any] = {
            "bundle_id": coverage.get("package", {}).get("bundle_id"),
            "bundle_version": coverage.get("package", {}).get("version"),
            "generated_package_present": coverage.get("generated_package_present", False),
            "manifest": coverage.get("manifest", {}),
            "counts": coverage.get("counts", {}),
            "source_families": coverage.get("source_families", []),
            "retrieved_at": coverage.get("package", {}).get("retrieved_at"),
        }
        return json.dumps(manifest, indent=2, ensure_ascii=False)
