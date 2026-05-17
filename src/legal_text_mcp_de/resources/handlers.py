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

    @app.resource("legal://corpus/manifest")
    def corpus_manifest() -> str:
        """Bundle manifest as JSON (coverage + provenance + retrieval timestamps)."""
        try:
            coverage = runtime.get_corpus_coverage()
        except Exception as exc:  # pragma: no cover — surface raw error to client
            coverage = {"error": str(exc)}
        return json.dumps(coverage, indent=2, ensure_ascii=False)
