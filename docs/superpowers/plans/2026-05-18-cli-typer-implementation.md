# CLI (typer) v2.1.0 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a `typer`-based CLI as the new `legal-text-mcp-de` console entry point. 14 subcommands covering every MCP tool + server lifecycle + corpus management + diagnostics. Bare invocation prints `--help`; explicit `serve` starts the MCP server. Release as v2.1.0 (Minor, no Major bump because the CLI form is outside the v1.0.0 stability contract).

**Architecture:** Thin CLI shell (`src/legal_text_mcp_de/cli/`) over the existing `LegalTextRuntime` (already shared between the MCP server and the FastAPI HTTP API). `typer` provides the subcommand graph; `_output.py` handles smart TTY-vs-pipe rendering; JSON output reuses the existing `legal_text_mcp_de.http_models.*` Pydantic schemas — this gives a free CLI-vs-HTTP contract check at test time.

**Tech Stack:** Python 3.12 / 3.13, `typer` (already transitive via `mcp[cli]==1.27.1`, promoted to direct dep), `rich` (already pulled by typer), `pydantic v2`, `httpx`, `pytest` + `typer.testing.CliRunner`. No new external runtime dependencies.

**Spec:** [docs/superpowers/specs/2026-05-18-cli-typer-design.md](../specs/2026-05-18-cli-typer-design.md)

---

## File structure

**Created:**

| Path | Responsibility |
|---|---|
| `src/legal_text_mcp_de/cli/__init__.py` | Root Typer app, global flags (`--json`, `--quiet`, `--debug`, `--version`), `main()` entry, sub-Typer registration |
| `src/legal_text_mcp_de/cli/_output.py` | `is_json_mode()`, `render_data(payload, model)`, `render_error(exc, exit_code)`, exit-code constants |
| `src/legal_text_mcp_de/cli/_runtime.py` | `get_runtime_or_die()` — lazy `LegalTextRuntime` loader with cached singleton |
| `src/legal_text_mcp_de/cli/_lookups.py` | 9 read-only subcommands: `laws`, `law`, `norm`, `cite`, `search`, `meta`, `coverage`, `limitations`, `related` |
| `src/legal_text_mcp_de/cli/_server.py` | `serve` (MCP), `http` (FastAPI) |
| `src/legal_text_mcp_de/cli/_research.py` | `research` (research_topic smart tool) |
| `src/legal_text_mcp_de/cli/_corpus.py` | `corpus` sub-Typer: `pull`, `verify`, `info` |
| `src/legal_text_mcp_de/cli/_diagnostic.py` | `health`, `version`, `completion` sub-Typer |
| `tests/test_cli/__init__.py` | Empty marker |
| `tests/test_cli/test_main.py` | bare invocation → help, `--version`, unknown subcommand → exit 2 |
| `tests/test_cli/test_output.py` | TTY/JSON detection, error → exit code, formatters |
| `tests/test_cli/test_runtime.py` | lazy loader, env-var resolution, dataset error handling |
| `tests/test_cli/test_lookups.py` | one happy + one error per lookup (text + `--json` for happy) |
| `tests/test_cli/test_server.py` | flag parsing only; `mcp.run` mocked |
| `tests/test_cli/test_research.py` | `MockSamplingClient` happy + no-key degradation |
| `tests/test_cli/test_corpus.py` | subprocess mocked for `oras` / `cosign` |
| `tests/test_cli/test_diagnostic.py` | httpx mocked for `health`; `version` shape; `completion` stdout |
| `docs/cli/index.md` | Curated CLI reference (typer help rendered) |

**Modified:**

| Path | Change |
|---|---|
| `pyproject.toml` | Add `typer>=0.20,<1` to `[project] dependencies`; repoint `[project.scripts] legal-text-mcp-de` to `legal_text_mcp_de.cli:main`; bump `version` to `2.1.0` (Task 22) |
| `.release-please-manifest.json` | `2.0.1` → `2.1.0` (Task 22) |
| `CHANGELOG.md` | New `## [2.1.0]` block (Task 21) |
| `README.md` | Bare invocations → `serve`; new "CLI" section; install-mode tags bumped to `2.1.0` (Task 20) |
| `docs/quickstart/{claude-desktop,cursor,uvx,docker,stdio}.md` | All `legal-text-mcp-de` → `legal-text-mcp-de serve` (Task 20) |
| `docs/api/index.md` | New `legal-text-mcp-de http` example alongside `uvicorn …` (Task 20) |
| `docs/operations/production-deployment.md` | Docker `CMD` with `serve`; tag bumped (Task 20) |
| `docs/operations/versioning.md` | New paragraph: CLI is outside the v1.0.0 stability contract (Task 21) |
| `docs/operations/migration-v1-v2.md` | New "v2.0 → v2.1 (CLI introduction)" section (Task 21) |
| `deployment/Dockerfile.hosted` | `CMD ["legal-text-mcp-de", "serve"]`; image bumped (Task 20) |
| `deployment/deploy.sh` | Example tag bumped (Task 20) |
| `Justfile` | New targets: `cli-help`, `search`, `norm`, `law` (Task 20) |
| `mkdocs.yml` | New top-level "CLI" nav entry (Task 20) |
| `scripts/verify_e2e.py` | Append 2 CLI smoke tests (Task 19) |

**Not touched:** `src/legal_text_mcp_de/{config,http_api,http_models,tools/*,resources/*,prompts/*,sampling/*,legal_texts/*}`, `tests/test_v1_compat.py`.

---

## Task ordering rationale

Bottom-up: foundation (`_output`, `_runtime`) before consumers (`_lookups`, `_server`, …). Each subcommand is a self-contained TDD cycle. Migration (docs + Docker + version bump) goes last so it does not block CI until the CLI itself is green. The `serve` subcommand swap (Task 13) is the breaking-change moment — explicitly isolated.

---

## Task 1: CLI package skeleton + typer dep + first failing test

