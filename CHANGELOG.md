# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.2] - 2026-05-18

Distribution / discovery release. No runtime behaviour changes.

### Added
- **Official MCP Registry integration**
  ([registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io)):
  - `server.json` at repo root (schema 2025-12-11) describes the PyPI
    + OCI packages, env vars, and stdio transport. Auto-bumped by
    release-please alongside `pyproject.toml`.
  - `.github/workflows/mcp-registry.yml`: tag-push workflow that runs
    `mcp-publisher validate` + version-vs-tag guard + GitHub OIDC
    login + `mcp-publisher publish` — no long-lived tokens.
- **Smithery.ai discovery**: `smithery.yaml` at repo root declares
  `runtime: container`, `startCommand.type: stdio`, and the three
  optional config fields (datasetPath, strictDataset, anthropicApiKey).
- **Contributor on-ramp**: `CONTRIBUTING.md` gains a "Your first
  contribution" section linking the curated `good first issue` filter
  and a 6-step workflow, plus an "Architecture tour" with a
  five-minute mental map of `src/`. Pairs with 4 newly-labelled
  good-first-issues (#91–#94).
- **GitHub Discussions**: welcome post in Announcements ([discussion
  #90](https://github.com/klein-business/legal-text-mcp-de/discussions/90))
  with 60-second quickstart + roadmap.
- **awesome-mcp-servers listing**: PR open against
  [punkpeye/awesome-mcp-servers#6544](https://github.com/punkpeye/awesome-mcp-servers/pull/6544)
  (87 k ⭐) for the ⚖️ Legal section.

### Fixed
- **PyPI ownership marker**: `README.md` now ships
  `mcp-name: io.github.klein-business/legal-text-mcp-de` so the
  Official MCP Registry's PyPI verification flow succeeds.

### Changed
- `pytest --cov` floor stays at 86 % combined; CLI module total is now
  91 % (was ~88 %), with `cli/_lookups.py` jumping 77 → 96 % via a
  single parametrised "every lookup exits 1 on missing DATASET_PATH"
  test.
- `mypy --strict` ratchet extends to 7 modules total: `config`,
  `http_models`, `legal_texts.{errors,models,sources}`, `cli.*`,
  `http_api`. The entire user-facing API surface (CLI + HTTP) is
  type-strict; a hard-failing `Mypy strict (cli + http_api)` CI job
  guards regressions.
- `.github/workflows/ci.yml`: stale `mypy mcp/` invocation (path no
  longer exists) replaced with `mypy` against the real `src/` tree.
- `docs/operations/openssf-application.md`: refreshed from a Silver
  draft into an awarded-Silver / Gold-progress (78 %) reference with
  live status pulled from `bestpractices.dev/projects/12860.json`,
  including a "Refresh checklist" maintenance section.

## [2.1.1] - 2026-05-18

Patch release rolling up the post-v2.1.0 follow-ups. No code changes;
docs polish + Dockerfile.hosted digest pin (the known follow-up listed
in the v2.1.0 entry).

### Fixed
- `deployment/Dockerfile.hosted`: base image upgraded from tag-only
  `:2.1.0` to digest-pinned
  `:2.1.0@sha256:b9f091484814d8324c3462cdfd5966c155a3fb35a6290eb93a12e7cfe4d15ece`.
  Closes the "known follow-up" listed in the v2.1.0 changelog.
- `README.md`: 4 stale phrasings cleaned up (PYTHONPATH=mcp legacy
  pytest invocation in Development section, "Verification (post-v2.0.0)"
  heading, "v2.0 exposes the corpus" phrasing for MCP Resources,
  HTTP API quickstart still showed only the bare uvicorn invocation).
- Documentation: image-tag examples bumped `:2.1.0` → `:2.1.1`
  across README + docs/quickstart/docker + docs/concepts/data-modes
  + docs/operations/{slsa,verify-with-cosign,production-deployment}
  + deployment/deploy.sh.

### Added
- `README.md`: 3-line "hero" subtitle under the H1 — concise
  value-proposition for first-time visitors ("Cite-grade German
  legal-text infrastructure for LLM agents").
- `README.md` HTTP-API quickstart now shows `legal-text-mcp-de http`
  as the primary command, with the raw uvicorn invocation listed as
  the equivalent.
- `README.md` Development section mentions the Justfile shortcuts.

### Compatibility
- All 10 MCP tool signatures (9 v1 + `research_topic`) unchanged.
- HTTP API surface unchanged.
- CLI surface unchanged (no new or renamed subcommands).

## [2.1.0] - 2026-05-18

### ⚠️ Breaking

- **Bare invocation prints help:** `legal-text-mcp-de` (no args) now
  prints `--help` instead of silently starting the MCP server. Use
  `legal-text-mcp-de serve` to start the MCP server explicitly.
  Affects: Claude Desktop configs, Docker `CMD`, `uvx` invocations.
  See [migration-v1-v2.md](docs/operations/migration-v1-v2.md) for the
  copy-paste-ready migration matrix.

### Added

- **`typer`-based CLI** as the new `legal-text-mcp-de` entry point.
  14 subcommands covering every MCP tool plus server lifecycle, corpus
  management, and diagnostics. See
  [docs/cli/index.md](docs/cli/index.md) for the full reference.
- New subcommands:
  - Server: `serve`, `http`
  - Lookups: `laws`, `law`, `norm`, `cite`, `search`, `meta`,
    `coverage`, `limitations`, `related`
  - Smart tool: `research`
  - Corpus: `corpus pull`, `corpus verify`, `corpus info`
  - Diagnostics: `health`, `version`,
    `completion show|install {bash|zsh|fish}`
- Global flags: `--json`, `--quiet`, `--debug`, `--version`.
- CLI JSON output schema mirrors `legal_text_mcp_de.http_models.*`
  Pydantic shapes — same models the HTTP API uses.
- Exit-code matrix: 0 success, 1 runtime, 2 usage, 3 sampling,
  4 corpus, 5 connectivity, 130 SIGINT.

### Changed

- `[project.scripts] legal-text-mcp-de` console entry repointed from
  `legal_text_mcp_de.server:main` to `legal_text_mcp_de.cli:main`.
  Old entry point preserved as internal call surface for legacy
  callers (still importable).
- `typer >= 0.20, < 1` promoted from transitive dependency
  (via `mcp[cli]==1.27.1`) to direct project dependency.

### Docs

- New: `docs/cli/index.md`, `mkdocs.yml` "CLI" nav entry.
- `README.md`: new "CLI" section; install modes updated to `serve`.
- All `docs/quickstart/*.md` updated to use `serve` in config snippets.
- `docs/operations/versioning.md`: new paragraph clarifying that the
  CLI invocation form is outside the v1.0.0 stability contract.
- `docs/operations/migration-v1-v2.md`: new "v2.0 → v2.1" section.

### Known follow-ups

- `deployment/Dockerfile.hosted` base image is pinned to `:2.1.0` tag.
  The digest pin returns in v2.1.1 once the v2.1.0 release workflow
  publishes the image and the manifest digest is known.

### Compatibility

- MCP tool signatures (all 10 incl. `research_topic`) unchanged —
  `tests/test_v1_compat.py` still green.
- HTTP API surface unchanged.

## [2.0.1] - 2026-05-17

Patch release rolling up post-GA cleanup. All changes are backwards-
compatible; no behaviour or surface changes vs. v2.0.0.

### Fixed
- `pyproject.toml`: `pytest-asyncio` constraint loosened to `>=0.24,<2`
  so Dependabot's security update for `pytest` (8.4.2 → 9.0.3) resolves
  cleanly. Bumps lockfile to `pytest 9.0.3` + `pytest-asyncio 1.3.0`.
  Resolves Dependabot Updates run 25989549469. (#71)
- `docs/`: GHCR docker tag examples corrected from `:v2.0.0` to
  `:2.0.0` (no leading `v` — matches the actual published tag).
  Files: `README.md`, `docs/quickstart/docker.md`,
  `docs/concepts/data-modes.md`, `docs/operations/{slsa,verify-with-cosign}.md`. (#73)
- `deployment/Dockerfile.hosted`: base image bumped from
  `:2.0.0-rc.4` (stale RC) to `:2.0.0@sha256:10958304…` (GA, digest-pinned). (#75)

### Changed
- **Workflow permissions hardening:** every workflow's top-level
  `permissions:` is now `contents: read`; writes (`packages`,
  `id-token`, `security-events`, `statuses`, `checks`, `contents:write`)
  pushed to job-level. Lifts OpenSSF Scorecard `Token-Permissions`
  from 0 to 10. Workflows touched: `codeql`, `commitlint`, `docs`,
  `release-please`, `release`, `trivy`, `research-topic-smoke`,
  `scorecard`. (#74, #75)
- `.github/workflows/release.yml`: SLSA-Python generator now uploads
  the `*.intoto.jsonl` provenance file as a GitHub Release asset
  (`upload-assets: true`). Closes Scorecard `Signed-Releases: 0`. (#75)
- `.release-please-manifest.json` bumped `0.1.0` → `2.0.0` → `2.0.1`
  so release-please tracks future patch/minor deltas correctly. (#71, this PR)
- `scripts/verify_pre_flip.py`: `EXPECTED_WORKFLOWS` includes
  `research-topic-smoke.yml`. (#71)
- `tests/test_verify_pre_flip.py`: in-test fixture aligned with the
  production list. (#71)

### Docs
- **`README.md`:** badge style restored to `for-the-badge` (larger,
  more prominent); `pip install legal-text-mcp-de==2.0.1` added as
  install Mode 1 (PyPI); other 4 install modes renumbered. (#74, this PR)
- `docs/concepts/mcp-native.md`: relative links to `../resources/…`,
  `../prompts/…`, `../tools/…`, `../operations/…` corrected. (#71)
- `docs/index.md`: replaces "nine tools" with full v2 capability
  bullets (Tools 10×, Resources 10×, Prompts 5×, Sampling). (#72)
- `docs/quickstart/{claude-desktop,cursor,uvx,docker}.md` +
  `docs/concepts/mcp-and-http-surface.md`: "nine tools" → "ten tools
  (9 v1 law tools + `research_topic`)". (#72)
- `docs/operations/versioning.md`: stability contract extended to
  cover v1 → v2 transition; support policy updated (`v2.x` current,
  `v1.x` security-only until 2026-11-17). (#72)
- `docs/operations/threat-model.md`: review date refreshed to
  `2026-05-17 (v2.0.0 GA close)`. (#72)

### Removed
- `docs/quickstart/docker.md`: stale "Pre-release: build locally"
  note. (#72)

### Compatibility
- All 9 v1 MCP tool signatures + 1 v2 `research_topic` tool unchanged
  (still frozen by `tests/test_v1_compat.py`).
- HTTP API surface unchanged.

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
