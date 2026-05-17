# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-05-17

### Added — MCP capabilities

#### Tier 2 — Resources (~10 URIs under `legal://`)
- `legal://laws` (paginated JSON list with cursor + limit)
- `legal://laws/{code}`, `legal://laws/{code}/full` (Markdown)
- `legal://laws/{code}/norms/{norm_id}` (Markdown), `.../relationships` (JSON)
- `legal://laws/{code}/source` (JSON provenance)
- `legal://corpus/coverage`, `legal://corpus/limitations`, `legal://corpus/manifest` (JSON)

#### Tier 3 — Prompts (5 curated slash-workflows)
- `/rechtsfrage`, `/zitation-checken`, `/norm-erklaeren`, `/recherche`, `/dsgvo-check`

#### Tier 4 — Sampling helpers
- `safe_sample` with timeout, retry, schema validation
- Error hierarchy + `MockSamplingClient` for testing

#### Tier 5 — `research_topic` Smart Tool
- Multi-step recherche with 2 sampling calls (LLM ranking + synthesis)
- Graceful degradation when client lacks sampling
- Progress reports via `ctx.report_progress`

### Added — Corpus
- Expanded from 5 to ~8500 laws (federal + top-5 Länder + 5 EU acts)
- Signed `.tar.zst` distribution via GHCR OCI artifact + GitHub Releases

### Added — Hosting
- Optional public-hosted MCP service at `mcp.klein.business/legal/de`
- Caddy + TLS + CSP/HSTS security headers
- Rate limiting (per-IP + per-bearer-token)
- Anonymised logging (no bodies, no PII)
- Prometheus metrics endpoint
- Privacy + ToS HTML pages
- Blue-green deploy script

### Changed
- `get_corpus_coverage` schema bumped v1 → v2 with new aggregate counts (old fields preserved)
- `DATASET_PATH` unset is now allowed (auto-downloads); set `STRICT_DATASET=true` for old behaviour
- Coverage gates raised to 92% statement / 82% branch

### Compatibility
- All 9 v1 tools unchanged (signatures + return shapes frozen by `tests/test_v1_compat.py`)
- HTTP API surface unchanged
- See `docs/operations/migration-v1-v2.md`

### Statistics
- 80+ tasks across 7 phases (A: Corpus, B: Resources, C: Prompts, D: Sampling, E: research_topic, F: Hosting, G: Polish)
- ~80 commits, all SSH-signed
- 485+ tests passing, 92%+ statement coverage, 82%+ branch coverage

## [2.0.0-rc.4] - 2026-05-17

### Added
- **Tier 5 — research_topic Smart Tool:** multi-step legal research with 2 sampling calls per invocation
  - Step 1: corpus search via `runtime.search_laws`
  - Step 2: hydrate norm text via `runtime.get_norm`
  - Step 3: LLM ranking of candidates by relevance (sampling call)
  - Step 4: related-norms graph loading
  - Step 5: LLM synthesis of research report (sampling call)
  - Graceful degradation when client lacks sampling
  - Progress reports via `ctx.report_progress`
- `tools/research_models.py`: `ResearchReport`, `RankedNorm` pydantic schemas
- `tools/research_prompts.py`: `build_ranking_prompt`, `build_synthesis_prompt`
- CI smoke workflow `.github/workflows/research-topic-smoke.yml` (cost-capped Haiku, opt-in via `smoke-test` environment)

## [2.0.0-rc.3] - 2026-05-17

### Added
- **Tier 4 — Sampling infrastructure:** `safe_sample` helper with timeout, retry, schema validation, and graceful degradation paths for clients that lack sampling support.
- Error hierarchy: `SamplingError`, `SamplingNotSupported`, `SamplingTimeout`, `SamplingRefused`, `SchemaValidationError`.
- Pydantic schemas: `SampleResult`, `RankingEntry`, `RankingResult` (with `top_n()` helper).
- `MockSamplingClient` for deterministic tests of smart tools (used by Phase E `research_topic` E2E).

## [2.0.0-rc.2] - 2026-05-17

### Added
- **Tier 3 — MCP Prompts:** 5 curated slash-workflows
  - `/rechtsfrage` — answer a German legal question with exact citations
  - `/zitation-checken` — resolve a citation and format the result with Stand-Datum
  - `/norm-erklaeren` — load a norm + relationships, plain-language explanation
  - `/recherche` — multi-step recherche (placeholder for E5 research_topic smart tool)
  - `/dsgvo-check` — walk through GDPR Art. 5, 6, 7, 9, 13, 14 against an activity

## [2.0.0-rc.1] - 2026-05-17

### Added
- **Tier 2 — MCP Resources:** 10 read-only URIs under `legal://`
  - `legal://laws` (paginated JSON list, cursor + limit via path components)
  - `legal://laws/page/{cursor}/{limit}` (explicit page access)
  - `legal://laws/{code}` (Markdown law header + norm index)
  - `legal://laws/{code}/full` (full law as Markdown)
  - `legal://laws/{code}/norms/{norm_id}` (Markdown single norm)
  - `legal://laws/{code}/norms/{norm_id}/relationships` (JSON related-norm graph)
  - `legal://laws/{code}/source` (JSON provenance)
  - `legal://corpus/coverage`, `legal://corpus/limitations`, `legal://corpus/manifest` (JSON corpus-wide)
- `resources/markdown_render.py`: pure renderers `render_norm()`, `render_law()`
- `tools/` module: 9 v1 MCP tools moved out of `server.py` into `tools/v1_tools.py` (`register_v1_tools(app, runtime)`); behaviour unchanged

### Changed
- `server.py` slimmed to orchestration only (registers tools + resources)

### Compatibility
- v1 MCP tool contract frozen in `tests/test_v1_compat.py` — all 9 tool names + signatures unchanged
- HTTP API surface unchanged

## [1.5.0] - 2026-05-17

### Added
- Corpus pipeline v2: builds federal (~6500), top-5 state-law (~2000) and 5 EU acts into a signed `.tar.zst` bundle.
- `prepare_data/build_corpus.py` CLI entry point for assembling bundles from configurable sources (`bund`, `land:<code>`, `eu:<celex>`).
- `src/legal_text_mcp_de/corpus/` package: `BundleManifest`/`BundleEntry` schemas, `CorpusCache` (XDG-compliant), `verify_bundle_signature` (cosign keyless), `load_corpus_bundle` (local-first with OCI auto-download fallback).
- New env vars: `CORPUS_VERSION`, `CORPUS_AUTO_DOWNLOAD`, `CORPUS_CERT_IDENTITY`, `STRICT_DATASET`.
- 5 state-law scrapers: Bayern (gesetze-bayern.de), NRW (recht.nrw.de), BW (landesrecht-bw.de jportal), NDS (nds-voris.de), HE (rv.hessenrecht.hessen.de).
- 4 EU-act loaders: ePrivacy (32002L0058), DSA (32022R2065), DMA (32022R1925), AI Act (32024R1689).
- 36 new tests covering the corpus pipeline (total 419 tests passing).

### Changed
- `DATASET_PATH` unset is no longer fatal at startup; default is auto-download from GHCR. Set `STRICT_DATASET=true` to restore old fail-fast behaviour.

### Compatibility
- All 9 v1 MCP tools unchanged. HTTP API unchanged. Drop-in for v1.0.0 callers.

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
