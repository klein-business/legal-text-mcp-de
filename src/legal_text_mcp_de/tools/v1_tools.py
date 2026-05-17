# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""The 9 v1-compatible MCP tools, moved out of v1's server.py.

Each tool wraps a LegalTextRuntime method. LegalTextError is caught at this
boundary and converted to the structured error dict shape that v1 callers
expect.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from legal_text_mcp_de.legal_texts.errors import LegalTextError
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime


def _call(func: Callable[..., dict[str, Any]], *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        return func(*args, **kwargs)
    except LegalTextError as exc:
        return exc.to_dict()


def register_v1_tools(app: FastMCP, runtime: LegalTextRuntime) -> None:
    """Register all 9 v1 MCP tools on the given FastMCP app."""

    @app.tool()
    def list_laws(query: str | None = None) -> dict[str, Any]:
        """List supported laws, optionally filtered by law metadata."""
        return _call(runtime.list_laws, query)

    @app.tool()
    def get_law(code: str) -> dict[str, Any]:
        """Return law metadata and normalized norm summaries for a law code or alias."""
        return _call(runtime.get_law, code)

    @app.tool()
    def get_norm(code: str, norm: str) -> dict[str, Any]:
        """Return one structured norm by canonical norm path or simple norm shorthand."""
        return _call(runtime.get_norm, code, norm)

    @app.tool()
    def resolve_citation(
        code: str,
        unit: str,
        paragraph_or_article: str,
        child_unit: str | None = None,
        child_value: str | None = None,
        absatz: str | None = None,
        satz: str | None = None,
        nummer: str | None = None,
        buchstabe: str | None = None,
    ) -> dict[str, Any]:
        """Resolve a structured legal citation without free-form parsing."""
        return _call(
            runtime.resolve_citation,
            code=code,
            unit=unit,
            paragraph_or_article=paragraph_or_article,
            child_unit=child_unit,
            child_value=child_value,
            absatz=absatz,
            satz=satz,
            nummer=nummer,
            buchstabe=buchstabe,
        )

    @app.tool()
    def search_laws(query: str, codes: list[str] | None = None) -> dict[str, Any]:
        """Search normalized legal texts with optional law-code filters."""
        return _call(runtime.search_laws, query, codes)

    @app.tool()
    def get_source_metadata(code: str | None = None) -> dict[str, Any]:
        """Return source provenance for all laws or one law code/alias."""
        return _call(runtime.get_source_metadata, code)

    @app.tool()
    def get_corpus_coverage() -> dict[str, Any]:
        """Return generated package, manifest, limitation, and relationship coverage metadata."""
        return _call(runtime.get_corpus_coverage)

    @app.tool()
    def get_source_limitations(
        source_family: str | None = None,
        terminal_state: str | None = None,
        state_code: str | None = None,
        law_id: str | None = None,
    ) -> dict[str, Any]:
        """Return official-source limitations with optional metadata filters."""
        return _call(
            runtime.get_source_limitations,
            source_family,
            terminal_state,
            state_code,
            law_id,
        )

    @app.tool()
    def get_related_norms(code: str, norm: str) -> dict[str, Any]:
        """Return generated relationship metadata for one norm when package relationships exist."""
        return _call(runtime.get_related_norms, code, norm)
