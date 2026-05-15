---
type: design
topic: public-release-phase-2-ci-hardening
date: 2026-05-15
status: review
---

# Public Release — Phase 2 (CI/CD Hardening) Design Amendment

## Decision

Phase 2 of the public-release programme implements Pillar 3 (CI/CD
Hardening & Quality Gates) of the parent design
[2026-05-15-public-release-enterprise-readiness-design.md](2026-05-15-public-release-enterprise-readiness-design.md),
plus a curated set of adjustments surfaced by the Phase 1
implementation. The phase produces a hardened multi-workflow CI
topology with quality gates, a SECURITY.md activating GitHub's
private vulnerability reporting, pre-commit hooks for developer
convenience, and an extended `verify_pre_flip.py` gate that asserts
the workflow set, required status checks, and branch-protection
configuration.

The repository remains private at the end of Phase 2. Public-flip
happens after Phase 4.

## Strategic Inputs (User-Confirmed)

| Decision | Choice |
| --- | --- |
| Carryover bundle | "Empfohlen": C-1, C-3, C-4, C-5, C-6 included; C-2 SPDX only for new files via pre-commit |
| Mypy adoption | Stufenweise — strict on `scripts/` immediately; plain mypy on `mcp/` as warning-only gate; per-module ratchet to strict in follow-up PRs |
| Commitlint scope | PR-title only; allowed types: feat, fix, chore, refactor, docs, test, ci, perf, build, style |
| CI matrix | Python 3.12 and 3.13 on `ubuntu-latest` (Linux-only) |
| SECURITY.md timing | Pulled forward from Phase 3 into Phase 2 because `pyproject.toml` already references `/security/policy` |

## What Stays from Pillar 3

The following Pillar-3 commitments carry through Phase 2 unchanged:

- Workflow topology: `ci.yml` (refactor), `e2e.yml`, `codeql.yml`,
  `scorecard.yml`, `dependency-review.yml`, `commitlint.yml`,
  `dco.yml`, `megalinter.yml` (expansion).
- `ci.yml` five-job structure: lint, typecheck, test, lock-integrity,
  build.
- Pre-commit hook set: ruff (check + format), mypy, `detect-secrets`,
  `markdownlint-cli2`, `actionlint`, `shellcheck`.
- Required status checks on `main` branch protection: all CI jobs +
  CodeQL + Scorecard + DCO + Dependency-Review + Commitlint +
  MegaLinter + E2E.
- `verify_pre_flip.py` Phase-2 extensions: workflow-set assertion,
  required-status-check assertion, branch-protection assertion via
  GitHub API.

## What Changes vs. Pillar 3

| Adjustment | Pillar 3 (original) | Phase 2 (this amendment) | Rationale |
| --- | --- | --- | --- |
| Mypy strict | `mcp/` and `scripts/` strict from day one | **Stufenweise**: `scripts/` strict; `mcp/` plain-mypy as warning-only gate; per-module ratchet planned | Avoids turning Phase 2 into a typing marathon; preserves Tier-C goal as a ratchet |
| Commitlint | "Conventional Commits enforcement" (unspecified scope) | **PR-title only**, fixed type allowlist (10 entries) | Low-friction for contributors; squash-merge maps PR title to commit anyway |
| SECURITY.md | Phase 3 (Pillar 2) | **Phase 2** | `pyproject.toml` already references `/security/policy`; without the file the URL 404s |
| SPDX headers | Not specified | **Pre-commit hook for new files**; full retrofit deferred | Sets the standard going forward without a large one-time touch |
| CHANGELOG link | Not specified | `[Unreleased]: …/compare/HEAD` → `compare/<initial-sha>...HEAD` | Removes the no-op diff that Keep-a-Changelog linters would flag |
| Secrets-check UX | FAIL when tool missing | **SKIP** result when `detect-secrets-hook` not on PATH | Distinguishes "environment misconfigured" from "secret found" |
| `detect-secrets` pin | `~=1.5` | `~=1.5.0` | Consistency with `PyYAML~=6.0.1`, `requests~=2.33.0` |

## SECURITY.md Content Scope

SECURITY.md adopts the Pillar-2 design from the parent spec verbatim,
adjusted only for the pre-`v1.0.0` lifecycle:

- Reporting channel: GitHub Security Advisories (private vulnerability
  reporting), with `martin@klein.business` as the documented backup.
- Response SLA: 5 business days acknowledgement; 90 days coordinated
  disclosure.
- Supported-versions table: initial entry `v1.x — supported
  (pre-release)`, with a note that the stability contract begins at
  `v1.0.0`.
- CVE assignment: via GitHub as CNA.
- Verification snippet placeholder for signed releases (full `cosign
  verify` text lands in Phase 4 alongside the actual signing
  pipeline).

GitHub repo setting: enable Private Vulnerability Reporting (Settings
→ Security → Code security and analysis). Captured in the Phase 2
plan as a manual step with a verification command.

## Workflow Topology (Final for Phase 2)

