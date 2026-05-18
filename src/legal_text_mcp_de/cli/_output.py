# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""CLI output rendering — TTY-aware text vs JSON, exit-code mapping.

Conventions
-----------
* Success payloads go to **stdout** in both modes (text or JSON envelope).
* Error payloads go to **stderr** in text mode and to **stdout** in JSON
  mode (so callers can pipe ``stdout`` into ``jq`` without losing the
  error body).
* Every public renderer accepts ``stream=`` so unit tests can capture
  output without monkey-patching ``sys.stdout``/``sys.stderr``. The
  mode-detection (TTY vs piped) uses the same stream the data will be
  written to, so injecting a buffer in tests is symmetric for both
  ``render_data`` and ``render_error``.

Exit-code constants follow the spec in section 3 and the de-facto Unix
convention of reserving ``1`` for generic runtime failures and ``2`` for
usage errors; the remaining codes are project-specific.
"""

from __future__ import annotations

import json
import sys
from typing import IO, Any, Final

from rich.console import Console
from rich.table import Table

# Exit code constants (Unix convention; see spec section 3).
EXIT_SUCCESS: Final = 0
EXIT_RUNTIME: Final = 1
EXIT_USAGE: Final = 2
EXIT_SAMPLING: Final = 3
EXIT_CORPUS: Final = 4
EXIT_CONNECTIVITY: Final = 5
EXIT_INTERRUPT: Final = 130


def is_json_mode(*, force_json: bool, stream: IO[str] | None = None) -> bool:
    """Decide whether output should be JSON.

    Rules:

    * ``--json`` flag (``force_json=True``) always wins.
    * If the target stream is a TTY → text mode.
    * If the target stream is piped/redirected (no ``isatty()`` or it
      returns ``False``) → JSON mode (machine-friendly default).
    """
    if force_json:
        return True
    s = stream or sys.stdout
    isatty = getattr(s, "isatty", lambda: False)
    return not isatty()


def render_data(
    payload: Any,
    *,
    stream: IO[str] | None = None,
    force_json: bool = False,
    text_renderer: Any = None,
) -> None:
    """Write a success payload as text (TTY) or JSON envelope.

    Text mode calls ``text_renderer(payload, console)`` when provided;
    otherwise falls back to ``console.print(payload)``.
    """
    s = stream or sys.stdout
    if is_json_mode(force_json=force_json, stream=s):
        s.write(json.dumps({"data": payload, "error": None}, ensure_ascii=False))
        s.write("\n")
        return
    console = Console(file=s)
    if text_renderer is not None:
        text_renderer(payload, console)
    else:
        console.print(payload)


def render_error(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    stream: IO[str] | None = None,
    force_json: bool = False,
) -> None:
    """Write an error envelope (matches the #64 ErrorBody shape).

    * JSON mode → envelope written to ``stream`` (default ``sys.stdout``).
    * Text mode → human-readable error written to ``stream`` (default
      ``sys.stderr``), so it does not collide with piped stdout payloads.

    Mode detection uses the same stream the data will be written to —
    symmetric with :func:`render_data` so unit tests can inject a buffer
    and exercise both code paths without monkey-patching ``sys.stdout``.
    """
    # JSON envelope goes to stdout by default but honours ``stream=`` for tests.
    json_stream = stream or sys.stdout
    if is_json_mode(force_json=force_json, stream=json_stream):
        payload = {
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
        }
        json_stream.write(json.dumps(payload, ensure_ascii=False))
        json_stream.write("\n")
        return
    # Text errors go to stderr by default but honour ``stream=`` too.
    err_stream = stream or sys.stderr
    console = Console(file=err_stream, stderr=err_stream is sys.stderr)
    console.print(f"[red]error[/red] [{code}] {message}")
    if details:
        console.print(details)


def render_table(
    rows: list[dict[str, Any]],
    *,
    columns: list[str],
    title: str | None = None,
    console: Console | None = None,
) -> None:
    """Render a list of dicts as a Rich table (text mode helper)."""
    c = console or Console()
    table = Table(title=title, show_header=True, header_style="bold")
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*(str(row.get(col, "")) for col in columns))
    c.print(table)