**Files:**
- Create: `src/legal_text_mcp_de/cli/__init__.py`
- Create: `tests/test_cli/__init__.py`
- Create: `tests/test_cli/test_main.py`
- Modify: `pyproject.toml` (add typer dep, do **not** repoint script yet — that's Task 13)

- [ ] **Step 1: Write the failing test**

`tests/test_cli/test_main.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Smoke tests for the CLI root app."""

from __future__ import annotations

from typer.testing import CliRunner

from legal_text_mcp_de.cli import app


def test_bare_invocation_prints_help_and_exits_zero():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout


def test_unknown_subcommand_exits_two():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["bogus-command"])
    assert result.exit_code == 2


def test_version_flag_prints_version_and_exits_zero():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "2." in result.stdout  # any 2.x version
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --group dev pytest tests/test_cli/test_main.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'legal_text_mcp_de.cli'`

- [ ] **Step 3: Create the minimal Typer app**

`src/legal_text_mcp_de/cli/__init__.py`:

```python
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
    no_args_is_help=True,
    add_completion=False,  # we ship our own `completion` subcommand later
    help="MCP-native German legal-text server with a shell CLI surface.",
    rich_markup_mode="rich",
)


@app.callback()
def _root(
    version_flag: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True),
    ] = None,
) -> None:
    """legal-text-mcp-de root callback (handles --version)."""


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":
    main()
```

`tests/test_cli/__init__.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
```

- [ ] **Step 4: Add typer as a direct dependency**

Edit `pyproject.toml`. Find the `dependencies = [...]` block under `[project]`. Append `"typer>=0.20,<1",` so it reads:

```toml
dependencies = [
    "mcp[cli]==1.27.1",
    "rapidfuzz",
    "pydantic-settings",
    "fastapi",
    "uvicorn",
    "typer>=0.20,<1",
]
```

Run: `uv lock` (regenerates `uv.lock`).
Expected: `Resolved 136 packages` (or similar; no errors).

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run --group dev pytest tests/test_cli/test_main.py -v`
Expected: PASS 3/3 tests.

- [ ] **Step 6: Commit**

```bash
git add src/legal_text_mcp_de/cli/__init__.py tests/test_cli/__init__.py tests/test_cli/test_main.py pyproject.toml uv.lock
git commit -s -S -m "feat(cli): typer skeleton + --version + --help test fixture"
```

---

## Task 2: `_output.py` — TTY detection + JSON envelope

**Files:**
- Create: `src/legal_text_mcp_de/cli/_output.py`
- Create: `tests/test_cli/test_output.py`

- [ ] **Step 1: Write the failing test**

`tests/test_cli/test_output.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_output.py — TTY detection, JSON envelope, error rendering."""

from __future__ import annotations

import io
import json

from legal_text_mcp_de.cli._output import (
    EXIT_CONNECTIVITY,
    EXIT_CORPUS,
    EXIT_RUNTIME,
    EXIT_SAMPLING,
    EXIT_SUCCESS,
    EXIT_USAGE,
    is_json_mode,
    render_data,
    render_error,
)


def test_is_json_mode_explicit_flag_wins():
    assert is_json_mode(force_json=True, stream=io.StringIO()) is True


def test_is_json_mode_pipe_defaults_to_json():
    # StringIO has no isatty() returning True
    assert is_json_mode(force_json=False, stream=io.StringIO()) is True


def test_is_json_mode_tty_defaults_to_text():
    fake_tty = io.StringIO()
    fake_tty.isatty = lambda: True  # type: ignore[method-assign]
    assert is_json_mode(force_json=False, stream=fake_tty) is False


def test_render_data_json_envelope_shape():
    buf = io.StringIO()
    render_data({"law": {"canonical_id": "bgb"}}, stream=buf, force_json=True)
    payload = json.loads(buf.getvalue())
    assert payload == {"data": {"law": {"canonical_id": "bgb"}}, "error": None}


def test_render_error_json_envelope_shape():
    buf = io.StringIO()
    render_error(
        code="NORM_NOT_FOUND",
        message="Norm '§ 999' not found",
        details={"code": "BGB", "norm": "§ 999"},
        stream=buf,
        force_json=True,
    )
    payload = json.loads(buf.getvalue())
    assert payload == {
        "data": None,
        "error": {
            "code": "NORM_NOT_FOUND",
            "message": "Norm '§ 999' not found",
            "details": {"code": "BGB", "norm": "§ 999"},
        },
    }


def test_exit_code_constants_are_unix_conventional():
    assert EXIT_SUCCESS == 0
    assert EXIT_RUNTIME == 1
    assert EXIT_USAGE == 2
    assert EXIT_SAMPLING == 3
    assert EXIT_CORPUS == 4
    assert EXIT_CONNECTIVITY == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --group dev pytest tests/test_cli/test_output.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'legal_text_mcp_de.cli._output'`

- [ ] **Step 3: Implement `_output.py`**

`src/legal_text_mcp_de/cli/_output.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""CLI output rendering — TTY-aware text vs JSON, exit-code mapping."""

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
    - --json flag → always JSON
    - stdout is a TTY → text
    - stdout is piped / redirected → JSON
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

    Text mode uses `text_renderer(payload, console)` when provided;
    otherwise falls back to a minimal repr.
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
    """Write an error envelope (matches the #64 ErrorBody shape)."""
    s = stream or sys.stderr
    if is_json_mode(force_json=force_json, stream=sys.stdout):
        payload = {
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False))
        sys.stdout.write("\n")
        return
    console = Console(file=s, stderr=True)
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
    """Render a list of dicts as a Rich table (text mode)."""
    c = console or Console()
    table = Table(title=title, show_header=True, header_style="bold")
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*(str(row.get(col, "")) for col in columns))
    c.print(table)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --group dev pytest tests/test_cli/test_output.py -v`
Expected: PASS 6/6 tests.

- [ ] **Step 5: Commit**

```bash
git add src/legal_text_mcp_de/cli/_output.py tests/test_cli/test_output.py
git commit -s -S -m "feat(cli): _output module — TTY/JSON detection + envelope shape + exit codes"
```

---

## Task 3: `_runtime.py` — lazy `LegalTextRuntime` loader

**Files:**
- Create: `src/legal_text_mcp_de/cli/_runtime.py`
- Create: `tests/test_cli/test_runtime.py`

- [ ] **Step 1: Write the failing test**

`tests/test_cli/test_runtime.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_runtime.py — lazy LegalTextRuntime loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from legal_text_mcp_de.cli._runtime import get_runtime_or_die
from legal_text_mcp_de.legal_texts.errors import LegalTextError


FIXTURE = Path(__file__).parent.parent / "fixtures" / "normalized"


def test_get_runtime_or_die_with_valid_dataset(monkeypatch):
    monkeypatch.setenv("DATASET_PATH", str(FIXTURE))
    monkeypatch.setenv("STRICT_STARTUP", "true")
    runtime = get_runtime_or_die()
    assert runtime is not None
    assert runtime.dataset is not None


def test_get_runtime_or_die_caches_between_calls(monkeypatch):
    monkeypatch.setenv("DATASET_PATH", str(FIXTURE))
    monkeypatch.setenv("STRICT_STARTUP", "true")
    r1 = get_runtime_or_die()
    r2 = get_runtime_or_die()
    assert r1 is r2


def test_get_runtime_or_die_raises_on_missing_dataset(monkeypatch):
    monkeypatch.delenv("DATASET_PATH", raising=False)
    monkeypatch.setenv("STRICT_STARTUP", "true")
    # Force cache clear
    from legal_text_mcp_de.cli import _runtime
    _runtime._cached_runtime = None
    with pytest.raises(LegalTextError):
        get_runtime_or_die()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --group dev pytest tests/test_cli/test_runtime.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'legal_text_mcp_de.cli._runtime'`

- [ ] **Step 3: Implement `_runtime.py`**

`src/legal_text_mcp_de/cli/_runtime.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Lazy LegalTextRuntime loader for the CLI.

Each CLI subcommand resolves the runtime through `get_runtime_or_die()`
so that env-var changes (DATASET_PATH, STRICT_STARTUP) take effect on
every fresh process invocation. The runtime is cached per-process so
that multi-subcommand sessions (e.g. piped invocations) don't re-load
the dataset.
"""

from __future__ import annotations

from legal_text_mcp_de.config import Settings
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime


_cached_runtime: LegalTextRuntime | None = None


def get_runtime_or_die() -> LegalTextRuntime:
    """Return a ready LegalTextRuntime; raise LegalTextError otherwise."""
    global _cached_runtime
    if _cached_runtime is not None:
        return _cached_runtime
    settings = Settings()  # picks up env vars at call time
    runtime = LegalTextRuntime.from_settings(settings, strict=True)
    _cached_runtime = runtime
    return runtime


def reset_runtime_cache() -> None:
    """Test helper: clear the per-process runtime cache."""
    global _cached_runtime
    _cached_runtime = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --group dev pytest tests/test_cli/test_runtime.py -v`
Expected: PASS 3/3.

- [ ] **Step 5: Commit**

```bash
git add src/legal_text_mcp_de/cli/_runtime.py tests/test_cli/test_runtime.py
git commit -s -S -m "feat(cli): _runtime module — lazy LegalTextRuntime loader with per-process cache"
```

---

## Task 4: First lookup subcommand — `laws`

Establishes the lookup template that Tasks 5–12 follow.

**Files:**
- Create: `src/legal_text_mcp_de/cli/_lookups.py`
- Create: `tests/test_cli/test_lookups.py`
- Modify: `src/legal_text_mcp_de/cli/__init__.py` (register lookups Typer)

- [ ] **Step 1: Write the failing test**

`tests/test_cli/test_lookups.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_lookups.py — the 9 read-only commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from legal_text_mcp_de.cli import app
from legal_text_mcp_de.cli._runtime import reset_runtime_cache
from legal_text_mcp_de.http_models import LawListResponse


FIXTURE = Path(__file__).parent.parent / "fixtures" / "normalized"


@pytest.fixture(autouse=True)
def _isolate_runtime(monkeypatch):
    monkeypatch.setenv("DATASET_PATH", str(FIXTURE))
    monkeypatch.setenv("STRICT_STARTUP", "true")
    reset_runtime_cache()
    yield
    reset_runtime_cache()


def test_laws_text_output_shows_law_count():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["laws"])
    assert result.exit_code == 0
    assert "BGB" in result.stdout or "bgb" in result.stdout


def test_laws_json_output_validates_against_http_schema():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["--json", "laws"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["error"] is None
    LawListResponse.model_validate(payload["data"])  # contract check


def test_laws_with_query_filter():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["--json", "laws", "--query", "DSGVO"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    # DSGVO must appear in at least one canonical_id
    ids = [law["canonical_id"] for law in payload["data"]["laws"]]
    assert any("dsgvo" in cid.lower() for cid in ids)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --group dev pytest tests/test_cli/test_lookups.py::test_laws_text_output_shows_law_count -v`
Expected: FAIL — `laws` command not registered.

- [ ] **Step 3: Implement `_lookups.py` with `laws` only (others added in Tasks 5-12)**

`src/legal_text_mcp_de/cli/_lookups.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Read-only lookup subcommands (1:1 mapping to the 9 v1 MCP tools)."""

from __future__ import annotations

from typing import Annotated

import typer

