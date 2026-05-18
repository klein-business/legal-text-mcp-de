# Contributing to legal-text-mcp-de

Thanks for your interest in contributing. This project follows the
guidelines below to keep contributions reviewable and the codebase
healthy.

## Code of Conduct

All participants are expected to follow the
[Contributor Covenant 2.1](CODE_OF_CONDUCT.md). Report unacceptable
behaviour to `martin@klein.business`.

## Reporting security issues

Do **not** open a public issue for security vulnerabilities. See
[SECURITY.md](SECURITY.md) for the disclosure process.

## Where to ask questions

- General questions and discussions:
  [GitHub Discussions](https://github.com/klein-business/legal-text-mcp-de/discussions)
- Bug reports and feature requests:
  [GitHub Issues](https://github.com/klein-business/legal-text-mcp-de/issues)
  (use the appropriate template)

## Your first contribution

New here? Two curated entry points:

- 🌱 **[Good first issues](https://github.com/klein-business/legal-text-mcp-de/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)** —
  small, self-contained, well-specified tasks with a clear acceptance criterion.
  Each issue links to the exact files to touch and the tests to add. Typical scope:
  1–4 hours.
- 🆘 **[Help wanted](https://github.com/klein-business/legal-text-mcp-de/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)** —
  larger items where outside expertise would speed things up (extra
  jurisdictions, alternative deployment recipes, integration recipes for new
  MCP clients).

**Workflow for first-time contributors:**

1. Comment on the issue to claim it (avoids two people working in parallel).
2. Fork → branch off `main` using `feat/<topic>` / `fix/<topic>` / `docs/<topic>`.
3. `uv sync --all-groups && uv run --group dev pytest` to confirm a green baseline.
4. Implement → add tests → `uv run --group dev ruff check . && ruff format .`.
5. Commit with `git commit -s` (DCO sign-off — see below) and push.
6. Open a PR — CI runs ~16 checks; turnaround on review is usually <48 h.

If anything is unclear, post in the issue or in [Q&A Discussions](https://github.com/klein-business/legal-text-mcp-de/discussions/categories/q-a).
No question is too small.

## Architecture tour

Five-minute mental map before you change code:

```
src/legal_text_mcp_de/
├── cli/                # Typer CLI (14 subcommands)
│   ├── _lookups.py     #   read-only commands: laws, law, norm, cite, …
│   ├── _server.py      #   `serve` (MCP) and `http` (FastAPI)
│   ├── _corpus.py      #   `corpus pull/verify/info` (ORAS-backed)
│   └── …
├── http_api.py         # FastAPI app (mirrors the MCP tool surface)
├── http_models.py      # Pydantic v2 schemas — single source of truth for
│                       # both HTTP and CLI JSON envelopes
├── server.py           # MCP server entry point (delegates to legal_texts/)
├── config.py           # pydantic-settings — all env-driven config
└── legal_texts/        # Domain core: loading, parsing, search, citing
    ├── models.py       #   normalised data model (Law, Norm, Source, …)
    ├── sources/        #   one adapter per upstream feed
    ├── search.py       #   rapidfuzz-backed search
    └── citation.py     #   citation parser + resolver
```

The **MCP tools**, **HTTP routes**, and **CLI subcommands** all delegate to the
same underlying `LegalTextRuntime`. So a fix in `legal_texts/` automatically
benefits all three surfaces — and one new HTTP route gets a CLI subcommand by
adding ~30 lines in `cli/_lookups.py`.

Full module-level documentation lives at
[docs/modules/](https://klein-business.github.io/legal-text-mcp-de/modules/cli/).

## Development setup

Requires Python 3.12 or 3.13 and [`uv`](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/klein-business/legal-text-mcp-de.git
cd legal-text-mcp-de
uv sync --all-groups
uv run --group dev pre-commit install        # optional but recommended
uv run --group dev pytest
```

### Justfile shortcuts (optional)

The repository ships a [`Justfile`](Justfile) with thin wrappers around
the canonical `uv` invocations. Install [`just`](https://just.systems/)
(`brew install just`) and run any of:

```bash
just                    # list all targets
just install            # uv sync --all-groups
just test               # uv run --group dev pytest
just lint               # ruff check + format --check
just fix                # ruff check --fix + format
just typecheck          # mypy scripts/
just docs               # mkdocs serve at localhost:8000
just run                # MCP server on fixture corpus
just api                # HTTP API on :8080 on fixture corpus
just verify-release     # the same release-gate the CI runs
```

The Justfile is a documentation artefact — using `uv` directly is
always equivalent. CI only invokes `uv`, never `just`.

## Branch and PR conventions

- Branch names: `feat/<short-description>`, `fix/<short-description>`,
  `chore/<short-description>` — no GitHub username prefix.
- PR titles must follow [Conventional Commits](https://www.conventionalcommits.org):
  `feat: ...`, `fix: ...`, `chore: ...`, `refactor: ...`, `docs: ...`,
  `test: ...`, `ci: ...`, `perf: ...`, `build: ...`, `style: ...`.
- Every commit must carry a `Signed-off-by:` trailer (DCO). Use
  `git commit -s` (or configure `commit.gpgsign true` plus a matching
  identity).

## Tests and quality gates

- Every new feature, bug fix, or refactor must include corresponding
  tests. Run the full suite before submitting:
  `uv run --group dev pytest mcp/tests`.
- Linting: `uv run --group dev ruff check .` and
  `uv run --group dev ruff format --check .`.
- Type-checking on `scripts/`: `uv run --group dev mypy scripts`.
- Coverage floor is enforced in CI via
  `[tool.coverage.report] fail_under` in `pyproject.toml`.

## Issue before PR for non-trivial work

For larger changes (new MCP tools, schema changes, architectural
adjustments), please open an issue first to discuss approach. Small
fixes and clear improvements can go directly to a PR.

## Licence

By contributing you agree that your contributions are licensed under
the [Apache License 2.0](LICENSE).
