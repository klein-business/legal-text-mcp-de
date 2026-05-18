# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Diagnostic subcommands: health, version, completion sub-Typer."""

from __future__ import annotations

import platform
from importlib.metadata import PackageNotFoundError, version as pkg_version
from typing import Annotated

import httpx
import typer
from typer import completion as _typer_completion

from legal_text_mcp_de.cli._output import (
    EXIT_CONNECTIVITY,
    render_data,
    render_error,
)


diagnostic_app = typer.Typer(help="Diagnostic / ops subcommands.")
completion_app = typer.Typer(help="Shell completion install / show.")


@diagnostic_app.command("version")
def version_cmd(ctx: typer.Context) -> None:
    """Print version + Python + platform."""
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    try:
        v = pkg_version("legal-text-mcp-de")
    except PackageNotFoundError:
        v = "0.0.0+unknown"
    payload = {
        "version": v,
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    render_data(payload, force_json=force_json)


@diagnostic_app.command("health")
def health(
    ctx: typer.Context,
    url: Annotated[str, typer.Option("--url")] = "http://localhost:8001/health",
) -> None:
    """HTTP GET /health on a running server."""
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    try:
        resp = httpx.get(url, timeout=5.0)
    except httpx.HTTPError as exc:
        render_error(
            code="HEALTH_UNREACHABLE",
            message=f"GET {url} failed: {exc}",
            details={"url": url, "error_type": type(exc).__name__},
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_CONNECTIVITY)
    if resp.status_code != 200:
        render_error(
            code="HEALTH_NON_OK",
            message=f"GET {url} returned HTTP {resp.status_code}",
            details={"url": url, "status_code": resp.status_code},
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_CONNECTIVITY)
    render_data(
        {"url": url, "status_code": 200, "body": resp.json()},
        force_json=force_json,
    )


@completion_app.command("show")
def completion_show(shell: Annotated[str, typer.Argument()]) -> None:
    """Print the shell-completion script to stdout.

    Uses typer's own ``get_completion_script`` API rather than re-executing
    the CLI with the magic env-var, because the root Typer is constructed
    with ``add_completion=False`` (which suppresses the env-var handshake).
    """
    if shell not in {"bash", "zsh", "fish"}:
        typer.echo(f"unsupported shell: {shell}", err=True)
        raise typer.Exit(code=2)
    # typer.completion ships incomplete public stubs in 0.25.x; the function
    # is exported and callable at runtime, but mypy strict cannot see it.
    script = _typer_completion.get_completion_script(  # type: ignore[attr-defined]
        prog_name="legal-text-mcp-de",
        complete_var="_LEGAL_TEXT_MCP_DE_COMPLETE",
        shell=shell,
    )
    typer.echo(script)


@completion_app.command("install")
def completion_install(shell: Annotated[str, typer.Argument()]) -> None:
    """Print install instructions (does not write to RC files unattended)."""
    if shell not in {"bash", "zsh", "fish"}:
        typer.echo(f"unsupported shell: {shell}", err=True)
        raise typer.Exit(code=2)
    instructions = {
        "bash": "echo 'eval \"$(legal-text-mcp-de completion show bash)\"' >> ~/.bashrc",
        "zsh": "echo 'eval \"$(legal-text-mcp-de completion show zsh)\"' >> ~/.zshrc",
        "fish": "legal-text-mcp-de completion show fish > ~/.config/fish/completions/legal-text-mcp-de.fish",
    }
    typer.echo(instructions[shell])
