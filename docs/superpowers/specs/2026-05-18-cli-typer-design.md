# CLI — typer-based subcommand surface for `legal-text-mcp-de`

| Field | Value |
|---|---|
| Date | 2026-05-18 |
| Status | draft |
| Target release | v2.1.0 |
| Author | Martin Klein |
| Supersedes | n/a |
| Related | docs/superpowers/specs/2026-05-17-v2-mcp-native-design.md (v2.0 surface) |

## Goal

Add a `typer`-based CLI to `legal-text-mcp-de` that exposes every MCP
tool (`list_laws`, `get_law`, `get_norm`, `resolve_citation`,
`search_laws`, `get_source_metadata`, `get_corpus_coverage`,
`get_source_limitations`, `get_related_norms`, `research_topic`) as a
shell subcommand, alongside server lifecycle (`serve`, `http`), corpus
management (`corpus pull / verify / info`), and diagnostics (`health`,
`version`, `completion`). The CLI complements the existing MCP server
and HTTP API; the underlying `LegalTextRuntime` is shared between all
three surfaces so behaviour stays identical.

## Non-goals

- **No** prompt invocation (`/rechtsfrage`, …) — prompts are interactive
  and belong in an MCP client, not a CLI.
- **No** `stop` / `restart` server-lifecycle commands — process
  supervision (systemd, Docker, Kubernetes) is the operator's domain.
- **No** config-file format — env-variables remain the single source of
  truth.
- **No** self-update / `legal-text-mcp-de update` — `pip`, `uvx`, and
  the container registry already do this.
- **No** REPL mode — out of scope; defeats the purpose of a structured
  CLI.
- **No** `corpus build` — stays a maintainer tool in
  `prepare_data.build_corpus`.

## Architecture in three sentences

The CLI is a thin shell over the existing `LegalTextRuntime` (the same
class that backs the MCP server and the FastAPI API). `typer` provides
the subcommand graph and shell-completion infrastructure; output
rendering and exit-code mapping live in a small `cli/_output.py` module
that emits either Rich-formatted text (TTY) or JSON matching the
existing `http_models` Pydantic shapes. The `legal-text-mcp-de` console
script is repointed from `server:main` to `cli:main`; bare invocation
prints `--help` (modern Git/Docker/Caddy convention) — explicit
`legal-text-mcp-de serve` replaces the old implicit server start.

## Tech stack

- `typer ≥ 0.20` — already a transitive dependency via
  `mcp[cli]==1.27.1`; this spec promotes it to a direct dep.
- `rich` — already pulled by `typer`; used for tables, Markdown
  rendering of norm text.
- `pydantic v2` — already in use; CLI reuses `http_models.*` for the
  JSON output schema (single source of truth shared with the HTTP API).
- `httpx` — already in use; `health` subcommand uses it to probe a
  running server.
- No new external runtime dependencies.

## Design

### 1. Subcommand inventory

```
legal-text-mcp-de [--json] [--quiet] [--debug] [--version] <subcommand> ...

Server lifecycle
  serve   [--host H] [--port P] [--dataset PATH] [--strict]
          Start the MCP server (streamable HTTP transport).

  http    [--host H] [--port P] [--dataset PATH]
          Start the FastAPI HTTP API.

Read-only lookups (1:1 mapping to the 9 v1 MCP tools)
  laws    [--query Q] [--code C ...]                  → list_laws
  law     CODE [--full]                               → get_law
  norm    CODE NORM_ID                                → get_norm
  cite    CITATION                                    → resolve_citation
                                                        (e.g. "§ 433 Abs. 1 BGB")
  search  QUERY [--code C ...] [--limit N]            → search_laws
  meta    CODE                                        → get_source_metadata
  coverage                                            → get_corpus_coverage
  limitations [--source-family F] [--terminal-state S]
                                                      → get_source_limitations
  related CODE NORM_ID                                → get_related_norms

Smart tools
  research TOPIC [--max-norms N]                      → research_topic
          Needs ANTHROPIC_API_KEY. Gracefully degrades to a
          ranked-search-hits fallback when sampling is unavailable
          (matches the existing Phase E behaviour).

Corpus lifecycle
  corpus pull   [--version V]                         ORAS download from GHCR
  corpus verify [--cert-identity ID]                  cosign verify of the local bundle
  corpus info                                         Show local bundle metadata + path

Diagnostic / ops
  health  [--url URL]                                 HTTP GET /health on a running server
  version                                             Print version + git SHA + Python version
  completion install {bash|zsh|fish}                  Install shell completion script
  completion show    {bash|zsh|fish}                  Print completion script to stdout
```