```
.github/workflows/
├── ci.yml                # PR + push: lint, typecheck, test, lock, build
├── e2e.yml               # PR + push + nightly: verify_release.py + verify_e2e.py
├── codeql.yml            # PR + weekly: Python SAST
├── scorecard.yml         # weekly: OpenSSF Scorecard (SARIF + README badge)
├── dependency-review.yml # PR: GitHub Dependency Review
├── commitlint.yml        # PR: Conventional-Commits PR-title check
├── dco.yml               # PR: DCO sign-off check
└── megalinter.yml        # PR + push: MegaLinter (expanded scope)
```

Phase 4 will add `release.yml` and `docs.yml`. They are explicitly out
of scope for Phase 2.

## `ci.yml` Job Detail

| Job | Command | Notes |
| --- | --- | --- |
| lint | `uv run ruff check . && uv run ruff format --check .` | Existing ruff config; no new rules |
| typecheck-strict | `uv run --group dev mypy scripts` | Strict profile; blocks PRs |
| typecheck-warn | `uv run --group dev mypy mcp \|\| true` | Non-blocking; output captured as GH Action annotation; cap to first 50 findings |
| test | `uv run --group dev pytest --cov=mcp --cov-report=xml --cov-fail-under=<floor>` | Matrix on Python 3.12 + 3.13; coverage floor computed once at Phase-2 start |
| lock-integrity | `uv lock --check` | Catches uncommitted lockfile drift |
| build | `uv build` | Produces sdist + wheel; uploaded as artefacts for downstream Phase-4 release-gate inspection |

`pyproject.toml` mypy section (added in Phase 2):

```toml
[tool.mypy]
python_version = "3.12"
files = ["scripts", "mcp"]

[[tool.mypy.overrides]]
module = "scripts.*"
strict = true

[[tool.mypy.overrides]]
module = "mcp.*"
# Per-module ratchet to strict planned. Currently plain mypy as warning-gate.
ignore_errors = false
```

Coverage floor: `[tool.coverage.report] fail_under = <max(85, measured-baseline)>`.

## Pre-commit Hook Set

`.pre-commit-config.yaml` (new in Phase 2):

| Hook | Repo / Version pin | Purpose |
| --- | --- | --- |
| `ruff-check` | `astral-sh/ruff-pre-commit` (latest stable) | Lint |
| `ruff-format` | same | Format check |
| `mypy` | `pre-commit/mirrors-mypy` (latest stable) | Type-check (matches CI scope) |
| `detect-secrets` | `Yelp/detect-secrets` matching `~=1.5.0` | Secrets scan against baseline |
| `markdownlint-cli2` | `DavidAnson/markdownlint-cli2` (latest stable) | Markdown linting |
| `actionlint` | `rhysd/actionlint` (latest stable) | GitHub Actions workflow lint |
| `shellcheck` | `koalaman/shellcheck-precommit` (latest stable) | Bash scripts in `prepare_data/` |
| `spdx-license-header` | local hook script | Adds `# SPDX-License-Identifier: Apache-2.0` to new `.py` files |

CI does not invoke `pre-commit run --all-files` as a separate job; the
individual hooks' equivalent CI jobs (`ci.yml`, `megalinter.yml`) are
authoritative. Pre-commit is a developer-convenience layer. Required
status checks point at the CI jobs, not at pre-commit.

## Commitlint Configuration

`.commitlintrc.json` (new in Phase 2):

```json
{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "type-enum": [
      2, "always",
      ["feat", "fix", "chore", "refactor", "docs", "test", "ci", "perf", "build", "style"]
    ],
    "subject-case": [2, "never", ["upper-case", "pascal-case", "start-case"]],
    "header-max-length": [2, "always", 100]
  }
}
```

Workflow `commitlint.yml` scans PR title only via
`wagoid/commitlint-github-action@v6` with `configFile: .commitlintrc.json`.
Dependabot is compatible out-of-the-box (uses `chore(deps): …`).

## DCO Enforcement

