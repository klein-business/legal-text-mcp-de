## Summary

<!-- One or two sentences describing what this PR changes. -->

## Type of change

- [ ] Bug fix (`fix:`)
- [ ] New feature (`feat:`)
- [ ] Refactor (`refactor:`)
- [ ] Documentation (`docs:`)
- [ ] Tests (`test:`)
- [ ] CI/build (`ci:` / `build:`)
- [ ] Chore (`chore:`)
- [ ] Performance (`perf:`)
- [ ] Style (`style:`)

## Checklist

- [ ] PR title follows Conventional Commits (e.g. `feat: add foo`).
- [ ] All new and existing tests pass locally
      (`uv run --group dev pytest mcp/tests`).
- [ ] Code is formatted and linted
      (`uv run --group dev ruff check .` and
      `uv run --group dev ruff format --check .`).
- [ ] Mypy strict passes on `scripts/`
      (`uv run --group dev mypy scripts`).
- [ ] Every commit is signed off (`git commit -s`).
- [ ] User-visible changes are noted in `CHANGELOG.md` under
      `## [Unreleased]`.
- [ ] Documentation is updated where relevant (docs/ pages,
      tool references, MCP/HTTP examples).

## Related issues

<!-- Fixes #123, or "n/a" -->

## Test plan

<!-- How can a reviewer verify this works? Commands, scenarios. -->
