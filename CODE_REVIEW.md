<!--
SPDX-License-Identifier: Apache-2.0
Copyright 2026 klein-business
-->

# Code Review Policy

This document defines what a code review covers for `legal-text-mcp-de` and
how reviews are conducted. It supplements [`CONTRIBUTING.md`](CONTRIBUTING.md)
and is referenced by the OpenSSF Best Practices Gold criterion
`code_review_standards`.

## Scope

Every change to `main` goes through a pull request that triggers the full CI
matrix. The 14 required status checks on `main` (see branch protection) gate
mergeability: lint, type-check, tests on Python 3.12 + 3.13, lockfile
integrity, build, MegaLinter, release gate, uv runtime + Docker, CodeQL,
dependency review, Gitleaks, DCO, and PR-title (Conventional Commits).

Beyond the automated gates, a human reviewer (or the maintainer's own
self-review pass before merging) checks the items listed below.

## Mandatory review checklist

A pull request is **only mergeable** when all of these items have been
verified by a reviewer (and recorded in the PR conversation when not
obvious from the diff).

### Correctness

- The change does what the PR description says.
- New behaviour is covered by tests (`tests/` adds or modifies cases).
- Edge cases have tests: empty input, missing source, malformed corpus,
  validation failure, concurrent access where relevant.
- Existing tests still pass on Python 3.12 and 3.13.

### API and contract stability

- No breaking change to the public Python API (`legal_text_mcp_de.*`),
  the MCP tool schema, the HTTP API surface (`/health`, `/api/*`,
  `/mcp/*`), the CLI entry point `legal-text-mcp-de`, or the container
  command/healthcheck — unless the PR title is `feat!:` and the
  `CHANGELOG.md` has a *BREAKING CHANGES* entry.
- Configuration changes (env variables, `DATASET_PATH`,
  `STRICT_STARTUP`, etc.) are documented in `README.md` and the docs
  site.

### Security

- No new dependency that is unmaintained, has known CVEs, or is not
  Apache-2.0 / MIT / BSD compatible.
- Untrusted input is validated at the boundary (pydantic models for
  HTTP, MCP tool argument schemas, env via pydantic-settings).
- No secrets, tokens, API keys, or service credentials are committed
  (Gitleaks gates this; manual inspection of `.env*`, fixtures, and
  test outputs).
- CodeQL findings on the PR are triaged. Any suppression has a
  comment justifying why the finding is a false positive.
- Cryptographic primitives use stdlib or established FLOSS libraries.
  No custom crypto.
- File I/O paths are validated when they originate from user input
  (no traversal into `/etc` etc.).

### Quality

- The diff conforms to ruff (style + lint) and mypy strict (for files
  in the strict-typed set: `scripts/` and the 5 strict-typed `mcp/`
  modules). CI enforces this.
- Public functions and classes have docstrings sufficient for
  `mkdocstrings` to render meaningful reference docs.
- New modules carry the SPDX header (`# SPDX-License-Identifier:
  Apache-2.0` and the copyright line) — `verify_pre_flip.py` and the
  pre-commit hook flag missing headers.
- No commented-out code, no `print()` debug noise, no leftover `TODO`
  without an issue reference.
- Test names describe the behaviour, not the implementation.

### Performance and resource use

- For changes touching the parser, normalizer, or search path:
  benchmark numbers in the PR description (or a comment) so
  regressions are visible.
- New runtime dependencies are justified; their footprint is checked
  against the existing `uv.lock` resolution.

### Documentation

- User-facing changes update `README.md`, the docs site
  (`docs/`), or the `CHANGELOG.md` — whichever applies.
- Architectural changes update `GOVERNANCE.md` or
  `docs/superpowers/specs/` if a design decision is encoded.
- New public symbols are picked up by mkdocstrings; reference page
  renders without warnings.

### Operational concerns

- The Dockerfile still builds (the `uv runtime and Docker` job gates
  this).
- E2E tests (`e2e.yml`) pass: the container starts, `/health` returns
  200, the MCP transport accepts a tool call.
- The release workflow (`release.yml`) is not broken by the PR —
  pin updates to actions are checked against published SHAs.

## How reviews are conducted

1. The author opens a PR with a self-review note in the description:
   "Self-reviewed against `CODE_REVIEW.md`. The following items are
   covered: …". This is the baseline expectation; it is **not**
   sufficient by itself when an external reviewer is available.

2. A reviewer who is not the author reads the diff, runs the change
   locally where the diff is non-trivial (≥50 lines or touches the
   parser/normalizer/security path), and confirms the checklist
   items relevant to the change.

3. Comments are inline. Required changes use GitHub's *Request
   changes* status. Suggestions use *Comment*. *Approve* means: "I
   have run through the checklist and I am comfortable that this is
   ready to merge".

4. The maintainer (`klein-business`) squash-merges the PR after
   approval. The squash-merge commit is automatically SSH-signed by
   GitHub's bot and counts as a verified commit on `main`.

5. For trivial changes (one-line typo fix, dependency-bump Dependabot
   PRs), self-review is acceptable. The bypass-allowlist on `main`
   protection allows the maintainer to merge without a second
   approval in that case. The maintainer still records the
   self-review in the merge commit message.

## Reviewer-author independence

The OpenSSF Gold criterion `two_person_review` asks that at least 50%
of proposed modifications are reviewed by someone other than the
author before release. As of v1.0.0, `legal-text-mcp-de` is a
solo-maintainer project. The maintainer:

- Treats every PR as a code review against this document,
  self-reviewing in the PR description.
- Welcomes co-maintainer onboarding (see `GOVERNANCE.md`).
- Tracks externally contributed PRs separately; each one that is
  merged increments the two-person-review ratio.

Once a second maintainer is on board, the bypass-allowlist will be
removed in favour of standard required-approval review.

## Tooling that automates parts of this checklist

| Item | Tool / workflow |
|---|---|
| Style / lint | `ruff` (CI `Lint (ruff)`) |
| Type safety | `mypy --strict` for `scripts/` + 5 `mcp/` modules (CI `Mypy strict (scripts)`) |
| Tests Py3.12 / Py3.13 | `pytest` (CI `Test (py3.12)`, `Test (py3.13)`) |
| Coverage floor | `pytest --cov` with `fail_under` in `pyproject.toml` |
| Lockfile integrity | `uv lock --check` (CI `Lockfile integrity`) |
| Build | `uv build` (CI `Build (sdist + wheel)`) |
| Static analysis | CodeQL extended-suite (CI `CodeQL analysis (python)`) |
| Container security | Trivy image scan (CI `Trivy` — informational) |
| Secrets | Gitleaks (CI `Gitleaks scan`) + GitHub secret scanning |
| Dependency review | GitHub dependency-review-action (CI `Dependency review`) |
| Commit message format | commitlint (CI `PR title (Conventional Commits)`) |
| DCO sign-off | tim-actions/dco (CI `DCO sign-off check`) |
| Cross-language linting | MegaLinter (CI `MegaLinter`) |
| Release smoke test | Fixture-backed release gate (CI `Release gate (fixture-backed)`) |
| Runtime smoke test | uv + Docker container check (CI `uv runtime and Docker`) |
