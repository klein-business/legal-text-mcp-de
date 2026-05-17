# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Resource handlers for legal:// URIs.

This module is the registration entry point. Individual URI handlers will
be added in subsequent tasks (B3-B11). For now it registers one static
resource (legal://corpus/manifest) so the resources subsystem is wired up.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime


def register_resources(app: FastMCP, runtime: LegalTextRuntime) -> None:
    """Register all legal:// MCP resources on the given FastMCP app."""

    @app.resource("legal://corpus/manifest")
    def corpus_manifest() -> str:
        """Bundle manifest as JSON (coverage + provenance + retrieval timestamps)."""
        try:
            coverage = runtime.get_corpus_coverage()
        except Exception as exc:  # pragma: no cover — surface raw error to client
            coverage = {"error": str(exc)}
        return json.dumps(coverage, indent=2, ensure_ascii=False)
