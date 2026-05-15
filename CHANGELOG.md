# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Re-licensed from proprietary commercial to Apache License 2.0.
- Established `LICENSE` (Apache-2.0), `NOTICE` with upstream attribution
  and data-source statements, `AUTHORS.md`, and `CHANGELOG.md`.
- Preserved upstream MIT licence terms for code derived from
  `floleuerer/deutsche-gesetze-mcp` in `licenses/MIT-floleuerer.txt`.
- Rewrote `README.md` in English with disclaimers and an OSS-focused
  structure.
- Updated `pyproject.toml` metadata (Apache-2.0 SPDX license,
  `requires-python = ">=3.12"`, project URLs, PyPI classifiers).
- Updated the README banner asset to display the Apache-2.0 badge.
- Hardened CI into eight workflows (ci, e2e, codeql, scorecard,
  dependency-review, commitlint, dco, megalinter).
- Configured mypy stufenweise: strict on `scripts/`, plain (warning-only)
  on `mcp/`.
- Coverage floor enforced via `[tool.coverage.report] fail_under` in
  `pyproject.toml` (set to 86%, the measured baseline).
- Switched `detect-secrets` pin from `~=1.5` to `~=1.5.0` (consistency
  with project convention).
- `verify_pre_flip.py` extended from 5 to 8 checks
  (`check_workflow_set`, `check_required_status_checks`,
  `check_branch_protection`); secrets-check now returns `SKIP` (rather
  than `FAIL`) when `detect-secrets-hook` is missing from PATH.
- Fixed `[Unreleased]` compare link in `CHANGELOG.md` to point at the
  initial commit rather than `HEAD`.
- Retired `scripts/verify_ci_workflow.py` (superseded by
  `verify_pre_flip.check_workflow_set`).

### Added

- `scripts/verify_pre_flip.py` and `mcp/tests/test_verify_pre_flip.py` —
  gate that asserts the repository is ready for public visibility.
- `.secrets.baseline` and `detect-secrets` dev dependency for the
  secrets-scan gate.
- `SECURITY.md` — vulnerability disclosure policy and supported-versions
  table.
- `.pre-commit-config.yaml` — developer-convenience hooks mirroring CI.
- `scripts/check_spdx_header.py` — pre-commit hook ensuring new Python
  files carry the SPDX header.
- `.commitlintrc.json` — Conventional Commits configuration applied to
  PR titles.
- `docs/operations/coverage-baseline-phase2.md` — coverage baseline
  evidence.
- New dev dependencies: `mypy~=1.13.0`, `pytest-cov~=6.0.0`,
  `pre-commit~=4.0`.

[Unreleased]: https://github.com/klein-business/legal-text-mcp-de/compare/e510e4b...HEAD
