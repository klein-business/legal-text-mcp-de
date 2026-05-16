# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Source layout migrated from `mcp/` (PYTHONPATH hack) to
  `src/legal_text_mcp_de/` (hatchling src-layout). The runtime now
  installs via `uv pip install -e .` or `uvx legal-text-mcp-de`.
- Build system switched to hatchling with PEP 517 `[build-system]`
  metadata in `pyproject.toml`. `[tool.uv] package = false` removed.
- Project entry point added: `legal-text-mcp-de = legal_text_mcp_de.server:main`.
- Mypy strict ratcheted onto five `mcp/` modules: `config`,
  `http_models`, `legal_texts.errors`, `legal_texts.models`,
  `legal_texts.sources`.
- Coverage floor raised from 86 to 88 after closing gaps on
  `normalizer.py` (0→100%) and `parser.py` (61→90%).
- DCO workflow now verifies every commit in a PR (not only HEAD).
- ruff version skew resolved: pinned in `pyproject.toml` (~=0.15.0);
  pre-commit uses the uv-installed binary.
- Pre-Phase-2 Python files all carry the SPDX-License-Identifier
  header; exempt list reduced to comments only.
- `verify_full_corpus_bundle.py`: 42 `union-attr` ignores replaced
  with typed intermediates via `_as_dict` helper.
- pyproject `Homepage` URL now points at the documentation site
  (`https://klein-business.github.io/legal-text-mcp-de`).
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
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`,
  `GOVERNANCE.md`, `ROADMAP.md` — community-health files.
- `.github/CODEOWNERS`,
  `.github/ISSUE_TEMPLATE/{bug_report,feature_request,config}.yml`,
  `.github/PULL_REQUEST_TEMPLATE.md`.
- `.github/dependabot.yml` — weekly updates for pip, github-actions,
  docker ecosystems.
- mkdocs-material documentation site under `docs/`, deployed to
  GitHub Pages on push to `main` and on each release tag via
  `mike`. 35 pages covering quickstart, concepts, MCP tools, HTTP
  API, operations (security, SBOM, cosign-verify, versioning,
  threat model, OpenSSF application, launch procedure, SLSA),
  contributing, and community.
- `.github/workflows/{release,release-please,docs,gitleaks,trivy}.yml`
  for the release pipeline (PyPI Trusted Publisher + multi-arch GHCR
  with cosign + SBOM + SLSA-3), release-please version PR, mkdocs
  deploy, gitleaks scan, Trivy image scan.
- `.release-please-config.json`, `.release-please-manifest.json`.
- `.trivyignore` (initially empty with header comment).
- Docker hardening: digest-pinned base image, non-root USER 10001,
  HEALTHCHECK, multi-arch buildx config in release.yml.
- `cyclonedx-bom` dev dependency for Python SBOM generation; syft +
  cosign documented for local OCI SBOM/signature work.
- `verify_pre_flip.py` extended from 8 to 11 checks:
  `check_release_workflow_present`, `check_pypi_name_reserved`,
  `check_security_settings`.
- New dependency group `docs` with mkdocs-material plus plugins.
- New dev dependencies: `ruff~=0.15.0`, `cyclonedx-bom~=5.0`.
- New tests: `tests/test_normalizer.py` (6 tests),
  `tests/test_parser_branches.py` (18 tests), plus expanded
  `test_verify_pre_flip.py` (now 41 tests).

[Unreleased]: https://github.com/klein-business/legal-text-mcp-de/compare/e510e4b...HEAD
