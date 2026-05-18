# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""legal-text-mcp-de command-line interface (typer-based).

Bare invocation prints `--help` and exits 0. Use `legal-text-mcp-de serve`
to start the MCP server (previously the bare-invocation default).
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Annotated

import typer


def _resolve_version() -> str:
    try:
        return version("legal-text-mcp-de")
    except PackageNotFoundError:
        return "0.0.0+unknown"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(_resolve_version())
        raise typer.Exit(code=0)


app = typer.Typer(
    name="legal-text-mcp-de",
    add_completion=False,  # we ship our own `completion` subcommand later
    help="MCP-native German legal-text server with a shell CLI surface.",
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version_flag: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True),
    ] = None,
) -> None:
    """legal-text-mcp-de root callback.

    Handles `--version` eagerly and, when invoked without a subcommand,
    prints the help text and exits 0 (so bare invocation is non-fatal
    and discoverable).
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":
    main()
