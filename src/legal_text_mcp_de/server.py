# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from legal_text_mcp_de.config import settings
from legal_text_mcp_de.corpus.loader import BundleLoadError, load_corpus_bundle
from legal_text_mcp_de.legal_texts.errors import LegalTextError
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime


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


def _call(func, *args, **kwargs) -> dict[str, Any]:
    try:
        return func(*args, **kwargs)
    except LegalTextError as exc:
        return exc.to_dict()


def create_mcp_app(runtime: LegalTextRuntime | None = None) -> FastMCP:
    runtime = runtime or LegalTextRuntime.from_settings(settings, strict=False)
    app = FastMCP(
        "legal-text-mcp-de",
        stateless_http=True,
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
    )

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
