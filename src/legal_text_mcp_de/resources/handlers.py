# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Resource handlers for legal:// URIs.

This module is the registration entry point. All URI handlers for the
legal:// namespace are registered inside register_resources().
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime
from legal_text_mcp_de.resources.markdown_render import render_law, render_norm


def register_resources(app: FastMCP, runtime: LegalTextRuntime) -> None:
    """Register all legal:// MCP resources on the given FastMCP app."""

    # ------------------------------------------------------------------
    # B3: legal://laws — list of all laws as JSON
    # ------------------------------------------------------------------

    @app.resource("legal://laws")
    def list_laws() -> str:
        """All laws in the corpus as JSON."""
        try:
            data = runtime.list_laws()
        except Exception as exc:
            data = {"error": str(exc)}
        return json.dumps(data, indent=2, ensure_ascii=False)

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

    @app.resource("legal://corpus/manifest")
    def corpus_manifest() -> str:
        """Bundle manifest as JSON (coverage + provenance + retrieval timestamps)."""
        try:
            coverage = runtime.get_corpus_coverage()
        except Exception as exc:  # pragma: no cover — surface raw error to client
            coverage = {"error": str(exc)}
        return json.dumps(coverage, indent=2, ensure_ascii=False)
