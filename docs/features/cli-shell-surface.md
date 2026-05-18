---
type: documentation
entity: feature
feature: "cli-shell-surface"
version: 2.1
---

# Feature: cli-shell-surface

> Part of [legal-text-mcp-de](../overview.md)

## Summary

v2.1.0 introduces a [Typer](https://typer.tiangolo.com)-based command-line
interface that exposes every MCP tool, the FastMCP server lifecycle, the
FastAPI HTTP transport, the signed corpus bundle pipeline, and a set of
diagnostic commands behind 14 explicit subcommands. The CLI is the new
user-facing entry point for the `legal-text-mcp-de` console script.

> **Breaking change in v2.1.0:** bare `legal-text-mcp-de` invocation now
> prints `--help` instead of starting the MCP server. Use
> `legal-text-mcp-de serve` to start the server. The Dockerfile `CMD` was
> updated accordingly. See the `[2.1.0]` entry in
> [CHANGELOG](../changelog.md) for migration details.

The CLI's JSON output envelope is contract-compatible with the existing
HTTP API responses (`legal_text_mcp_de.http_models.*`), so the same
client code that consumes `/laws/{code}` can consume
`legal-text-mcp-de law BGB --json` interchangeably.

## How It Works

### User Flow

```bash
# Start the MCP server (replaces pre-v2.1 bare invocation):
DATASET_PATH=src/tests/fixtures/normalized \
  uv run legal-text-mcp-de serve

# Or run a one-shot lookup:
uv run legal-text-mcp-de law BGB
uv run legal-text-mcp-de search "widerruf" --code bgb --limit 5

# Pipe-friendly JSON envelope (machine-readable matches http_models):
uv run legal-text-mcp-de norm BGB "§ 355" --json | jq '.data.norm.text'

# Multi-step LLM research (needs ANTHROPIC_API_KEY for full mode):
uv run legal-text-mcp-de research "Datenschutz Einwilligung" --detail full

# Pull and verify the signed corpus bundle:
uv run legal-text-mcp-de corpus pull --version latest
uv run legal-text-mcp-de corpus verify
```

The full subcommand catalogue is documented in
[docs/cli/index.md](../cli/index.md).

### Output Mode

Output mode is decided per-process based on the stream `--json` is
writing to:

| Situation | Mode | Where errors go |
| --------- | ---- | --------------- |
| stdout is a TTY | text (Rich) | stderr |
| stdout is piped / redirected | JSON envelope | stdout (so `\| jq` works) |
| `--json` flag set explicitly | JSON envelope (always wins) | stdout |

Success payloads are `{"data": …, "error": null}`. Error payloads are
`{"data": null, "error": {"code", "message", "details"}}` — the same
`ErrorBody` shape used by the HTTP API.

### Technical Flow

1. The user invokes `legal-text-mcp-de <subcommand> [...]` (the
   console-script registered as `legal_text_mcp_de.cli:main`).
2. The root Typer callback `_root` captures `--json`, `--quiet`, `--debug`
   into `ctx.obj`, then either dispatches to the named subcommand or — if
   no subcommand was provided — prints `--help` and exits 0.
3. Read-only subcommands call `get_runtime_or_die()` once per process to
   instantiate `Settings()` (reads env vars at call time) and
   `LegalTextRuntime.from_settings(settings, strict=True)`. Subsequent
   subcommands in the same process reuse the cached runtime.
4. The subcommand calls the appropriate runtime method (or an external
   helper for `serve`, `http`, `research`, `corpus`, `health`) and passes
   the resulting payload to `render_data`.
5. `render_data` checks `is_json_mode` against the output stream and
   writes either a Rich-rendered table or a JSON envelope.
6. On exception, the subcommand catches a domain-specific error type
   (`LegalTextError`, `SamplingError`, `httpx.HTTPError`, or a
   subprocess non-zero exit) and calls `render_error` + `raise
   typer.Exit(code=…)` with the matching exit-code constant.

## Implementation

| Subcommand | File | Backing function / external call |
| ---------- | ---- | --------------------------------- |
| `laws [--query Q]` | [`cli/_lookups.py`](../modules/cli.md) | `LegalTextRuntime.list_laws(query)` |
| `law CODE [--full]` | [`cli/_lookups.py`](../modules/cli.md) | `LegalTextRuntime.get_law(code)`; strips norm bodies unless `--full`. |
| `norm CODE NORM_ID` | [`cli/_lookups.py`](../modules/cli.md) | `LegalTextRuntime.get_norm(code, norm_id)` |
| `cite --code --unit --paragraph [--child-unit --child-value]` | [`cli/_lookups.py`](../modules/cli.md) | `LegalTextRuntime.resolve_citation(...)` |
| `search QUERY [--code …] [--limit N]` | [`cli/_lookups.py`](../modules/cli.md) | `LegalTextRuntime.search_laws(query, codes)`; `--limit` applied client-side. |
| `meta CODE` | [`cli/_lookups.py`](../modules/cli.md) | `LegalTextRuntime.get_source_metadata(code)` |
| `coverage` | [`cli/_lookups.py`](../modules/cli.md) | `LegalTextRuntime.get_corpus_coverage()` |
| `limitations [filters…]` | [`cli/_lookups.py`](../modules/cli.md) | `LegalTextRuntime.get_source_limitations(...)` |
| `related CODE NORM_ID` | [`cli/_lookups.py`](../modules/cli.md) | `LegalTextRuntime.get_related_norms(code, norm_id)` |
| `serve [--host --port --dataset --strict]` | [`cli/_server.py`](../modules/cli.md) | `create_mcp_app(runtime).run(transport="streamable-http")` |
| `http [--host --port --dataset]` | [`cli/_server.py`](../modules/cli.md) | `uvicorn.run("legal_text_mcp_de.http_api:app", …)` |
| `research TOPIC [--max-candidates --detail]` | [`cli/_research.py`](../modules/cli.md) | `tools.research_topic._run_research(...)` |
| `corpus pull [--version]` | [`cli/_corpus.py`](../modules/cli.md) | `subprocess.run(["oras", "pull", …])` |
| `corpus verify [--cert-identity]` | [`cli/_corpus.py`](../modules/cli.md) | `subprocess.run(["cosign", "verify-blob", …])` |
| `corpus info` | [`cli/_corpus.py`](../modules/cli.md) | Filesystem listing of `$XDG_CACHE_HOME/legal-text-mcp-de`. |
| `version` | [`cli/_diagnostic.py`](../modules/cli.md) | `importlib.metadata.version("legal-text-mcp-de")` + `platform.*`. |
| `health [--url]` | [`cli/_diagnostic.py`](../modules/cli.md) | `httpx.get(url, timeout=5.0)` |
| `completion show {bash\|zsh\|fish}` | [`cli/_diagnostic.py`](../modules/cli.md) | `typer.completion.get_completion_script(...)` |
| `completion install {bash\|zsh\|fish}` | [`cli/_diagnostic.py`](../modules/cli.md) | Prints install instructions (does not modify RC files). |

Module-level documentation lives at [docs/modules/cli.md](../modules/cli.md).

## Exit Codes

| Code | Constant | When |
| ---- | -------- | ---- |
| 0 | `EXIT_SUCCESS` | Normal success; also a `research` run that degraded to a ranked-search fallback because no sampling client was available. |
| 1 | `EXIT_RUNTIME` | `LegalTextError` from runtime (missing dataset, unknown law/norm, invalid citation). Error envelope carries the original `code` + `details`. |
| 2 | `EXIT_USAGE` | Typer default: unknown flag, missing argument. Also `completion {show,install}` with an unsupported shell name. |
| 3 | `EXIT_SAMPLING` | `SamplingError` raised by `_run_research` (timeout, schema violation, refusal). Distinguishable from `EXIT_RUNTIME` so CI can treat sampling outages differently from data errors. |
| 4 | `EXIT_CORPUS` | `corpus pull` non-zero (`oras` missing or registry unreachable); `corpus verify` with no cached bundle or non-zero `cosign verify-blob`. |
| 5 | `EXIT_CONNECTIVITY` | `health` subcommand: transport error (`httpx.HTTPError`) or non-200 response. |
| 130 | `EXIT_INTERRUPT` | SIGINT. |

## Edge Cases

- **No `DATASET_PATH` and no bundle in the XDG cache.** The first read-only
  subcommand call to `get_runtime_or_die()` raises `LegalTextError` with
  the runtime's structured `{code, message, details}`. Exit: 1.
- **`research` without `ANTHROPIC_API_KEY`.** `_run_research` falls back to
  the ranked-search degraded mode and returns a `ResearchReport` with
  `status="degraded_no_sampling"`. The CLI exits 0 — the degraded payload
  is a valid response, not an error. See
  [research-topic-smart-tool](research-topic-smart-tool.md) for the
  contract.
- **`research` with sampling timeout / schema violation / refusal.** A
  hard `SamplingError` exits 3.
- **`corpus pull` without `oras` installed.** `subprocess.run` raises or
  returns non-zero; the CLI writes an error envelope and exits 4.
- **`corpus verify` against the wrong tag.** `cosign verify-blob` fails;
  exit 4 with the verifier's stderr in the error envelope's `details`.
- **`health` against an unreachable URL.** `httpx.HTTPError`; exit 5.
- **Bare `legal-text-mcp-de`.** Prints `--help` and exits 0. Pre-v2.1.0
  this started the MCP server.
- **`--json` on a TTY.** The flag wins: JSON envelope on stdout even when
  the user is reading the result in a terminal.

## Compatibility with the HTTP API

Every CLI JSON envelope's `data` field carries the exact same dict shape
as the corresponding HTTP endpoint response, because both pathways
serialise the same `LegalTextRuntime` return values through the same
`legal_text_mcp_de.http_models.*` Pydantic models:

```bash
# These two snippets return the same payload inside the `data` key:
curl -s http://localhost:8001/laws/bgb            | jq
legal-text-mcp-de law bgb --full --json | jq .data
```

This keeps the CLI a thin shell over the underlying transport contract —
no parallel JSON schema to maintain.

## Related

- [docs/cli/index.md](../cli/index.md) — curated end-user CLI reference.
- [cli module](../modules/cli.md) — package structure, symbols, tests.
- [mcp-law-tools](mcp-law-tools.md) — the MCP tools each read-only
  subcommand wraps.
- [research-topic-smart-tool](research-topic-smart-tool.md) — the smart
  tool behind `research`.
- [http-api](http-api.md) — the FastAPI surface behind `http` and the
  source of the JSON shape used by every CLI subcommand.
