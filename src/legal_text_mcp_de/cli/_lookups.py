# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Read-only lookup subcommands (1:1 mapping to the 9 v1 MCP tools)."""

from __future__ import annotations

from typing import Annotated

import typer

from legal_text_mcp_de.cli._output import EXIT_RUNTIME, render_data, render_error
from legal_text_mcp_de.cli._runtime import get_runtime_or_die
from legal_text_mcp_de.legal_texts.errors import LegalTextError


lookups_app = typer.Typer(help="Read-only lookups against the legal corpus.")


@lookups_app.command("laws")
def laws(
    ctx: typer.Context,
    query: Annotated[str | None, typer.Option("--query", "-q")] = None,
) -> None:
    """List laws; optional --query filter (substring match)."""
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    try:
        runtime = get_runtime_or_die()
        payload = runtime.list_laws(query)
    except LegalTextError as exc:
        render_error(
            code=exc.code,
            message=str(exc),
            details=getattr(exc, "details", None) or {},
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_RUNTIME)
    render_data(payload, force_json=force_json)
