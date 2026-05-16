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

## Development setup

Requires Python 3.12 or 3.13 and [`uv`](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/klein-business/legal-text-mcp-de.git
cd legal-text-mcp-de
uv sync --all-groups
uv run --group dev pre-commit install        # optional but recommended
PYTHONPATH=mcp uv run --group dev pytest mcp/tests -v
```

After the source rename (Section F of the public-release programme),
`PYTHONPATH=mcp` is no longer required; `uv run pytest` is sufficient.

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