from legal_text_mcp_de.cli._output import render_data, render_error, EXIT_RUNTIME
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
```

- [ ] **Step 4: Wire `lookups_app` and `--json` global flag into root**

Modify `src/legal_text_mcp_de/cli/__init__.py`. Replace the `_root` callback and add `lookups_app` registration. The complete file after this step:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""legal-text-mcp-de command-line interface (typer-based)."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Annotated

import typer

from legal_text_mcp_de.cli._lookups import lookups_app


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
    no_args_is_help=True,
    add_completion=False,
    help="MCP-native German legal-text server with a shell CLI surface.",
    rich_markup_mode="rich",
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


# Register the lookups Typer as commands directly on the root (no `lookups` prefix).
for command_info in lookups_app.registered_commands:
    app.registered_commands.append(command_info)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run --group dev pytest tests/test_cli/test_lookups.py::test_laws_text_output_shows_law_count tests/test_cli/test_lookups.py::test_laws_json_output_validates_against_http_schema tests/test_cli/test_lookups.py::test_laws_with_query_filter -v`
Expected: PASS 3/3.

- [ ] **Step 6: Commit**

```bash
git add src/legal_text_mcp_de/cli/_lookups.py src/legal_text_mcp_de/cli/__init__.py tests/test_cli/test_lookups.py
git commit -s -S -m "feat(cli): laws subcommand + lookup template + JSON contract check"
```

---

## Task 5: `law` subcommand

**Files:**
- Modify: `src/legal_text_mcp_de/cli/_lookups.py`
- Modify: `tests/test_cli/test_lookups.py`

- [ ] **Step 1: Append failing tests**

Append to `tests/test_cli/test_lookups.py`:

```python
def test_law_text_output_shows_canonical_id():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["law", "BGB"])
    assert result.exit_code == 0
    assert "BGB" in result.stdout or "bgb" in result.stdout


def test_law_unknown_code_returns_runtime_error_exit_1():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["law", "DOES_NOT_EXIST"])
    assert result.exit_code == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --group dev pytest tests/test_cli/test_lookups.py::test_law_text_output_shows_canonical_id tests/test_cli/test_lookups.py::test_law_unknown_code_returns_runtime_error_exit_1 -v`
Expected: FAIL — `law` command not registered.

- [ ] **Step 3: Append `law` command to `_lookups.py`**

Append to `src/legal_text_mcp_de/cli/_lookups.py`:

```python
@lookups_app.command("law")
def law(
    ctx: typer.Context,
    code: Annotated[str, typer.Argument(help="Law canonical ID or code (e.g. BGB, DSGVO).")],
    full: Annotated[bool, typer.Option("--full", help="Include full text for every norm.")] = False,
) -> None:
    """Show law metadata; --full also dumps every norm's text."""
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    try:
        runtime = get_runtime_or_die()
        payload = runtime.get_law(code)
    except LegalTextError as exc:
        render_error(
            code=exc.code,
            message=str(exc),
            details=getattr(exc, "details", None) or {},
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_RUNTIME)
    if not full and "law" in payload and "norms" in payload["law"]:
        # Strip norm bodies in summary mode
        payload["law"]["norms"] = [
            {k: v for k, v in n.items() if k != "text"} for n in payload["law"].get("norms", [])
        ]
    render_data(payload, force_json=force_json)
```

- [ ] **Step 4: Re-register `law` command on root in `__init__.py`**