= **14 explicit subcommands** + 4 global flags + `--version`.

### 2. Module structure

```
src/legal_text_mcp_de/cli/
├── __init__.py        # Root Typer app + global flags + main() entry
├── _output.py         # Text/JSON renderers, exit-code mapping, ErrorHandler
├── _runtime.py        # Lazy LegalTextRuntime loader, shared CLI dependencies
├── _lookups.py        # 9 read-only commands
├── _server.py         # serve, http (thin wrappers over existing entrypoints)
├── _research.py       # research smart-tool
├── _corpus.py         # `corpus` sub-Typer: pull, verify, info
└── _diagnostic.py     # health, version, completion (sub-Typer for completion)

tests/test_cli/
├── __init__.py
├── test_main.py           # bare invocation → --help; --version; unknown subcommand → exit 2
├── test_output.py         # JSON/Text formatters, error → exit-code mapping
├── test_lookups.py        # one happy + one error path per lookup (= 18 tests)
├── test_server.py         # flag parsing only; server.run() is mocked
├── test_research.py       # MockSamplingClient happy + no-key degradation
├── test_corpus.py         # subprocess mocked for oras / cosign
└── test_diagnostic.py     # httpx mocked for health; completion stdout
```

Files **not** touched by this spec:

- `src/legal_text_mcp_de/{config,http_api,http_models,tools/*,resources/*,prompts/*,sampling/*,legal_texts/*}` — the CLI consumes the runtime; the runtime stays untouched.
- `tests/test_v1_compat.py` — the v1 tool contract is unaffected.

Files updated outside `src/legal_text_mcp_de/cli/`:

- `pyproject.toml` — `[project.scripts]` repointed to `cli:main`; `typer` promoted from transitive to direct dependency; version `2.0.1 → 2.1.0`.
- `src/legal_text_mcp_de/server.py` — `def main()` kept for backwards compatibility (internal callers); no behaviour change.
- `README.md`, all `docs/quickstart/*.md`, `docs/operations/production-deployment.md`, `deployment/Dockerfile.hosted`, `deployment/deploy.sh` — invocation form updated to `legal-text-mcp-de serve` (or `http`).
- `mkdocs.yml` — new top-level "CLI" nav entry pointing to `docs/cli/index.md`.
- `CHANGELOG.md` — new `[2.1.0]` block with a prominent `### Breaking` note.
- `docs/operations/versioning.md` — CLI-stability clarification (CLI form is not part of the v1.0.0 contract).
- `docs/operations/migration-v1-v2.md` — append "v2.0 → v2.1 (CLI introduction)" section.
- `Justfile` — new targets: `just cli-help`, `just search`, etc.
- `.release-please-manifest.json` — `2.0.1 → 2.1.0`.

New documentation:

- `docs/cli/index.md` — single curated CLI reference page (auto-generated from `typer` help via `typer --help` rendered into Markdown).

### 3. Output, errors, exit codes

#### Default output detection

| Context | Default format | Override |
|---|---|---|
| stdout is TTY (interactive) | Rich text | `--json` forces JSON |
| stdout is piped / redirected | JSON | `--json` is implicit; explicit on TTY too |

The `--quiet` flag suppresses progress/headers on text mode without
changing the data payload. The `--debug` flag enables verbose logging
on stderr.

#### JSON schema (single source of truth)

The CLI's JSON output **is** the HTTP API's JSON output. CLI consumers
can use the same `legal_text_mcp_de.http_models` Pydantic models the
HTTP API uses:

```jsonc
// success
{
  "data": { /* matches LawListResponse / SearchResponse / etc. */ },
  "error": null
}

// error (matches the ErrorBody shape from #64 / PR #78)
{
  "data": null,
  "error": {
    "code": "NORM_NOT_FOUND",
    "message": "Norm '§ 999' not found in BGB",
    "details": { "code": "BGB", "norm": "§ 999" }
  }
}
```

#### Exit-code matrix

| Code | Meaning | Example trigger |
|---|---|---|
| `0` | Success | data printed |
| `1` | Runtime / business error | `LegalTextError`: `NORM_NOT_FOUND`, `LAW_NOT_FOUND`, `AMBIGUOUS_CITATION`, `DATASET_NOT_READY` |
| `2` | CLI usage error | invalid args, unknown subcommand (typer default) |
| `3` | Smart-tool **hard** failure | sampling timeout, schema validation failure. **Soft** degradation (no `ANTHROPIC_API_KEY` → fall back to ranked search hits) prints a stderr warning and exits `0` — this matches the Phase E `research_topic` behaviour. |
| `4` | Corpus error | `corpus pull` ORAS failed, `corpus verify` signature mismatch |
| `5` | Connectivity error | `health` HTTP GET failed |
| `130` | SIGINT (Ctrl-C) | standard Unix convention |

