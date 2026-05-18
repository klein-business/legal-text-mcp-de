# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""corpus sub-Typer: pull (ORAS), verify (cosign), info."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from legal_text_mcp_de.cli._output import (
    EXIT_CORPUS,
    render_data,
    render_error,
)

corpus_app = typer.Typer(help="Corpus bundle management.")


def _cache_dir() -> Path:
    xdg = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(xdg) / "legal-text-mcp-de"


@corpus_app.command("pull")
def pull(
    ctx: typer.Context,
    version_: Annotated[str, typer.Option("--version")] = "latest",
) -> None:
    """ORAS-pull the signed corpus bundle from GHCR."""
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    cache = _cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    oci_ref = f"ghcr.io/klein-business/legal-text-mcp-de-corpus:{version_}"
    result = subprocess.run(
        ["oras", "pull", oci_ref, "--output", str(cache)],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        render_error(
            code="CORPUS_PULL_FAILED",
            message=f"oras pull failed (exit {result.returncode})",
            details={
                "oci_ref": oci_ref,
                "stderr": result.stderr.decode("utf-8", errors="replace"),
            },
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_CORPUS)
    render_data({"pulled": oci_ref, "cache_dir": str(cache)}, force_json=force_json)


@corpus_app.command("verify")
def verify(
    ctx: typer.Context,
    cert_identity: Annotated[
        str, typer.Option("--cert-identity")
    ] = "https://github.com/klein-business/legal-text-mcp-de/.github/workflows/release.yml@refs/tags/v2.0.1",
) -> None:
    """cosign verify the local corpus bundle's signature."""
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    cache = _cache_dir()
    bundle_glob = list(cache.glob("*.tar.zst"))
    if not bundle_glob:
        render_error(
            code="CORPUS_NOT_PRESENT",
            message=f"No .tar.zst bundle found in {cache}; run 'corpus pull' first.",
            details={"cache_dir": str(cache)},
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_CORPUS)
    bundle = bundle_glob[0]
    result = subprocess.run(
        [
            "cosign",
            "verify-blob",
            "--certificate-identity",
            cert_identity,
            "--certificate-oidc-issuer",
            "https://token.actions.githubusercontent.com",
            str(bundle),
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        render_error(
            code="CORPUS_VERIFY_FAILED",
            message=f"cosign verify-blob failed (exit {result.returncode})",
            details={
                "bundle": str(bundle),
                "stderr": result.stderr.decode("utf-8", errors="replace"),
            },
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_CORPUS)
    render_data(
        {"verified": str(bundle), "cert_identity": cert_identity},
        force_json=force_json,
    )


@corpus_app.command("info")
def info(ctx: typer.Context) -> None:
    """Show local corpus bundle metadata."""
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    cache = _cache_dir()
    bundles = sorted(cache.glob("*.tar.zst")) if cache.exists() else []
    payload = {
        "cache_dir": str(cache),
        "bundles": [{"path": str(b), "bytes": b.stat().st_size} for b in bundles],
        "count": len(bundles),
    }
    render_data(payload, force_json=force_json)