Confirm the loop in `__init__.py` (Task 4 Step 4) still picks up every command from `lookups_app.registered_commands`. No change required — the loop already adds whatever is registered.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run --group dev pytest tests/test_cli/test_lookups.py -v`
Expected: PASS 5/5 (3 from Task 4 + 2 from this task).

- [ ] **Step 6: Commit**

```bash
git add src/legal_text_mcp_de/cli/_lookups.py tests/test_cli/test_lookups.py
git commit -s -S -m "feat(cli): law subcommand"
```

---

## Task 6: `norm` subcommand

**Files:**
- Modify: `src/legal_text_mcp_de/cli/_lookups.py`
- Modify: `tests/test_cli/test_lookups.py`

- [ ] **Step 1: Append failing tests**

Append to `tests/test_cli/test_lookups.py`:

```python
def test_norm_returns_norm_payload():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["--json", "norm", "BGB", "§ 355"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["norm"]["canonical_id"] == "bgb/par:355"


def test_norm_unknown_returns_runtime_error_exit_1():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["norm", "BGB", "§ 999999"])
    assert result.exit_code == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --group dev pytest tests/test_cli/test_lookups.py::test_norm_returns_norm_payload tests/test_cli/test_lookups.py::test_norm_unknown_returns_runtime_error_exit_1 -v`
Expected: FAIL — `norm` not registered.

- [ ] **Step 3: Append `norm` command**

Append to `src/legal_text_mcp_de/cli/_lookups.py`:

```python
@lookups_app.command("norm")
def norm(
    ctx: typer.Context,
    code: Annotated[str, typer.Argument(help="Law code (e.g. BGB).")],
    norm_id: Annotated[str, typer.Argument(help="Norm identifier (e.g. '§ 355' or 'par:355').")],
) -> None:
    """Fetch a single norm with full text + provenance."""
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    try:
        runtime = get_runtime_or_die()
        payload = runtime.get_norm(code, norm_id)
    except LegalTextError as exc:
        render_error(
            code=exc.code,
            message=str(exc),
            details=getattr(exc, "details", None) or {},
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_RUNTIME)
    render_data(payload, force_json=force_json)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --group dev pytest tests/test_cli/test_lookups.py -v`
Expected: PASS 7/7.

- [ ] **Step 5: Commit**

```bash
git add src/legal_text_mcp_de/cli/_lookups.py tests/test_cli/test_lookups.py
git commit -s -S -m "feat(cli): norm subcommand"
```

---

## Task 7: `cite` subcommand

**Files:**
- Modify: `src/legal_text_mcp_de/cli/_lookups.py`
- Modify: `tests/test_cli/test_lookups.py`

- [ ] **Step 1: Append failing tests**

Append to `tests/test_cli/test_lookups.py`:

```python
def test_cite_resolves_egbgb_art_246a_par_1():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        app,
        ["--json", "cite", "--code", "EGBGB", "--unit", "art",
         "--paragraph", "246a", "--child-unit", "par", "--child-value", "1"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["norm"]["canonical_id"] == "egbgb/art:246a/par:1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --group dev pytest tests/test_cli/test_lookups.py::test_cite_resolves_egbgb_art_246a_par_1 -v`
Expected: FAIL — `cite` not registered.

- [ ] **Step 3: Append `cite` command**

Append to `src/legal_text_mcp_de/cli/_lookups.py`:

```python
@lookups_app.command("cite")
def cite(
    ctx: typer.Context,
    code: Annotated[str, typer.Option("--code", help="Law code (e.g. BGB, EGBGB).")],
    unit: Annotated[str, typer.Option("--unit", help="Norm unit: par, art, abs, satz, …")],
    paragraph: Annotated[str, typer.Option("--paragraph", help="Paragraph or article number.")],
    child_unit: Annotated[str | None, typer.Option("--child-unit", help="Optional child unit.")] = None,
    child_value: Annotated[str | None, typer.Option("--child-value", help="Optional child value.")] = None,
) -> None:
    """Resolve a structured citation (e.g. '§ 433 Abs. 1 BGB' broken into parts)."""
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    try:
        runtime = get_runtime_or_die()
        kwargs = {"code": code, "unit": unit, "paragraph_or_article": paragraph}
        if child_unit:
            kwargs["child_unit"] = child_unit
        if child_value:
            kwargs["child_value"] = child_value
        payload = runtime.resolve_citation(**kwargs)
    except LegalTextError as exc:
        render_error(
            code=exc.code,
            message=str(exc),
            details=getattr(exc, "details", None) or {},
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_RUNTIME)
    render_data(payload, force_json=force_json)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --group dev pytest tests/test_cli/test_lookups.py::test_cite_resolves_egbgb_art_246a_par_1 -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/legal_text_mcp_de/cli/_lookups.py tests/test_cli/test_lookups.py
git commit -s -S -m "feat(cli): cite subcommand with structured citation flags"
```

---

## Task 8: `search` subcommand

**Files:**
- Modify: `src/legal_text_mcp_de/cli/_lookups.py`
- Modify: `tests/test_cli/test_lookups.py`

- [ ] **Step 1: Append failing tests**

```python
def test_search_with_code_filter():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["--json", "search", "Werbung", "--code", "UWG"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["codes"] == ["uwg_2004"]
    assert payload["data"]["results"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --group dev pytest tests/test_cli/test_lookups.py::test_search_with_code_filter -v`
Expected: FAIL.

- [ ] **Step 3: Append `search` command**

```python
@lookups_app.command("search")
def search(
    ctx: typer.Context,
    query: Annotated[str, typer.Argument(help="Full-text search query.")],
    code: Annotated[list[str] | None, typer.Option("--code", help="Restrict to one or more law codes (repeatable).")] = None,
    limit: Annotated[int, typer.Option("--limit", help="Maximum number of hits to return.")] = 50,
) -> None:
    """Full-text search across the corpus."""
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    try:
        runtime = get_runtime_or_die()
        payload = runtime.search_laws(query, code)
        # Apply --limit at CLI layer (runtime returns all)
        if "results" in payload:
            payload["results"] = payload["results"][:limit]
            payload["count"] = len(payload["results"])
    except LegalTextError as exc:
        render_error(
            code=exc.code,
            message=str(exc),
            details=getattr(exc, "details", None) or {},
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_RUNTIME)
    render_data(payload, force_json=force_json)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --group dev pytest tests/test_cli/test_lookups.py::test_search_with_code_filter -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/legal_text_mcp_de/cli/_lookups.py tests/test_cli/test_lookups.py
git commit -s -S -m "feat(cli): search subcommand with --code repeatable + --limit"
```

---

## Task 9: `meta` subcommand

**Files:**
- Modify: `src/legal_text_mcp_de/cli/_lookups.py`
- Modify: `tests/test_cli/test_lookups.py`

- [ ] **Step 1: Append failing test**

```python
def test_meta_for_dsgvo_includes_eur_lex_kind():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["--json", "meta", "DSGVO"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["sources"][0]["source"]["source_kind"] == "eur-lex-cellar"
```

- [ ] **Step 2: Run test — expect FAIL**

`uv run --group dev pytest tests/test_cli/test_lookups.py::test_meta_for_dsgvo_includes_eur_lex_kind -v`

- [ ] **Step 3: Append `meta` command**

```python
@lookups_app.command("meta")
def meta(
    ctx: typer.Context,
    code: Annotated[str, typer.Argument(help="Law code.")],
) -> None:
    """Show source metadata + provenance for a law."""
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    try:
        runtime = get_runtime_or_die()
        payload = runtime.get_source_metadata(code)
    except LegalTextError as exc:
        render_error(
            code=exc.code,
            message=str(exc),
            details=getattr(exc, "details", None) or {},
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_RUNTIME)
    render_data(payload, force_json=force_json)
```

- [ ] **Step 4: Run — expect PASS**

`uv run --group dev pytest tests/test_cli/test_lookups.py::test_meta_for_dsgvo_includes_eur_lex_kind -v`

- [ ] **Step 5: Commit**

```bash
git add src/legal_text_mcp_de/cli/_lookups.py tests/test_cli/test_lookups.py
git commit -s -S -m "feat(cli): meta subcommand"
```

---

## Task 10: `coverage` subcommand

**Files:**
- Modify: `src/legal_text_mcp_de/cli/_lookups.py`
- Modify: `tests/test_cli/test_lookups.py`

- [ ] **Step 1: Append failing test**

```python
def test_coverage_returns_counts():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["--json", "coverage"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "generated_package_present" in payload["data"]
```

- [ ] **Step 2: Run — expect FAIL**

`uv run --group dev pytest tests/test_cli/test_lookups.py::test_coverage_returns_counts -v`

- [ ] **Step 3: Append `coverage` command**

```python
@lookups_app.command("coverage")
def coverage(ctx: typer.Context) -> None:
    """Show corpus coverage statistics."""
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    try:
        runtime = get_runtime_or_die()
        payload = runtime.get_corpus_coverage()
    except LegalTextError as exc:
        render_error(
            code=exc.code,
            message=str(exc),
            details=getattr(exc, "details", None) or {},
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_RUNTIME)
    render_data(payload, force_json=force_json)
```

- [ ] **Step 4: Run — expect PASS**

`uv run --group dev pytest tests/test_cli/test_lookups.py::test_coverage_returns_counts -v`

- [ ] **Step 5: Commit**

```bash
git add src/legal_text_mcp_de/cli/_lookups.py tests/test_cli/test_lookups.py
git commit -s -S -m "feat(cli): coverage subcommand"
```

---

## Task 11: `limitations` subcommand

**Files:**
- Modify: `src/legal_text_mcp_de/cli/_lookups.py`
- Modify: `tests/test_cli/test_lookups.py`

- [ ] **Step 1: Append failing test**

```python
def test_limitations_returns_count_field():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["--json", "limitations"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "count" in payload["data"]
```

- [ ] **Step 2: Run — expect FAIL**

`uv run --group dev pytest tests/test_cli/test_lookups.py::test_limitations_returns_count_field -v`

- [ ] **Step 3: Append `limitations` command**

```python
@lookups_app.command("limitations")
def limitations(
    ctx: typer.Context,
    source_family: Annotated[str | None, typer.Option("--source-family")] = None,
    terminal_state: Annotated[str | None, typer.Option("--terminal-state")] = None,
    state_code: Annotated[str | None, typer.Option("--state-code")] = None,
    law_id: Annotated[str | None, typer.Option("--law-id")] = None,
) -> None:
    """List sources that did not produce a normalised entry."""
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    try:
        runtime = get_runtime_or_die()
        payload = runtime.get_source_limitations(
            source_family=source_family,
            terminal_state=terminal_state,
            state_code=state_code,
            law_id=law_id,
        )
    except LegalTextError as exc:
        render_error(
            code=exc.code,
            message=str(exc),
            details=getattr(exc, "details", None) or {},
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_RUNTIME)
    render_data(payload, force_json=force_json)
```

- [ ] **Step 4: Run — expect PASS**

`uv run --group dev pytest tests/test_cli/test_lookups.py::test_limitations_returns_count_field -v`

- [ ] **Step 5: Commit**

```bash
git add src/legal_text_mcp_de/cli/_lookups.py tests/test_cli/test_lookups.py
git commit -s -S -m "feat(cli): limitations subcommand with all four filter flags"
```

---

## Task 12: `related` subcommand

**Files:**
- Modify: `src/legal_text_mcp_de/cli/_lookups.py`
- Modify: `tests/test_cli/test_lookups.py`

- [ ] **Step 1: Append failing test**

```python
def test_related_returns_count_field_zero_or_more():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["--json", "related", "BGB", "§ 355"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "count" in payload["data"]
```

- [ ] **Step 2: Run — expect FAIL**

`uv run --group dev pytest tests/test_cli/test_lookups.py::test_related_returns_count_field_zero_or_more -v`

- [ ] **Step 3: Append `related` command**

```python
@lookups_app.command("related")
def related(
    ctx: typer.Context,
    code: Annotated[str, typer.Argument(help="Law code.")],
    norm_id: Annotated[str, typer.Argument(help="Norm identifier.")],
) -> None:
    """List relationships emanating from a norm."""
    force_json = bool(ctx.obj and ctx.obj.get("json"))
    try:
        runtime = get_runtime_or_die()
        payload = runtime.get_related_norms(code, norm_id)
    except LegalTextError as exc:
        render_error(
            code=exc.code,
            message=str(exc),
            details=getattr(exc, "details", None) or {},
            force_json=force_json,
        )
        raise typer.Exit(code=EXIT_RUNTIME)
    render_data(payload, force_json=force_json)
```

- [ ] **Step 4: Run full lookups test file — expect all PASS**

Run: `uv run --group dev pytest tests/test_cli/test_lookups.py -v`
Expected: PASS all 12 tests (3 from Task 4 + 1 per task 5-12 = +8 more, total 12 — wait, recompute: Task 4=3, Task 5=2, Task 6=2, Task 7=1, Task 8=1, Task 9=1, Task 10=1, Task 11=1, Task 12=1 → **13 tests total**).

- [ ] **Step 5: Commit**

```bash
git add src/legal_text_mcp_de/cli/_lookups.py tests/test_cli/test_lookups.py
git commit -s -S -m "feat(cli): related subcommand — all 9 v1-tool lookups now in CLI"
```

---

## Task 13: `serve` subcommand + console-script repoint (BREAKING)

This is the breaking-change moment. The old `legal-text-mcp-de` (no args) silently started the MCP server; from this commit on, bare invocation prints `--help`.

**Files:**
- Create: `src/legal_text_mcp_de/cli/_server.py`
- Create: `tests/test_cli/test_server.py`
- Modify: `pyproject.toml` (repoint `[project.scripts]`)
- Modify: `src/legal_text_mcp_de/cli/__init__.py` (register server subcommands)

- [ ] **Step 1: Write the failing test**

`tests/test_cli/test_server.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_server.py — flag parsing only, mcp.run() is mocked."""

from __future__ import annotations

from typer.testing import CliRunner

from legal_text_mcp_de.cli import app


def test_serve_runs_mcp_app(monkeypatch):
    invoked = {}

    def fake_run(transport: str) -> None:
        invoked["transport"] = transport

    # Patch the create_mcp_app().run reference used by serve
    import legal_text_mcp_de.cli._server as srv_mod
    monkeypatch.setattr(srv_mod, "_run_mcp", lambda **kw: invoked.update(kw))

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["serve", "--host", "127.0.0.1", "--port", "9999"])
    assert result.exit_code == 0
    assert invoked.get("host") == "127.0.0.1"
    assert invoked.get("port") == 9999
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run --group dev pytest tests/test_cli/test_server.py -v`
Expected: FAIL — `cli._server` does not exist.

- [ ] **Step 3: Implement `_server.py`**

`src/legal_text_mcp_de/cli/_server.py`:

```python
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
```

- [ ] **Step 4: Register on root in `__init__.py`**

Edit `src/legal_text_mcp_de/cli/__init__.py`. Add the import and the registration loop below the lookups loop:

```python
from legal_text_mcp_de.cli._server import server_app
...
for command_info in server_app.registered_commands:
    app.registered_commands.append(command_info)
```

- [ ] **Step 5: Repoint the console script in `pyproject.toml`**

Find `[project.scripts]` and change:

```toml
[project.scripts]
legal-text-mcp-de = "legal_text_mcp_de.cli:main"
```

(Previously pointed to `legal_text_mcp_de.server:main`.)

- [ ] **Step 6: Reinstall package so the script picks up the new entry point**

Run: `uv sync --all-groups --reinstall-package legal-text-mcp-de`
Expected: package re-installed, `legal-text-mcp-de --help` now prints the CLI Typer help.

- [ ] **Step 7: Run — expect PASS + smoke-check the binary**

Run: `uv run --group dev pytest tests/test_cli/test_server.py -v`
Expected: PASS.

Sanity-check: `uv run legal-text-mcp-de --help | head -5`
Expected: contains `Usage:`, lists subcommands including `serve`, `http`, `laws`, …

- [ ] **Step 8: Commit**

```bash
git add src/legal_text_mcp_de/cli/_server.py src/legal_text_mcp_de/cli/__init__.py pyproject.toml tests/test_cli/test_server.py
git commit -s -S -m "feat(cli)!: serve + http subcommands; repoint console script to cli:main

BREAKING: 'legal-text-mcp-de' (no args) now prints --help instead of
silently starting the MCP server. Use 'legal-text-mcp-de serve' to
start the MCP server explicitly. Container CMD, Claude Desktop configs,
and 'uvx legal-text-mcp-de' invocations must be updated to append
'serve'. Migration details ship in docs/operations/migration-v1-v2.md
under the v2.0 -> v2.1 section."
```

---

## Task 14: `research` subcommand (smart tool)

**Files:**
- Create: `src/legal_text_mcp_de/cli/_research.py`
- Create: `tests/test_cli/test_research.py`
- Modify: `src/legal_text_mcp_de/cli/__init__.py`

- [ ] **Step 1: Write the failing test**

`tests/test_cli/test_research.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_research.py — research smart tool."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from legal_text_mcp_de.cli import app
from legal_text_mcp_de.cli._runtime import reset_runtime_cache


FIXTURE = Path(__file__).parent.parent / "fixtures" / "normalized"


@pytest.fixture(autouse=True)
def _isolate_runtime(monkeypatch):
    monkeypatch.setenv("DATASET_PATH", str(FIXTURE))
    monkeypatch.setenv("STRICT_STARTUP", "true")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    reset_runtime_cache()
    yield
    reset_runtime_cache()


def test_research_without_api_key_returns_ranked_search_fallback_exit_zero():
    """No ANTHROPIC_API_KEY → soft degradation, exit 0 with ranked search hits."""
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["--json", "research", "Werbung"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    # The Phase-E _run_research path returns a ResearchReport; in
    # the no-key path the status is one of {no_matches, error, ok}
    # depending on the fixture corpus. Either way, error field must
    # be None on a soft degradation.
    assert payload["error"] is None
    assert "topic" in payload["data"]
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run --group dev pytest tests/test_cli/test_research.py -v`
Expected: FAIL — `research` not registered.

- [ ] **Step 3: Implement `_research.py`**

`src/legal_text_mcp_de/cli/_research.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""research subcommand — research_topic smart tool via the CLI."""

from __future__ import annotations

import asyncio
from typing import Annotated

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
        report = asyncio.run(
            _run_research(runtime, topic, max_candidates, detail, ctx=None)
        )
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
```

- [ ] **Step 4: Register on root**

Append to `src/legal_text_mcp_de/cli/__init__.py`:

```python
from legal_text_mcp_de.cli._research import research_app
...
for command_info in research_app.registered_commands:
    app.registered_commands.append(command_info)
```

- [ ] **Step 5: Run — expect PASS**

Run: `uv run --group dev pytest tests/test_cli/test_research.py -v`
Expected: PASS 1/1.

- [ ] **Step 6: Commit**

```bash
git add src/legal_text_mcp_de/cli/_research.py src/legal_text_mcp_de/cli/__init__.py tests/test_cli/test_research.py
git commit -s -S -m "feat(cli): research subcommand with sampling-failure exit code 3"
```

---

## Task 15: `corpus` sub-Typer — pull / verify / info

**Files:**
- Create: `src/legal_text_mcp_de/cli/_corpus.py`
- Create: `tests/test_cli/test_corpus.py`
- Modify: `src/legal_text_mcp_de/cli/__init__.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_cli/test_corpus.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_corpus.py — corpus pull / verify / info (subprocess mocked)."""

from __future__ import annotations

from typer.testing import CliRunner

from legal_text_mcp_de.cli import app


def test_corpus_pull_invokes_oras_with_version(monkeypatch):
    called = {}

    def fake_run(args, capture_output=False, check=False, **kw):
        called["args"] = args
        class _R:
            returncode = 0
            stdout = b""
            stderr = b""
        return _R()

    import legal_text_mcp_de.cli._corpus as cmod
    monkeypatch.setattr(cmod.subprocess, "run", fake_run)

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["corpus", "pull", "--version", "1.5.0"])
    assert result.exit_code == 0
    assert any("1.5.0" in str(part) for part in called["args"])


def test_corpus_verify_invokes_cosign(monkeypatch):
    called = {}

    def fake_run(args, capture_output=False, check=False, **kw):
        called["args"] = args
        class _R:
            returncode = 0
            stdout = b"Verified OK"
            stderr = b""
        return _R()

    import legal_text_mcp_de.cli._corpus as cmod
    monkeypatch.setattr(cmod.subprocess, "run", fake_run)

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["corpus", "verify"])
    assert result.exit_code == 0
    assert any("cosign" in str(part) for part in called["args"])


def test_corpus_info_returns_zero_when_cache_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["--json", "corpus", "info"])
    assert result.exit_code == 0
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run --group dev pytest tests/test_cli/test_corpus.py -v`
Expected: FAIL — `corpus` not registered.

- [ ] **Step 3: Implement `_corpus.py`**

`src/legal_text_mcp_de/cli/_corpus.py`:

```python
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
            details={"oci_ref": oci_ref, "stderr": result.stderr.decode("utf-8", errors="replace")},
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
            details={"bundle": str(bundle), "stderr": result.stderr.decode("utf-8", errors="replace")},
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
        "bundles": [
            {"path": str(b), "bytes": b.stat().st_size} for b in bundles
        ],
        "count": len(bundles),
    }
    render_data(payload, force_json=force_json)
```

- [ ] **Step 4: Register `corpus_app` on root**

Append to `src/legal_text_mcp_de/cli/__init__.py`:

```python
from legal_text_mcp_de.cli._corpus import corpus_app
...
app.add_typer(corpus_app, name="corpus")
```

(Note: `add_typer` keeps the `corpus` prefix, unlike the loops above.)

- [ ] **Step 5: Run — expect PASS**

Run: `uv run --group dev pytest tests/test_cli/test_corpus.py -v`
Expected: PASS 3/3.

- [ ] **Step 6: Commit**

```bash
git add src/legal_text_mcp_de/cli/_corpus.py src/legal_text_mcp_de/cli/__init__.py tests/test_cli/test_corpus.py
git commit -s -S -m "feat(cli): corpus sub-Typer (pull/verify/info) with subprocess-based oras + cosign"
```

---

## Task 16: `health`, `version`, `completion` — diagnostic subcommands

**Files:**
- Create: `src/legal_text_mcp_de/cli/_diagnostic.py`
- Create: `tests/test_cli/test_diagnostic.py`
- Modify: `src/legal_text_mcp_de/cli/__init__.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_cli/test_diagnostic.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_diagnostic.py — health, version, completion."""

from __future__ import annotations

import httpx
from typer.testing import CliRunner

from legal_text_mcp_de.cli import app


def test_version_subcommand_prints_2_x():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "2." in result.stdout


def test_health_returns_zero_when_endpoint_ok(monkeypatch):
    def fake_get(url, timeout=None):
        return httpx.Response(200, json={"status": "ok"})

    import legal_text_mcp_de.cli._diagnostic as dmod
    monkeypatch.setattr(dmod.httpx, "get", fake_get)

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["health"])
    assert result.exit_code == 0


def test_health_returns_five_when_endpoint_unreachable(monkeypatch):
    def fake_get(url, timeout=None):
        raise httpx.ConnectError("connection refused")

    import legal_text_mcp_de.cli._diagnostic as dmod
    monkeypatch.setattr(dmod.httpx, "get", fake_get)

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["health"])
    assert result.exit_code == 5


def test_completion_show_bash_prints_to_stdout():
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["completion", "show", "bash"])
    assert result.exit_code == 0
    assert "_LEGAL_TEXT_MCP_DE_COMPLETE" in result.stdout or "complete" in result.stdout.lower()
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run --group dev pytest tests/test_cli/test_diagnostic.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `_diagnostic.py`**

`src/legal_text_mcp_de/cli/_diagnostic.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Diagnostic subcommands: health, version, completion sub-Typer."""

from __future__ import annotations

import platform
import sys
from importlib.metadata import PackageNotFoundError, version as pkg_version
from typing import Annotated

import httpx
import typer

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
    render_data({"url": url, "status_code": 200, "body": resp.json()}, force_json=force_json)


@completion_app.command("show")
def completion_show(shell: Annotated[str, typer.Argument()]) -> None:
    """Print the shell-completion script to stdout."""
    if shell not in {"bash", "zsh", "fish"}:
        typer.echo(f"unsupported shell: {shell}", err=True)
        raise typer.Exit(code=2)
    # typer's own complete machinery emits the right script when the magic env-var is set
    import os, subprocess
    env = os.environ.copy()
    env[f"_LEGAL_TEXT_MCP_DE_COMPLETE"] = f"{shell}_source"
    result = subprocess.run(
        [sys.executable, "-m", "legal_text_mcp_de.cli"],
        env=env,
        capture_output=True,
    )
    sys.stdout.write(result.stdout.decode("utf-8", errors="replace"))


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
```

- [ ] **Step 4: Register on root**

Append to `src/legal_text_mcp_de/cli/__init__.py`:

```python
from legal_text_mcp_de.cli._diagnostic import diagnostic_app, completion_app
...
for command_info in diagnostic_app.registered_commands:
    app.registered_commands.append(command_info)
app.add_typer(completion_app, name="completion")
```

- [ ] **Step 5: Run — expect PASS**

Run: `uv run --group dev pytest tests/test_cli/test_diagnostic.py -v`
Expected: PASS 4/4.

- [ ] **Step 6: Commit**

```bash
git add src/legal_text_mcp_de/cli/_diagnostic.py src/legal_text_mcp_de/cli/__init__.py tests/test_cli/test_diagnostic.py
git commit -s -S -m "feat(cli): health + version + completion (show/install) subcommands"
```

---

## Task 17: Full CLI test suite must be green

- [ ] **Step 1: Run the entire test suite**

Run: `uv run --group dev --group prepare-data pytest`
Expected: PASS, total count = previous + ~25 new CLI tests (3 main + 6 output + 3 runtime + 13 lookups + 1 server + 1 research + 3 corpus + 4 diagnostic). 5 still-skipped tests carry over from before.

- [ ] **Step 2: Lint + format check**

Run:
```bash
uv run --group dev ruff check src/legal_text_mcp_de/cli tests/test_cli
uv run --group dev ruff format --check src/legal_text_mcp_de/cli tests/test_cli
```
Expected: clean.

- [ ] **Step 3: Coverage check for the CLI package**

Run: `uv run --group dev pytest tests/test_cli --cov=src/legal_text_mcp_de/cli --cov-report=term-missing`
Expected: ≥ 90 % statement coverage; if below, add tests covering the missing branches before continuing.

- [ ] **Step 4: Commit any tightening tests added in Step 3**

If you added tests in Step 3:
```bash
git add tests/test_cli/
git commit -s -S -m "test(cli): raise package coverage to >=90% statement"
```

If you added none, skip the commit.

---

## Task 18: `scripts/verify_e2e.py` smoke tests

**Files:**
- Modify: `scripts/verify_e2e.py`

- [ ] **Step 1: Read the existing file to find the right insertion point**

Open `scripts/verify_e2e.py`. Look at the bottom of `main()`. Add the CLI smoke section before the final success log line.

- [ ] **Step 2: Append smoke tests**

Add this function to `scripts/verify_e2e.py`:

```python
def smoke_cli_bare_invocation_prints_help() -> None:
    result = subprocess.run(
        ["legal-text-mcp-de"], capture_output=True, timeout=10
    )
    assert result.returncode == 0, f"exit {result.returncode}"
    assert b"Usage:" in result.stdout, "no Usage: line in bare-invocation output"
    print("CLI bare-invocation OK")


def smoke_cli_version_prints_2_x() -> None:
    result = subprocess.run(
        ["legal-text-mcp-de", "--version"], capture_output=True, timeout=10
    )
    assert result.returncode == 0, f"exit {result.returncode}"
    assert b"2." in result.stdout, "version not in 2.x range"
    print("CLI --version OK")
```

Wire them into `main()`:

```python
def main() -> int:
    # ... existing checks ...
    smoke_cli_bare_invocation_prints_help()
    smoke_cli_version_prints_2_x()
    print("All E2E checks passed.")
    return 0
```

- [ ] **Step 3: Run**

Run: `uv run --group dev python scripts/verify_e2e.py`
Expected: All existing checks pass plus the two new CLI smoke lines.

- [ ] **Step 4: Commit**

```bash
git add scripts/verify_e2e.py
git commit -s -S -m "test(e2e): add CLI bare-invocation + --version smoke tests"
```

---

## Task 19: Docs migration — README, quickstarts, deployment, mkdocs

**Files:**
- Modify: `README.md`, `docs/quickstart/{claude-desktop,cursor,uvx,docker,stdio}.md`, `docs/api/index.md`, `docs/operations/production-deployment.md`, `deployment/Dockerfile.hosted`, `deployment/deploy.sh`, `Justfile`, `mkdocs.yml`
- Create: `docs/cli/index.md`

- [ ] **Step 1: README — install modes get `serve`**

In `README.md`, find every plain `legal-text-mcp-de` invocation in the Install / Quickstart code blocks. Replace with `legal-text-mcp-de serve`. Specifically:

- Mode 1 `pip install` block: `legal-text-mcp-de` → `legal-text-mcp-de serve`
- Mode 2 `uvx legal-text-mcp-de` → `uvx legal-text-mcp-de serve`
- Mode 4 self-built corpus block: `uvx legal-text-mcp-de` → `uvx legal-text-mcp-de serve`
- Quickstart "Run the MCP server" block: `uv run legal-text-mcp-de` → `uv run legal-text-mcp-de serve`

Then add a new section just below `## Installation`:

```markdown
## CLI

`legal-text-mcp-de` ships a full subcommand CLI. Bare invocation prints
`--help`. Common commands:

```bash
legal-text-mcp-de serve              # start the MCP server (replaces the v2.0 bare invocation)
legal-text-mcp-de http               # start the FastAPI HTTP API
legal-text-mcp-de laws --query DSGVO # list laws
legal-text-mcp-de norm BGB "§ 433"   # fetch a single norm
legal-text-mcp-de search Werbung     # full-text search
legal-text-mcp-de corpus pull        # download the signed corpus bundle
legal-text-mcp-de corpus verify      # cosign-verify the local bundle
legal-text-mcp-de version            # version + Python + platform
```

Add `--json` to any subcommand for machine-readable output (matches the
HTTP API's response schema). See [CLI reference](docs/cli/index.md) for
the full subcommand list.

> **BREAKING in v2.1.0:** bare `legal-text-mcp-de` now prints `--help`.
> Append `serve` to keep the v2.0 behaviour (started the MCP server).
```

- [ ] **Step 2: Quickstarts — append `serve`**

For each of these files, find the `legal-text-mcp-de` invocations in code blocks (especially the JSON config snippets for Claude Desktop) and append `serve` where it acts as the entry point:

- `docs/quickstart/claude-desktop.md` — `"args": ["legal-text-mcp-de"]` → `"args": ["legal-text-mcp-de", "serve"]`
- `docs/quickstart/cursor.md` — same shape
- `docs/quickstart/uvx.md` — `uvx legal-text-mcp-de` → `uvx legal-text-mcp-de serve`
- `docs/quickstart/docker.md` — `docker run … :2.0.1` → `docker run … :2.1.0 serve`
- `docs/quickstart/stdio.md` — `args: ["legal-text-mcp-de"]` → `args: ["legal-text-mcp-de", "serve"]`

- [ ] **Step 3: `docs/api/index.md` — add `legal-text-mcp-de http` alternative**

Find the "Starting the HTTP API" section. Below the `uvicorn` example, add:

```markdown
Equivalent CLI subcommand (v2.1.0+):

```bash
legal-text-mcp-de http --host 127.0.0.1 --port 8080
```
```

- [ ] **Step 4: `docs/operations/production-deployment.md` — Docker `CMD` with `serve`; tag bumped**

Replace every occurrence of `legal-text-mcp-de:2.0.1` with `:2.1.0`. Append `serve` to the `docker run` example commands. The Caddyfile + nginx examples' upstream image reference stays the same shape.

- [ ] **Step 5: `deployment/Dockerfile.hosted`**

```diff
- FROM ghcr.io/klein-business/legal-text-mcp-de:2.0.0@sha256:10958304da461768bddd8d90ff759bb2e0a2e6970693b304ef3c8ec2b8723c31
+ FROM ghcr.io/klein-business/legal-text-mcp-de:2.1.0
+ # The digest pin returns in a follow-up patch (v2.1.1) once the v2.1.0
+ # release-workflow publishes the image and the manifest digest is known.
+ # CHANGELOG [2.1.0] notes this as a known follow-up.
- CMD ["uv", "run", "--frozen", "--no-sync", "legal-text-mcp-de"]
+ CMD ["uv", "run", "--frozen", "--no-sync", "legal-text-mcp-de", "serve"]
```

- [ ] **Step 6: `deployment/deploy.sh`**

Replace the image-tag example near the top: `:2.0.1` → `:2.1.0`. Append `serve` in any `docker run` example.

- [ ] **Step 7: `Justfile` — add CLI shortcuts**

Append:

```just
# CLI shortcuts (v2.1.0+).
cli-help:
    uv run legal-text-mcp-de --help

cli-search QUERY:
    uv run legal-text-mcp-de search "{{QUERY}}"

cli-norm CODE NORM:
    uv run legal-text-mcp-de norm "{{CODE}}" "{{NORM}}"

cli-version:
    uv run legal-text-mcp-de version
```

Also update the existing `run` and `api` targets to use the new subcommands:

```diff
- DATASET_PATH=tests/fixtures/normalized STRICT_STARTUP=true uv run legal-text-mcp-de
+ DATASET_PATH=tests/fixtures/normalized STRICT_STARTUP=true uv run legal-text-mcp-de serve
```

and for `api`:

```diff
- DATASET_PATH=tests/fixtures/normalized STRICT_STARTUP=true uv run uvicorn legal_text_mcp_de.http_api:app …
+ DATASET_PATH=tests/fixtures/normalized STRICT_STARTUP=true uv run legal-text-mcp-de http --port 8080
```

- [ ] **Step 8: `mkdocs.yml` — new "CLI" nav entry**

Find the `nav:` block. Add a new top-level entry **after** "Quickstart" and **before** "Concepts":

```yaml
  - CLI:
      - Reference: cli/index.md
```

- [ ] **Step 9: Create `docs/cli/index.md`**

Curated CLI reference (do not auto-generate this round — YAGNI):

```markdown
# CLI reference

`legal-text-mcp-de` is a `typer`-based subcommand CLI introduced in
v2.1.0. Bare invocation prints `--help`. Add `--json` to any subcommand
for machine-readable output (matches the HTTP API response schema).

## Global flags

| Flag | Purpose |
|---|---|
| `--json` | Force JSON output even on a TTY |
| `--quiet`, `-q` | Suppress non-essential stderr |
| `--debug`, `-v` | Verbose logging |
| `--version` | Print version and exit |

## Server lifecycle

```bash
legal-text-mcp-de serve [--host H] [--port P] [--dataset PATH] [--strict]
legal-text-mcp-de http  [--host H] [--port P] [--dataset PATH]
```

## Read-only lookups

```bash
legal-text-mcp-de laws [--query Q]
legal-text-mcp-de law  CODE [--full]
legal-text-mcp-de norm CODE NORM_ID
legal-text-mcp-de cite --code CODE --unit UNIT --paragraph P [--child-unit U --child-value V]
legal-text-mcp-de search QUERY [--code C ...] [--limit N]
legal-text-mcp-de meta CODE
legal-text-mcp-de coverage
legal-text-mcp-de limitations [--source-family F] [--terminal-state S] [--state-code C] [--law-id L]
legal-text-mcp-de related CODE NORM_ID
```

## Smart tool

```bash
legal-text-mcp-de research TOPIC [--max-candidates N] [--detail brief|full]
```

Needs `ANTHROPIC_API_KEY` for full LLM-ranked synthesis. Without the key,
degrades gracefully to a ranked search-hits fallback (exit code 0).

## Corpus lifecycle

```bash
legal-text-mcp-de corpus pull   [--version V]
legal-text-mcp-de corpus verify [--cert-identity ID]
legal-text-mcp-de corpus info
```

## Diagnostics

```bash
legal-text-mcp-de health  [--url URL]
legal-text-mcp-de version
legal-text-mcp-de completion show    {bash|zsh|fish}
legal-text-mcp-de completion install {bash|zsh|fish}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Runtime / business error (LegalTextError) |
| 2 | CLI usage error (typer default) |
| 3 | Smart-tool sampling error (hard) |
| 4 | Corpus error (pull or verify failed) |
| 5 | Connectivity error (`health` unreachable) |
| 130 | SIGINT |

## See also

- [HTTP API overview](../api/index.md)
- [Migration v1 → v2 → v2.1](../operations/migration-v1-v2.md)
- [Production deployment](../operations/production-deployment.md)
```

- [ ] **Step 10: Verify docs links**

Run: `uv run --group dev python -c "import sys; sys.path.insert(0, 'scripts'); from verify_release import check_docs_links; check_docs_links(); print('OK')"`
Expected: `OK`.

- [ ] **Step 11: Commit**

```bash
git add README.md docs/quickstart/ docs/api/index.md docs/operations/production-deployment.md deployment/Dockerfile.hosted deployment/deploy.sh Justfile mkdocs.yml docs/cli/index.md
git commit -s -S -m "docs(v2.1): migrate invocations to explicit serve; new CLI reference page"
```

---

## Task 20: `versioning.md` clarification + `migration-v1-v2.md` v2.0→v2.1 section + CHANGELOG

**Files:**
- Modify: `docs/operations/versioning.md`
- Modify: `docs/operations/migration-v1-v2.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: `versioning.md` — CLI clarification**

Find the "Stability contract" section. After the bullet list, add a new paragraph:

```markdown
The CLI invocation form (subcommand names, flag names, positional
argument order) is **not** part of the v1.0.0 stability contract. CLI
subcommand renames trigger a CHANGELOG entry with a clear migration
note, but no major version bump.
```

- [ ] **Step 2: `migration-v1-v2.md` — append v2.0 → v2.1 section**

Append to the bottom of `docs/operations/migration-v1-v2.md`:

```markdown
## v2.0 → v2.1 — CLI introduction (BREAKING for invocation form)

v2.1.0 introduces a `typer`-based CLI as the new `legal-text-mcp-de`
entry point. Bare invocation now prints `--help`; the MCP server
requires the explicit `serve` subcommand.

**Migration:**

| Before (v2.0.x) | After (v2.1.0+) |
|---|---|
| `legal-text-mcp-de` | `legal-text-mcp-de serve` |
| `uvx legal-text-mcp-de` | `uvx legal-text-mcp-de serve` |
| `docker run … :2.0.1` | `docker run … :2.1.0 serve` |
| Claude Desktop `"args": ["legal-text-mcp-de"]` | `"args": ["legal-text-mcp-de", "serve"]` |

**Not breaking:**

- All 9 v1 MCP tool signatures + `research_topic`
- HTTP API surface
- Environment variables (`DATASET_PATH`, `STRICT_STARTUP`,
  `MAX_REQUEST_BODY_BYTES`, …)
- Corpus bundle format

**Why not v3.0.0:** the `docs/operations/versioning.md` stability
contract explicitly enumerates "MCP tool signature, HTTP route, or
dataset schema". CLI invocation form is outside that contract and
evolves with minor versions.
```

- [ ] **Step 3: `CHANGELOG.md` — new `[2.1.0]` block**

Insert above the existing `## [2.0.1]` entry:

```markdown
## [2.1.0] - 2026-05-18

### ⚠️ Breaking

- **Bare invocation prints help:** `legal-text-mcp-de` (no args) now
  prints `--help` instead of silently starting the MCP server. Use
  `legal-text-mcp-de serve` to start the MCP server explicitly.
  Affects: Claude Desktop configs, Docker `CMD`, `uvx` invocations.
  See [migration-v1-v2.md](docs/operations/migration-v1-v2.md) for the
  copy-paste-ready migration matrix.

### Added

- **`typer`-based CLI** as the new `legal-text-mcp-de` entry point.
  14 subcommands covering every MCP tool plus server lifecycle, corpus
  management, and diagnostics. See
  [docs/cli/index.md](docs/cli/index.md) for the full reference.
- New subcommands:
  - Server: `serve`, `http`
  - Lookups: `laws`, `law`, `norm`, `cite`, `search`, `meta`,
    `coverage`, `limitations`, `related`
  - Smart tool: `research`
  - Corpus: `corpus pull`, `corpus verify`, `corpus info`
  - Diagnostics: `health`, `version`,
    `completion show|install {bash|zsh|fish}`
- Global flags: `--json`, `--quiet`, `--debug`, `--version`.
- CLI JSON output schema mirrors `legal_text_mcp_de.http_models.*`
  Pydantic shapes — same models the HTTP API uses.
- Exit-code matrix: 0 success, 1 runtime, 2 usage, 3 sampling,
  4 corpus, 5 connectivity, 130 SIGINT.

### Changed

- `[project.scripts] legal-text-mcp-de` console entry repointed from
  `legal_text_mcp_de.server:main` to `legal_text_mcp_de.cli:main`.
  Old entry point preserved as internal call surface for legacy
  callers (still importable).
- `typer >= 0.20, < 1` promoted from transitive dependency
  (via `mcp[cli]==1.27.1`) to direct project dependency.

### Docs

- New: `docs/cli/index.md`, `mkdocs.yml` "CLI" nav entry.
- `README.md`: new "CLI" section; install modes updated to `serve`.
- All `docs/quickstart/*.md` updated to use `serve` in config snippets.
- `docs/operations/versioning.md`: new paragraph clarifying that the
  CLI invocation form is outside the v1.0.0 stability contract.
- `docs/operations/migration-v1-v2.md`: new "v2.0 → v2.1" section.

### Compatibility

- MCP tool signatures (all 10 incl. `research_topic`) unchanged —
  `tests/test_v1_compat.py` still green.
- HTTP API surface unchanged.
```

- [ ] **Step 4: Verify**

Run: `uv run --group dev python -c "import sys; sys.path.insert(0, 'scripts'); from verify_release import check_docs_links; check_docs_links(); print('OK')"`
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add CHANGELOG.md docs/operations/versioning.md docs/operations/migration-v1-v2.md
git commit -s -S -m "docs(v2.1): CHANGELOG + migration matrix + CLI-stability paragraph in versioning.md"
```

---

## Task 21: Version bump 2.0.1 → 2.1.0 + release-please manifest

**Files:**
- Modify: `pyproject.toml`
- Modify: `.release-please-manifest.json`
- Modify: `uv.lock` (regenerated)

- [ ] **Step 1: Bump `pyproject.toml`**

```diff
- version = "2.0.1"
+ version = "2.1.0"
```

- [ ] **Step 2: Bump `.release-please-manifest.json`**

```diff
- {".": "2.0.1"}
+ {".": "2.1.0"}
```

(Pretty-print preserved; if the file is on one line, the same.)

- [ ] **Step 3: Regenerate `uv.lock`**

Run: `uv lock`
Expected: `Updated legal-text-mcp-de v2.0.1 -> v2.1.0`.

- [ ] **Step 4: Smoke-test the bumped version**

Run: `uv run legal-text-mcp-de version`
Expected: `version: 2.1.0` (or whatever JSON shape the version subcommand prints).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .release-please-manifest.json uv.lock
git commit -s -S -m "chore(release): v2.1.0 — typer CLI"
```

---

## Task 22: PR + merge + tag + release

- [ ] **Step 1: Push branch**

```bash
git push -u origin feat/cli-typer-v2.1.0
```

- [ ] **Step 2: Open PR with summary**

```bash
gh pr create --repo klein-business/legal-text-mcp-de --base main \
  --title "feat(cli)!: typer-based CLI; bare invocation prints --help (v2.1.0)" \
  --body "$(cat <<'EOF'
Implements the CLI per docs/superpowers/specs/2026-05-18-cli-typer-design.md.

- 14 subcommands under src/legal_text_mcp_de/cli/
- Bare 'legal-text-mcp-de' prints --help; 'serve' starts the MCP server
- typer >= 0.20 promoted from transitive to direct dep
- JSON output schema mirrors http_models.* (free CLI-vs-HTTP contract check)
- All v1 MCP tool signatures unchanged (tests/test_v1_compat.py green)
- Exit codes: 0 success, 1 runtime, 2 usage, 3 sampling, 4 corpus, 5 connectivity
- README, all docs/quickstart/*, docs/operations/*, Justfile, mkdocs.yml,
  deployment/* updated to the new invocation form

BREAKING: see docs/operations/migration-v1-v2.md (new "v2.0 -> v2.1" section).
EOF
)"
```

- [ ] **Step 3: Wait for CI**

Wait for all required checks to pass (Build, CI, CodeQL, Tests, MegaLinter, Trivy, uv runtime, Release gate, ...).

- [ ] **Step 4: Squash-merge**

```bash
gh pr merge --repo klein-business/legal-text-mcp-de \
  --squash --admin --delete-branch \
  --subject "feat(cli)!: typer-based CLI; bare invocation prints --help (v2.1.0)"
```

- [ ] **Step 5: Tag v2.1.0 on the merge commit + push**

```bash
git fetch origin main
git tag -s v2.1.0 -m "v2.1.0 — typer CLI" "$(git rev-parse origin/main)"
git push origin v2.1.0
```

- [ ] **Step 6: Watch Release + Docs workflows**

Watch the v2.1.0 tag run:

```bash
gh run list --repo klein-business/legal-text-mcp-de --limit 5
```

Expected: Release workflow green end-to-end (the Create-Release collision fix from PR #80 means the new `gh release upload --clobber` path takes care of the asset attachment). Docs workflow publishes the `2.1.0` mike alias and rolls `latest` forward.

- [ ] **Step 7: Verify**

```bash
pip install --no-cache-dir --dry-run legal-text-mcp-de==2.1.0   # PyPI live
docker pull ghcr.io/klein-business/legal-text-mcp-de:2.1.0      # GHCR live
gh release view v2.1.0 --repo klein-business/legal-text-mcp-de  # GH Release with assets + .intoto.jsonl
curl -fsSL https://klein-business.github.io/legal-text-mcp-de/2.1.0/  # docs live
```

Expected: all four checks succeed.

---

## Self-review notes

(For the author; can be deleted before merge.)

- ✅ Spec section 1 (subcommand inventory) → Tasks 4–16 (one task per subcommand or sub-Typer group).
- ✅ Spec section 2 (module structure) → Files map at the top of this plan matches 1:1.
- ✅ Spec section 3 (output / errors / exit codes) → Tasks 2 + 14 (sampling exit 3) + 15 (corpus exit 4) + 16 (connectivity exit 5).
- ✅ Spec section 4 (testing) → Tasks 1, 2, 3, 4–12, 13, 14, 15, 16, 17 (full-suite gate), 18 (smoke).
- ✅ Spec section 5 (migration) → Tasks 13 (entry-point swap) + 19 (docs) + 20 (CHANGELOG + versioning + migration page) + 21 (version bump) + 22 (release).
- ✅ All subcommand names match between tasks: `laws`, `law`, `norm`, `cite`, `search`, `meta`, `coverage`, `limitations`, `related`, `research`, `serve`, `http`, `corpus pull/verify/info`, `health`, `version`, `completion show/install`.
- ✅ JSON envelope shape `{"data": …, "error": null}` used consistently across `_output.py`, lookup tests, and the CLI reference page.
- ✅ Exit codes 0/1/2/3/4/5/130 referenced consistently in `_output.py` constants, exit-code mapping in commands, the CLI reference page, and the spec.
- ✅ No `TBD`, `TODO`, `FIXME`, `implement later`, or "similar to Task N" — every step contains the exact code/command.
