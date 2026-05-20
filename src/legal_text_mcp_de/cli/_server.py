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


def _run_mcp(*, host: str | None, port: int | None, dataset: str | None, strict: bool) -> None:
    """Indirection so tests can monkeypatch without touching mcp internals.

    Each flag is only applied when explicitly given on the command line.
    When omitted, the values from ``settings`` (which read HOST/PORT/
    DATASET_PATH from the environment) win. This preserves the v2.0
    behaviour where env-driven config Just Worked.
    """
    if dataset is not None:
        settings.dataset_path = dataset
    if host is not None:
        settings.host = host
    if port is not None:
        settings.port = port
    runtime = LegalTextRuntime.from_settings(settings, strict=strict)
    mcp = create_mcp_app(runtime)
    mcp.run(transport="streamable-http")


def _run_http(*, host: str | None, port: int | None, dataset: str | None) -> None:
    """Indirection for `http` subcommand.

    Like _run_mcp, flags only apply when explicitly given; otherwise we
    fall back to the env-driven settings (HOST/PORT/DATASET_PATH) so
    operators who configure via environment don't need to repeat the
    values on the command line.
    """
    import uvicorn

    if dataset is not None:
        settings.dataset_path = dataset
    effective_host = host if host is not None else settings.host
    effective_port = port if port is not None else settings.port
    uvicorn.run(
        "legal_text_mcp_de.http_api:app",
        host=effective_host,
        port=effective_port,
        log_level="info",
    )


@server_app.command("serve")
def serve(
    host: Annotated[str | None, typer.Option("--host", help="Bind host (default from HOST env or 0.0.0.0).")] = None,
    port: Annotated[int | None, typer.Option("--port", help="Bind port (default from PORT env or 8001).")] = None,
    dataset: Annotated[str | None, typer.Option("--dataset")] = None,
    strict: Annotated[bool, typer.Option("--strict")] = True,
) -> None:
    """Start the MCP server (streamable HTTP transport)."""
    _run_mcp(host=host, port=port, dataset=dataset, strict=strict)


@server_app.command("http")
def http(
    host: Annotated[str | None, typer.Option("--host", help="Bind host (default from HOST env or 0.0.0.0).")] = None,
    port: Annotated[int | None, typer.Option("--port", help="Bind port (default from PORT env or 8001).")] = None,
    dataset: Annotated[str | None, typer.Option("--dataset")] = None,
) -> None:
    """Start the FastAPI HTTP API."""
    _run_http(host=host, port=port, dataset=dataset)