#### Stderr conventions

- **stdout**: data only (text or JSON), never mixed.
- **stderr**: logging, warnings, progress, error messages.
- Guarantee: `legal-text-mcp-de search "…" > out.json && jq . out.json`
  works unfiltered.

#### Unhandled exceptions

```python
try:
    args.func(args)
except LegalTextError as e:
    render_error(e, exit_code=1)
except (SamplingError, SchemaValidationError) as e:
    render_error(e, exit_code=3)
except KeyboardInterrupt:
    sys.exit(130)
except Exception as e:  # noqa: BLE001
    render_error(e, exit_code=1, include_traceback=settings.debug)
```

In `--json` mode the traceback is part of `error.details.traceback`
only when `--debug` is active; otherwise the error is reduced to
`{"code": "INTERNAL", "message": str(exc)}`.

### 4. Testing & verification

#### Strategy

`typer.testing.CliRunner(mix_stderr=False)` drives every subcommand
against the existing `tests/fixtures/normalized` dataset (same fixture
the MCP / HTTP tests use). One happy-path test + one error-path test
per subcommand. JSON output is validated against the relevant
`http_models.*` Pydantic schema — this gives us a free contract check
that CLI and HTTP API stay in lockstep.

#### Coverage targets

| Module | Statement | Branch | Rationale |
|---|---|---|---|
| `cli/__init__.py` | 100% | 100% | small + dispatch-critical |
| `cli/_output.py` | 100% | ≥ 90% | TTY/JSON matrix + every exit-code path |
| `cli/_runtime.py` | ≥ 90% | ≥ 80% | lazy loader |
| `cli/_lookups.py` | ≥ 90% | ≥ 80% | one happy + one error per command |
| `cli/_server.py` | flag-parsing only | n/a | server.run() mocked; real start is integration |
| `cli/_research.py` | ≥ 90% | ≥ 80% | `MockSamplingClient` |
| `cli/_corpus.py` | ≥ 90% | ≥ 80% | subprocess mocked |
| `cli/_diagnostic.py` | ≥ 90% | ≥ 80% | httpx mocked |

Project-wide floor stays `fail_under = 86` (combined statement + branch); CLI raises it slightly.

#### Schema-drift gate

Each lookup test that asserts `--json` output deserialises the payload
through the matching `http_models.*` Pydantic class
(`LawListResponse`, `SearchResponse`, …). If a future change to
`http_models` is not mirrored in the CLI's response shape (or
vice-versa), these tests fail. Functions as a CLI-vs-HTTP contract
check at zero extra maintenance cost.

#### Mocking strategy

- `LegalTextRuntime`: real, loaded from `tests/fixtures/normalized`.
- `oras pull` / `cosign verify`: `monkeypatch.setattr("subprocess.run", fake_run)`.
- `research_topic` sampling: reuse `legal_text_mcp_de.sampling.testing.MockSamplingClient` (Phase D infra).
- `health` httpx call: `httpx.MockTransport` for deterministic responses.

#### Smoke tests in `scripts/verify_e2e.py`

```python
# Smoke 1: bare invocation prints help and exits 0
r = subprocess.run(["legal-text-mcp-de"], capture_output=True, timeout=5)
assert r.returncode == 0 and b"Usage:" in r.stdout

# Smoke 2: --version emits a parseable version string
r = subprocess.run(["legal-text-mcp-de", "--version"], capture_output=True, timeout=5)
assert r.returncode == 0 and b"2." in r.stdout
```

#### Acceptance criteria for the implementation PR

- [ ] All 14 subcommands implemented; ≥ 1 happy + ≥ 1 error test per command.
- [ ] `pytest tests/test_cli/` green.
- [ ] `scripts/verify_e2e.py` smoke tests green.
- [ ] Project-wide `coverage` ≥ 86 %; CLI module ≥ 90 % statement.
- [ ] `legal-text-mcp-de --help` renders without error.
- [ ] `legal-text-mcp-de serve` behaves identically to the old
  bare-`legal-text-mcp-de` entry point.
- [ ] `tests/test_v1_compat.py` still green (no v1-tool regression).
- [ ] `scripts/verify_release.check_docs_links()` green (no broken
  cross-references in the new `docs/cli/` content).
- [ ] OpenSSF Scorecard re-runs; no regression vs. the 7.1 baseline.

### 5. Migration & versioning

#### Breaking-change matrix

