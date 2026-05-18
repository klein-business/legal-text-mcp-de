# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""legal-text-mcp-de command-line interface (typer-based).

Bare invocation prints `--help`. Use `legal-text-mcp-de serve` to start
the MCP server (previously the bare-invocation default).
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Annotated

import typer

from legal_text_mcp_de.cli._corpus import corpus_app
from legal_text_mcp_de.cli._diagnostic import completion_app, diagnostic_app
from legal_text_mcp_de.cli._lookups import lookups_app
from legal_text_mcp_de.cli._research import research_app
from legal_text_mcp_de.cli._server import server_app


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
    add_completion=False,
    help="MCP-native German legal-text server with a shell CLI surface.",
    rich_markup_mode="rich",
    invoke_without_command=True,
)


@app.callback()
def _root(
    ctx: typer.Context,
    json_output: Annotated[bool, typer.Option("--json", help="Force JSON output.")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Suppress non-essential stderr.")] = False,
    debug: Annotated[bool, typer.Option("--debug", "-v", help="Verbose logging.")] = False,
    version_flag: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True),
    ] = None,
) -> None:
    """legal-text-mcp-de root callback."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output
    ctx.obj["quiet"] = quiet
    ctx.obj["debug"] = debug
    # Bare invocation: print help and exit 0 (matches Task 1's contract).
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)


# Register the lookups Typer's commands directly on the root (no `lookups` prefix).
for command_info in lookups_app.registered_commands:
    app.registered_commands.append(command_info)

for command_info in server_app.registered_commands:
    app.registered_commands.append(command_info)

for command_info in research_app.registered_commands:
    app.registered_commands.append(command_info)

# corpus is a sub-Typer (keeps its `corpus` prefix), not lifted onto root.
app.add_typer(corpus_app, name="corpus")

# Diagnostic commands (version, health) are lifted onto root; completion stays sub-Typer.
for command_info in diagnostic_app.registered_commands:
    app.registered_commands.append(command_info)
app.add_typer(completion_app, name="completion")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
