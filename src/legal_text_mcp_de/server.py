# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""FastMCP entry point for legal-text-mcp-de.

The 9 v1 tools live in `tools.v1_tools`. New v2 capabilities (Resources,
Prompts, smart tools) plug in similarly via their own modules.
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from legal_text_mcp_de.config import settings
from legal_text_mcp_de.corpus.loader import BundleLoadError, load_corpus_bundle
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime
from legal_text_mcp_de.prompts import register_prompts
from legal_text_mcp_de.resources import register_resources
from legal_text_mcp_de.tools import register_research_topic, register_v1_tools


def _resolve_dataset_path() -> Path | None:
    """Return a usable corpus path, auto-downloading from GHCR if needed.

    Resolution order:
    1. ``settings.dataset_path`` if set → use it.
    2. If auto-download disabled, return None (or raise if strict).
    3. Otherwise call ``load_corpus_bundle`` which handles local cache
       first, then OCI download with optional cosign verification.
    """
    if settings.dataset_path:
        return Path(settings.dataset_path)
    if not settings.corpus_auto_download:
        if settings.strict_dataset or settings.strict_startup:
            raise BundleLoadError("DATASET_PATH not set and corpus_auto_download disabled")
        return None
    loaded = load_corpus_bundle(
        local_path=None,
        auto_download=True,
        version=settings.corpus_version,
        cert_identity=settings.corpus_cert_identity,
        verify_signature=settings.corpus_cert_identity is not None,
    )
    return loaded.bundle_path


def create_mcp_app(runtime: LegalTextRuntime | None = None) -> FastMCP:
    """Build the FastMCP app with all registrations."""
    runtime = runtime or LegalTextRuntime.from_settings(settings, strict=False)
    app = FastMCP(
        "legal-text-mcp-de",
        stateless_http=True,
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
    )
    register_v1_tools(app, runtime)
    register_research_topic(app, runtime)
    register_resources(app, runtime)
    register_prompts(app)

    @app.custom_route("/health", methods=["GET"])  # type: ignore[untyped-decorator]
    async def _health(_request: Request) -> Response:
        """Liveness probe for the Dockerfile HEALTHCHECK and load balancers."""
        return JSONResponse({"status": "ok"})

    return app


mcp = create_mcp_app()


def main() -> None:
    """Entry point for the legal-text-mcp-de console script."""
    dataset_path = _resolve_dataset_path()
    if dataset_path is not None:
        settings.dataset_path = str(dataset_path)
    runtime = LegalTextRuntime.from_settings(settings, strict=settings.strict_startup)
    app = create_mcp_app(runtime)
    app.run(transport="streamable-http")


if __name__ == "__main__":
    main()
