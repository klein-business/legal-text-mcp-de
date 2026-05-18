# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Server-lifecycle subcommands: serve (MCP) + http (FastAPI)."""

from __future__ import annotations

from typing import Annotated

import typer

from legal_text_mcp_de.config import settings
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime
from legal_text_mcp_de.server import create_mcp_app


server_app = typer.Typer(help="Server-lifecycle commands.")


def _run_mcp(*, host: str, port: int, dataset: str | None, strict: bool) -> None:
    """Indirection so tests can monkeypatch without touching mcp internals."""
    if dataset is not None:
        settings.dataset_path = dataset
    if host:
        settings.host = host
    if port:
        settings.port = port
    runtime = LegalTextRuntime.from_settings(settings, strict=strict)
    mcp = create_mcp_app(runtime)
    mcp.run(transport="streamable-http")


def _run_http(*, host: str, port: int, dataset: str | None) -> None:
    import uvicorn

    if dataset is not None:
        settings.dataset_path = dataset
    uvicorn.run(
        "legal_text_mcp_de.http_api:app",
        host=host,
        port=port,
        log_level="info",
    )


@server_app.command("serve")
def serve(
    host: Annotated[str, typer.Option("--host")] = "0.0.0.0",
    port: Annotated[int, typer.Option("--port")] = 8001,
    dataset: Annotated[str | None, typer.Option("--dataset")] = None,
    strict: Annotated[bool, typer.Option("--strict")] = True,
) -> None:
    """Start the MCP server (streamable HTTP transport)."""
    _run_mcp(host=host, port=port, dataset=dataset, strict=strict)


@server_app.command("http")
def http(
    host: Annotated[str, typer.Option("--host")] = "0.0.0.0",
    port: Annotated[int, typer.Option("--port")] = 8080,
    dataset: Annotated[str | None, typer.Option("--dataset")] = None,
) -> None:
    """Start the FastAPI HTTP API."""
    _run_http(host=host, port=port, dataset=dataset)