Workflow `dco.yml` uses `tim-actions/dco` (pinned by SHA at
implementation time) to verify each commit on the PR carries a
`Signed-off-by:` trailer. The check is a required status check on
`main`. `CONTRIBUTING.md` (Phase 3) will document `git commit -s`
usage; for Phase 2 the user (solo maintainer) sets `git config commit.gpgsign true`
locally and ensures all commits made from Phase 2 onward carry the
sign-off trailer. Pre-Phase-2 commits are exempt (the DCO check
inspects only the PR's own commits).

GPG-signed commits are independently required by branch protection
(`required_signatures = true`, planned as a Phase 2 enable step;
currently `false` on origin). Sign-off and GPG signing are two
separate mechanisms; both are required.

## `verify_pre_flip.py` Extensions

Three new checks added on top of the existing five:

| Check | Purpose | Failure mode |
| --- | --- | --- |
| `check_workflow_set` | `.github/workflows/` contains expected set (ci, e2e, codeql, scorecard, dependency-review, commitlint, dco, megalinter); no unexpected files | FAIL listing missing/extra |
| `check_required_status_checks` | Branch protection on `main` requires all expected checks | FAIL listing missing checks; requires GitHub API token |
| `check_branch_protection` | `enforce_admins = true`, `required_linear_history = true`, `allow_force_pushes = false` on `main` | FAIL listing the failing rules |

Tests use `pytest-httpserver` or `responses` library to stub the GitHub
API for unit tests; an integration test runs against the real
`api.github.com` when `VERIFY_GITHUB_TOKEN` is set.

The Phase 1 secrets-check `check_no_unaudited_secrets` is amended:
when `detect-secrets-hook` is missing from PATH, the check returns a
new `SKIPPED` result type (neither PASS nor FAIL), with the message
"detect-secrets-hook not on PATH". The CLI report renders `[SKIP]`
instead of `[FAIL]`. The aggregator returns exit code 0 if all checks
are PASS or SKIPPED (no FAILED).

## Out of Scope for Phase 2

- SPDX retrofit on existing Python sources (only new files via
  pre-commit hook are enforced)
- Mypy strict on `mcp/` (planned as per-module ratchet in follow-up
  PRs, with a tracking issue created at Phase-2 close)
- All Pillar-4 items: Dependabot config, OpenSSF Best Practices
  application, SBOM, SLSA, cosign, container hardening
- Pillar-2 community-health files except SECURITY.md (CONTRIBUTING,
  CODE_OF_CONDUCT, SUPPORT, GOVERNANCE, ROADMAP, CODEOWNERS, issue
  and PR templates remain Phase 3)
- mkdocs documentation site (Phase 3)
- `release.yml` and `docs.yml` workflows (Phase 4)
- Build-backend migration from `[tool.uv] package = false` to
  hatchling (Phase 4)
- README badge additions for CI/Coverage/Scorecard (badges added in
  Phase 4 alongside actual workflow stability)

## Acceptance Criteria (Phase 2)

1. All eight workflows configured (eight files in
   `.github/workflows/`); a synthetic test PR runs all of them, all
   green.
2. Coverage baseline measured (record in
   `docs/operations/coverage-baseline-phase2.md` as evidence); floor
   `max(85, baseline)` enforced via `[tool.coverage.report]
   fail_under`.
3. Mypy strict run passes on `scripts/`; plain-mypy run on `mcp/`
   reports findings as non-blocking CI annotations capped at 50.
4. Pre-commit hook set runs cleanly on a freshly checked-out
   workspace via `uv run --group dev pre-commit run --all-files`
   (allowed exceptions documented).
5. SECURITY.md present; GitHub Security Advisory tab activated; a
   test report from a separate account triggers an acknowledgement
   to `martin@klein.business`.
6. `verify_pre_flip.py` reports 8/8 PASS (5 existing + 3 new) on the
   real repository.
7. Branch-protection rules tightened: `commitlint`, `dco`,
   `codeql`, `scorecard`, `dependency-review`, `megalinter`, `e2e`,
   and all `ci.yml` matrix jobs are required status checks;
   `required_signatures` enabled; this is asserted programmatically
   by `check_required_status_checks` and `check_branch_protection`.
8. Python 3.13 matrix passes; if it fails for an environmental
   reason, document and either fix or restrict
   `requires-python` with a written rationale.
9. CHANGELOG `[Unreleased]` entry updated with all Phase 2 changes
   and `[Unreleased]` compare link fixed.

## Risks

| # | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| P2-1 | Coverage baseline surprisingly low (< 80%) | medium | medium | Plan a "test-gap-audit" follow-up PR; floor = `max(85, baseline + 1pp)` as backstop |
| P2-2 | Mypy plain on `mcp/` produces large finding count, noisy CI logs | medium | low | Cap annotations to 50 findings; per-module allowlist allows initial silencing where false positives dominate |
| P2-3 | Commitlint blocks Dependabot PRs (regex mismatch) | low | medium | Verify with a manual test PR titled `chore(deps): bump X from Y to Z` before enabling required check |
| P2-4 | Phase 3.13 matrix breakage due to upstream library | medium | low | Pin specific minor of any broken dep; document and ratchet later; do not block Phase 2 close on this |
| P2-5 | Pre-commit hook installation friction for contributors | low | low | Document install steps in (future) CONTRIBUTING.md; CI is the authoritative gate so pre-commit is opt-in |
| P2-6 | `verify_pre_flip` Phase-2 checks require GitHub API token; CI/local mismatch | medium | low | Make GitHub-API checks optional (skip without token); document `VERIFY_GITHUB_TOKEN` env in `docs/operations/` |
| P2-7 | SECURITY.md private-vulnerability-reporting setting forgotten as manual step | low | medium | Phase-2 plan ends with explicit manual-step checklist; `verify_pre_flip` (when token set) queries `repos/{owner}/{repo}` for `security_and_analysis.secret_scanning.status` etc. |

## Open Items Carried Into the Implementation Plan

- Coverage baseline (measured at Phase-2 start)
- Specific GitHub Action version pins for new workflows (latest stable
  at implementation time)
- `scorecard.yml` minimum-permissions configuration
- `megalinter.yml` expanded linter set (proposed:
  `MARKDOWN_MARKDOWNLINT2`, `ACTION_ACTIONLINT`, `JSON_JSONLINT`;
  finalized at implementation time)