| Before | After (v2.1.0) | Who is affected |
|---|---|---|
| `legal-text-mcp-de` | `legal-text-mcp-de serve` | Claude Desktop configs, Docker `CMD`, `uvx`-examples |
| `uvx legal-text-mcp-de` | `uvx legal-text-mcp-de serve` | uvx auto-download mode |
| `docker run … :2.0.1` | `docker run … :2.1.0 serve` | Container default CMD; image bumped to 2.1.0 |

Not breaking: MCP tool signatures, HTTP API surface, env-vars, corpus
format. The v1 tool contract is still frozen by
`tests/test_v1_compat.py`.

#### Version bump: v2.1.0 (Minor), not v3.0.0

The repository's `docs/operations/versioning.md` defines MAJOR as
"breaking change to any public API (MCP tool signature, HTTP route, or
dataset schema)". CLI invocation form is not enumerated. The CLI did
not previously exist as a user-facing surface (bare invocation simply
started a server); we are not breaking a prior contract — we are
defining one.

User-base impact: zero (the repository was flipped to public on
2026-05-17; v2.0.1 was published on 2026-05-17T19:31:30Z). No
deprecation window is needed.

`docs/operations/versioning.md` will gain one paragraph clarifying the
CLI's status:

> The CLI invocation form (subcommand names, flag names, positional
> argument order) is not part of the v1.0.0 stability contract. CLI
> subcommand renames trigger a CHANGELOG entry with a clear migration
> note, but no major version bump.

#### Repo-internal file updates

```
pyproject.toml                       version 2.0.1 → 2.1.0
.release-please-manifest.json        2.0.1 → 2.1.0
CHANGELOG.md                         new [2.1.0] block with ### Breaking note
README.md                            all bare invocations → `serve`; new "CLI" section
docs/quickstart/{claude-desktop,cursor,uvx,docker,stdio}.md
                                     config snippets → explicit `serve`
docs/api/index.md                    uvicorn example + `legal-text-mcp-de http` alternative
docs/operations/production-deployment.md  docker CMD with `serve`
docs/operations/versioning.md        CLI-stability paragraph (above)
docs/operations/migration-v1-v2.md   new "v2.0 → v2.1 (CLI introduction)" section
deployment/Dockerfile.hosted         CMD updated; image tag bumped
deployment/deploy.sh                 example tag bumped
Justfile                             new targets: cli-help, search, norm, …
mkdocs.yml                           new "CLI" top-level nav entry
docs/cli/index.md                    NEW — curated CLI reference (typer --help rendered)
```

#### Announcement plan

- `CHANGELOG.md` `[2.1.0]` with a prominent `### Breaking` block at the top.
- `docs/operations/migration-v1-v2.md`: new "v2.0 → v2.1 (CLI
  introduction)" section with a copy-paste-ready `sed`-style migration
  for Claude Desktop configs.
- GitHub Release notes (auto-generated from CHANGELOG).
- README v2.1.0 with a "BREAKING" note next to the install modes.

#### Explicitly out of scope (for a later patch / minor)

- ~~Auto-generated mkdocs CLI reference from `typer` help~~ — nice but
  YAGNI for v2.1; the curated `docs/cli/index.md` is enough.
- ~~Interactive REPL mode~~ — defeats the CLI purpose.
- ~~Self-update (`legal-text-mcp-de update`)~~ — collides with
  pip / uvx / container.
- ~~Pre-built completion scripts in `man/`~~ — `completion install` is
  enough.

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| Docker `CMD` regression in third-party Dockerfiles inheriting from us | Image base tag bumped from `:2.0.1` to `:2.1.0`; users opting into `:2.1.0` accept the migration. `:2` and `:latest` rolling tags update simultaneously. |
| Typer auto-completion shells out to subprocess on install | `completion install` is opt-in; safe-default is "print to stdout". |
| `research` subcommand silently degrades on missing API key | Always print a stderr warning when degradation kicks in; exit code 0 (success with degradation) vs. 3 (hard failure). |
| Test fixture drift if `http_models` evolves and CLI JSON validates against them | Schema-drift tests catch it; CI is the gate. |

## Open questions

None — every question raised in brainstorming has a decision recorded
above (scope = D, bare-invocation = B, framework = `typer`, version =
v2.1.0 as Minor).

## References

- Existing v2.0 design: `docs/superpowers/specs/2026-05-17-v2-mcp-native-design.md`
- HTTP body-size middleware (the same `ErrorBody` shape the CLI emits in JSON mode): PR #78 / Issue #64
- Versioning policy: `docs/operations/versioning.md`
- typer documentation: https://typer.tiangolo.com/
- CLI guidelines (community reference): https://clig.dev/
