# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""research subcommand — research_topic smart tool via the CLI."""

from __future__ import annotations

import asyncio
from typing import Annotated, Any, Coroutine, TypeVar

import typer

from legal_text_mcp_de.cli._output import (
    EXIT_RUNTIME,
    EXIT_SAMPLING,
    render_data,
    render_error,
)
from legal_text_mcp_de.cli._runtime import get_runtime_or_die
from legal_text_mcp_de.legal_texts.errors import LegalTextError
from legal_text_mcp_de.sampling.errors import SamplingError
from legal_text_mcp_de.tools.research_topic import _run_research


research_app = typer.Typer(help="Smart-tool subcommands.")

_T = TypeVar("_T")


def _run_async(coro: Coroutine[Any, Any, _T]) -> _T:
    """Run *coro* without leaving the main thread without an event loop.

    ``asyncio.run`` closes the loop and clears the thread-local loop, which
    breaks legacy ``asyncio.get_event_loop()`` callers downstream (notably
    ``tests/test_resources``). Wrapping the call so we restore a fresh
    default loop afterwards keeps the public behaviour intact while
    preventing test-ordering flakiness.
    """
    try:
        return asyncio.run(coro)
    finally:
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
        except RuntimeError:
            pass


@research_app.command("research")
def research(
    ctx: typer.Context,
    topic: Annotated[str, typer.Argument(help="Research topic in German.")],
    max_candidates: Annotated[int, typer.Option("--max-candidates")] = 20,
    detail: Annotated[str, typer.Option("--detail", help="brief|full")] = "full",
) -> None:
    """Multi-step legal research with LLM-assisted ranking + synthesis.

    Without ANTHROPIC_API_KEY: degrades gracefully to a ranked-search
    fallback (exit 0). Sampling timeouts or schema violations exit 3.
    """
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    try:
        runtime = get_runtime_or_die()
        report = _run_async(_run_research(runtime, topic, max_candidates, detail, ctx=None))
        render_data(report.model_dump(), force_json=force_json)
    except SamplingError as exc:
        render_error(
            code="SAMPLING_FAILED",
            message=str(exc),
            details={"type": type(exc).__name__},
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_SAMPLING)
    except LegalTextError as exc:
        render_error(
            code=exc.code,
            message=str(exc),
            details=getattr(exc, "details", None) or {},
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_RUNTIME)
