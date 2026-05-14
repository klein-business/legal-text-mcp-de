from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError:
    # When tests import this file as top-level `server` with PYTHONPATH=mcp,
    # the local mcp/ directory can shadow the installed `mcp` package.
    import importlib
    import sys

    local_dir = Path(__file__).resolve().parent
    local_parent = local_dir.parent
    original_path = list(sys.path)
    sys.modules.pop("mcp", None)
    sys.modules.pop("mcp.server", None)
    sys.path = [
        path
        for path in sys.path
        if path
        and Path(path).resolve() not in {local_dir, local_parent}
    ]
    FastMCP = importlib.import_module("mcp.server.fastmcp").FastMCP
    sys.path = original_path

from config import settings
from legal_texts.errors import LegalTextError, as_error_dict
from legal_texts.runtime import LegalTextRuntime


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

    return app


mcp = create_mcp_app()


if __name__ == "__main__":
    runtime = LegalTextRuntime.from_settings(settings, strict=settings.strict_startup)
    mcp = create_mcp_app(runtime)
    mcp.run(transport="streamable-http")
