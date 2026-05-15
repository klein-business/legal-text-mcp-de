---
type: design
topic: public-release-phase-3-4-community-docs-distribution
date: 2026-05-16
status: review
---

# Public Release — Phase 3+4 (Community + Docs Site + Supply-Chain + Distribution + Launch) Design Amendment

## Decision

Phase 3+4 of the public-release programme implements Pillars 2, 4, 5,
6, and 7 of the parent design
[2026-05-15-public-release-enterprise-readiness-design.md](2026-05-15-public-release-enterprise-readiness-design.md)
as a single combined effort. At the end of this phase the repository
has all community-health files, a versioned mkdocs-material
documentation site, a complete supply-chain pipeline (Dependabot,
SBOM, SLSA-3, cosign), PyPI Trusted Publisher and signed multi-arch
GHCR images, release-please automation, and the manual launch
procedure for the v1.0.0 public flip is fully documented and
mechanically gated.

The repository remains private at PR-merge time. The public flip and
v1.0.0 release are manual final steps the user executes from the
documented launch procedure once the merged state is on `main`.

## Strategic Inputs (User-Confirmed)

| Decision | Choice |
| --- | --- |
| Plan structure | Single combined mega-plan; one large PR |
| Public-flip version | v1.0.0 directly (full stability commitment for MCP tools + HTTP routes) |
| PyPI package name | `legal-text-mcp-de` (PyPI 404-verified available 2026-05-16) |
| Carryovers from Phase 1+2 | All seven bundled (C-1 through C-7, see below) |
| Build-backend migration | Full source rename `mcp/` → `src/legal_text_mcp_de/` with hatchling; no selector workaround |
| Source layout | src-layout (`src/legal_text_mcp_de/`) for clarity and convention |
| Docs site | mkdocs-material defaults: no analytics, mike for versioning, GitHub Pages hosting |
| Release automation | `release-please-action` (manifest-driven) |
| Distroless OCI base | Out of scope for v1.0.0 |
| Public-flip mechanics | Documented manual procedure in `docs/operations/launch-procedure.md`; user executes after PR-merge |

## What Stays from the Parent Spec

Carries through unchanged from the parent design:

- Apache 2.0 licence + NOTICE + MIT-floleuerer preservation (Phase 1)
- 8-workflow CI topology + verify_pre_flip 8 checks (Phase 2)
- SECURITY.md content and Private Vulnerability Reporting model
- Tier-C ambition: signed releases, SBOM, SLSA-3, OpenSSF Best
  Practices silver, formal versioning policy

## What Changes vs. the Parent Spec

| Adjustment | Parent spec | Phase 3+4 (this amendment) |
| --- | --- | --- |
| SECURITY.md timing | Pillar 2 (Phase 3) | Already shipped in Phase 2 |
| Build-backend approach | "switch to hatchling; rename or selector — to be decided" | Full rename, src-layout, atomic single-task |
| PyPI name | Candidate + fallbacks | `legal-text-mcp-de` confirmed (verified) |
| Public-flip mechanics | Mixed in Pillar 7 | Pulled into a dedicated `launch-procedure.md` doc; user executes manually after merge |
| Coverage floor expectation | "floor never drops" | Raised opportunistically once C-6 lands |

## Carryover Bundle from Phase 1+2 Reviews

| # | Item | Section in mega-plan | Effort |
| --- | --- | --- | --- |
| C-1 | SPDX-header retrofit on ~75 pre-existing Python files via the existing `scripts/check_spdx_header.py` template; remove those paths from the exempt list once they carry the header | A: Pre-flight | mechanical, ~30 min |
| C-2 | Mypy strict ratchet on `mcp/` modules — apply per-module override `strict = true` for the simplest five (`config.py`, `http_models.py`, `legal_texts/errors.py`, `legal_texts/models.py`, `legal_texts/sources.py`); fix or annotate; remove from blanket `strict = false` override | C: Type cleanups | ~2–3 hours |
| C-3 | `scripts/verify_full_corpus_bundle.py` — convert the 50 `union-attr` ignores to typed intermediate variables; remove suppressions | C: Type cleanups | ~1 hour |
| C-4 | ruff version skew: pin ruff in `pyproject.toml` dev group; switch `.pre-commit-config.yaml` ruff entry to `repo: local` so it uses the same binary uv installs | A: Pre-flight | ~15 min |
| C-5 | DCO workflow currently passes only HEAD SHA to `tim-actions/dco`; switch to iterating all PR commits (use `${{ github.event.pull_request.commits }}`-based approach or a comparable action) | A: Pre-flight | ~30 min |
| C-6 | Coverage gaps: `mcp/legal_texts/normalizer.py` (0%), `mcp/parser.py` (61%) — add focused tests targeting branches; raise `fail_under` from 86 to the new measured floor | C: Type cleanups (despite the name; coverage lives here too) | ~2–3 hours |
| C-7 | `pyproject.toml` Homepage and Repository URLs are identical; either drop Homepage and keep only Repository, or document the intent. Decision: drop Homepage; PyPI renders Repository as the project page | A: Pre-flight | ~5 min |

## In-Scope Pillars

### Pillar 2 — Community Health & Governance

**Artefacts (all English, all under repo root or `.github/`):**

- `CONTRIBUTING.md` — dev setup (`uv sync --all-groups`), Conventional
  Commits with allowed types, DCO sign-off (`git commit -s`), branch
  naming, test + coverage expectations, lint/format expectations,
  pre-commit install pointer, "issue before PR for non-trivial work"
  expectation, cross-links to `CODE_OF_CONDUCT.md` and `SECURITY.md`.
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1 verbatim. Contact:
  `martin@klein.business`.
- `SUPPORT.md` — questions → GitHub Discussions; bugs → Issues; security
  → SECURITY.md private reporting.
- `GOVERNANCE.md` — solo-BDFL model, decision path, co-maintainer
  onboarding path, roadmap source (GitHub Projects), branch-protection
  bypass-allowlist audit path (referenced from the parent spec).
- `ROADMAP.md` — next 3–6 months: full state-law corpus coverage,
  additional EU acts, mypy-strict-ratchet completion on `mcp/`,
  distroless container migration, performance work.
- `.github/CODEOWNERS` — `* @klein-business`.
- `.github/ISSUE_TEMPLATE/bug_report.yml` — form fields: what
  happened, expected behaviour, repro, dataset/env, Python version,
  MCP/HTTP transport.
- `.github/ISSUE_TEMPLATE/feature_request.yml` — form fields: use
  case, proposal, alternatives.
- `.github/ISSUE_TEMPLATE/config.yml` — `blank_issues_enabled: false`;
  contact_links: Questions → Discussions, Security → private reporting.
- `.github/PULL_REQUEST_TEMPLATE.md` — checklist: tests, docs,
  CHANGELOG, DCO sign-off, Conventional-Commit-style title.

**Acceptance:**
- GitHub Insights → Community Standards: 100% green.
- Test PR from secondary account triggers DCO + commitlint checks.
- A CoC report email reaches `martin@klein.business`.

### Pillar 5 — Documentation Site

**Stack:**
- `mkdocs` + `mkdocs-material` (latest stable)
- Plugins: `mkdocstrings[python]`, `mkdocs-mermaid2-plugin`,
  `mkdocs-git-revision-date-localized-plugin`, `mike`,
  `mkdocs-redirects`, `mkdocs-swagger-ui-tag` (for embedded OpenAPI
  rendering)
- Hosting: GitHub Pages at `klein-business.github.io/legal-text-mcp-de`
- Analytics: none (privacy-conscious default)

**Structure (35 markdown files under `docs/`):**

```
docs/
├── index.md
├── quickstart/
│   ├── claude-desktop.md
│   ├── cursor.md
│   ├── uvx.md
│   └── docker.md
├── concepts/
│   ├── data-modes.md
│   ├── provenance.md
│   └── mcp-and-http-surface.md
├── tools/
│   ├── list_laws.md
│   ├── get_law.md
│   ├── get_norm.md
│   ├── resolve_citation.md
│   ├── search_laws.md
│   ├── get_source_metadata.md
│   ├── get_corpus_coverage.md
│   ├── get_source_limitations.md
│   └── get_related_norms.md
├── api/
│   ├── index.md
│   └── openapi.md            (mkdocs-swagger-ui-tag)
├── operations/
│   ├── security.md           (mirror of SECURITY.md)
│   ├── sbom.md
│   ├── verify-with-cosign.md
│   ├── versioning.md
│   ├── threat-model.md
│   ├── coverage-baseline.md  (mirror of phase-2 evidence)
│   ├── openssf-application.md
│   └── launch-procedure.md
├── contributing/
│   ├── index.md              (mirror of CONTRIBUTING.md)
│   └── code-of-conduct.md
├── changelog.md              (auto-include of CHANGELOG.md)
├── roadmap.md                (mirror of ROADMAP.md)
└── community/
    ├── governance.md
    └── support.md
```

**Existing content migration:** The current `docs/features/*.md` and
`docs/modules/*.md` files become source material for `docs/concepts/`,
`docs/tools/`, and `docs/api/`. Files are not deleted; they may be
moved or content-merged. Cross-links in the repo (README, CHANGELOG)
are updated to point at the new structure.

**Deploy (`docs.yml`):**
- `on: push: branches: [main]` → `mike deploy --push --update-aliases dev` (preview)
- `on: push: tags: ['v*.*.*']` → `mike deploy --push --update-aliases <version> latest`
- Permissions: `contents: write` (mike pushes to `gh-pages` branch)
- Concurrency group prevents racing deploys

**One-time GitHub Pages setting:** repo Settings → Pages → Source =
`gh-pages` branch (documented in `launch-procedure.md` as Day-0
prerequisite).

**Acceptance:**
- `mkdocs build --strict` exits 0 with no warnings.
- All cross-links resolve.
- After v1.0.0 release, `mike` lists `1.0.0` aliased to `latest`.
- Search returns hits for MCP tool names and law identifiers.

### Pillar 4 — Security & Supply-Chain

**Dependabot (`.github/dependabot.yml`):** pip + github-actions +
docker ecosystems; weekly Monday schedule; grouping by
`security` / `minor` / `patch`; labels `dependencies`; reviewer
`klein-business`.

**SBOM generation:**
- Python: `cyclonedx-py environment` → CycloneDX 1.6 JSON
  (`dist/sbom-python.cdx.json`) → attached to GitHub Release.
- OCI: `anchore/syft` → CycloneDX JSON → attached via
  `cosign attest --predicate sbom.json --type cyclonedx`.

**SLSA-3 build provenance:**
- Python wheel/sdist: `slsa-framework/slsa-github-generator` Python
  builder. Provenance via PEP 740 to PyPI (built into
  `pypa/gh-action-pypi-publish`) and as GitHub Release asset.
- OCI: `slsa-framework/slsa-github-generator` Docker builder.
  Attestation attached to image via `cosign attest --predicate`.

**Signing (Sigstore cosign keyless):**
- OCI images keyless-signed using GitHub Actions OIDC → Fulcio in
  `release.yml`.
- Verification command in README and `docs/operations/verify-with-cosign.md`:
  ```bash
  cosign verify ghcr.io/klein-business/legal-text-mcp-de:v1.0.0 \
    --certificate-identity-regexp 'https://github.com/klein-business/.*' \
    --certificate-oidc-issuer https://token.actions.githubusercontent.com
  ```
- Python distribution: PEP 740 Sigstore attestation via the official
  PyPI publish action (built-in).

**Container scanning:**
- `aquasecurity/trivy-action` on PR + release. Fail on `HIGH`/`CRITICAL`
  unless explicit waiver in `.trivyignore`.

**Image hardening (Dockerfile changes):**
- Pin `python:3.12-slim` base by digest (`@sha256:...`).
- `USER 10001:10001` for non-root execution.
- `HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health', timeout=2)" || exit 1`
  (no curl dependency).
- Multi-arch build (`linux/amd64`, `linux/arm64`) via
  `docker/build-push-action` + QEMU + buildx.
- Distroless deferred to post-v1.0.0.

**Secret scanning extended:**
- GitHub-native Secret Scanning + Push Protection enabled in repo
  settings (manual step documented in `launch-procedure.md`).
- `gitleaks/gitleaks-action` as a Required Check on PRs.
- `detect-secrets` via pre-commit and CI remain from Phase 2.

**Threat model (`docs/operations/threat-model.md`):** STRIDE-style
analysis for: MCP transport (streamable HTTP), HTTP-API endpoints,
dataset loading (DATASET_PATH config and validation), source
discovery (gesetze-im-internet.de, EUR-Lex/Cellar runtime fetches).
Tier-C documentation requirement.

**OpenSSF Best Practices Silver
(`docs/operations/openssf-application.md`):** pre-drafted answers
covering all 51 silver-level criteria; ready for user to file via
bestpractices.coreinfrastructure.org post-flip.

**Acceptance:**
- Scorecard ≥ 8 (verifiable after first weekly run on main).
- CodeQL has no `error`/`high` findings on `main`.
- Test tag `v0.99.0-rc.1` runs `release.yml` end-to-end and produces:
  signed wheel + sdist (PEP 740 attestation), multi-arch GHCR image
  (cosign-signed), Python + OCI SBOMs, SLSA provenance files.
- `cosign verify` snippet returns success against the test release.
- Trivy reports no `HIGH`/`CRITICAL` on the OCI image.
- `docker exec <id> id` confirms non-root (UID 10001).

### Pillar 6 — Distribution

**Build-backend migration (highest-risk piece):**

Move from `[tool.uv] package = false` + ad-hoc `PYTHONPATH=mcp`
invocation to a hatchling-built installable package using src-layout:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/legal_text_mcp_de"]

[project.scripts]
legal-text-mcp-de = "legal_text_mcp_de.server:main"
```

The `[tool.uv]` table loses `package = false`. uv now uses the
declared build-backend automatically.

**Source rename:** `mcp/*.py` and `mcp/legal_texts/*` move under
`src/legal_text_mcp_de/`. Imports of the runtime change from
`import server` / `from legal_texts import X` (legacy PYTHONPATH
tricks) to `from legal_text_mcp_de import server` /
`from legal_text_mcp_de.legal_texts import X`. The runtime's
internal `import mcp.server.fastmcp` (i.e., the Anthropic MCP SDK)
remains unchanged because that's the PyPI package name and the
rename eliminates the previous import-shadowing concern.

**Files affected by the rename (snapshot at design time; verify at
implementation):**
- Source: ~25 files under `mcp/` move to `src/legal_text_mcp_de/`.
- Tests: ~30 test files in `mcp/tests/` move to `tests/` and update
  imports.
- `Dockerfile`: `COPY mcp/ ./mcp/` → install-from-wheel-based COPY.
- 8 GitHub workflows: drop `PYTHONPATH=mcp` env / use `uv run` against
  the installed package.
- `.pre-commit-config.yaml`: mypy `additional_dependencies` review.
- `mkdocs.yml`: mkdocstrings paths.
- 11 `scripts/verify_*.py`: update imports and any path constants.
- README, NOTICE-attribution references unchanged (NOTICE is about
  legal attribution, not source paths).

**Risk mitigation:** the rename is one atomic implementation task in
the plan, with full test-suite verification immediately before and
after. If verification fails after the rename, revert the single
commit.

**PyPI:**
- Trusted Publisher configured on pypi.org (manual one-time setup
  documented in `launch-procedure.md`): repo
  `klein-business/legal-text-mcp-de`, workflow `release.yml`,
  environment `pypi`.
- PEP 740 attestations via `pypa/gh-action-pypi-publish`.
- Long description = `README.md`.
- Entry point: `legal-text-mcp-de = legal_text_mcp_de.server:main`.

**GHCR:**
- Image: `ghcr.io/klein-business/legal-text-mcp-de`.
- Tags per release: `v1.0.0`, `v1.0`, `v1`, `latest`, `sha-<short>`.
- Multi-arch (amd64, arm64).
- Cosign keyless-signed.
- SBOM + SLSA provenance attached as attestations.

**Release automation (release-please):**
- Manifest-driven: `.release-please-config.json` +
  `.release-please-manifest.json` at repo root.
- Conventional Commits on `main` produce a release PR that bumps the
  `version` in `pyproject.toml` and `CHANGELOG.md`. Merging that PR
  pushes a tag, which triggers `release.yml`.

**Versioning policy (`docs/operations/versioning.md`):**
- SemVer 2.0.0 strict.
- Stability contract for MCP tool signatures and HTTP API routes
  begins at v1.0.0.
- Breaking changes require a major bump; deprecation cycle of two
  minor versions.
- Support window: current `v1.x`. After a later major release, the
  prior `v(N-1).x` receives security patches for six months.

**`release.yml` end-to-end (triggered by `push: tags: 'v*.*.*'`):**
1. `build-python` — `uv build` → sdist + wheel; SBOM via cyclonedx-py.
2. `slsa-python` — SLSA-3 generator (parallel).
3. `publish-pypi` — Trusted Publisher upload with PEP 740 attestation
   (depends on `build-python`).
4. `build-image` — `docker buildx` multi-arch + push GHCR.
5. `cosign-sign-image` — keyless sign + attest SBOM + attest SLSA
   provenance (depends on `build-image`).
6. `github-release` — release-please-managed body; attach wheel,
   sdist, sbom-python.cdx.json, sbom-oci.cdx.json,
   slsa-python.intoto.jsonl, slsa-oci.intoto.jsonl, checksums.txt.

**Acceptance:**
- `uvx legal-text-mcp-de --version` returns the installed version.
- `docker pull ghcr.io/klein-business/legal-text-mcp-de:v1.0.0`
  succeeds; `cosign verify` returns success.
- GitHub Release `v1.0.0` carries all six artefact types.
- `release-please` correctly proposes the next bump based on
  Conventional-Commit history.

### Pillar 7 — Launch Procedure

**`verify_pre_flip.py` extensions (8 → 11 checks):**

| New check | Purpose | Failure mode |
| --- | --- | --- |
| `check_release_workflow_present` | `release.yml` exists and parses to valid YAML | FAIL with missing or parse error |
| `check_pypi_name_reserved` | HEAD request to `pypi.org/pypi/legal-text-mcp-de/json`; 200 = reserved, 404 = unreserved | FAIL on 404, SKIP on offline |
| `check_security_settings` | GitHub API: secret scanning enabled, push protection enabled, private vulnerability reporting enabled | FAIL with missing settings, SKIP without `VERIFY_GITHUB_TOKEN` |

Final gate output at flip time: 9 PASS + 2 SKIP (without token) or
11 PASS (with token after PyPI reservation + GitHub settings done).

**Launch-procedure doc (`docs/operations/launch-procedure.md`):**
step-by-step manual sequence the user executes when ready:

1. **Pre-audit** — `VERIFY_GITHUB_TOKEN=<PAT> python scripts/verify_pre_flip.py`
   → 11/11 PASS.
2. **PyPI Trusted Publisher setup** on pypi.org/manage/account/publishing/
   (one-time).
3. **GitHub settings (manual)**:
   - Settings → General → Visibility → Public.
   - Settings → Code security and analysis → Private Vulnerability
     Reporting → Enable.
   - Settings → Code security and analysis → Secret Scanning →
     Enable; Push Protection → Enable.
   - Settings → Pages → Source = `gh-pages` branch.
   - Topics: as listed in the parent spec under Pillar 1.
   - Description + Homepage URL (docs site).
   - Discussions → Enable; Wiki → Disable.
4. **Branch protection** on `main`: confirm all 13 required status
   checks are still enforced; ensure `required_signatures = true`.
5. **Tag `v1.0.0`** — either push manually or merge the release-please
   PR. Triggers `release.yml`.
6. **Verify post-flip**:
   - `pip install legal-text-mcp-de==1.0.0` works.
   - `docker pull ghcr.io/klein-business/legal-text-mcp-de:v1.0.0` and
     `cosign verify` succeed.
   - Docs site `klein-business.github.io/legal-text-mcp-de` shows
     `1.0.0` and `latest` aliases.
   - GitHub Release v1.0.0 has all six artefact types.
   - README badges resolve in the public render.

**Day-1 post-flip tasks:**
- File the OpenSSF Best Practices Silver application
  (`bestpractices.coreinfrastructure.org`) using the pre-drafted
  answers in `docs/operations/openssf-application.md`.
- Optional: PR onto a community-curated MCP server list
  (e.g. `awesome-mcp-servers`).
- Optional, user-driven: HN Show, LinkedIn, Reddit posts — not in
  engineering scope.

**Rollback plan (within 24h if critical issue):**
- Settings → Visibility → Private (instant).
- `pypi yank legal-text-mcp-de 1.0.0 --reason "<text>"` (yank, not
  delete — keeps prior installs working).
- GHCR tags removed via API (image digests remain for compliance, but
  tags gone).
- Communication via GitHub Discussion announcement + CHANGELOG entry.

## Execution Order (Mega-Plan Sections)

| Section | Purpose | Estimated tasks |
| --- | --- | --- |
| A. Pre-flight carryovers | C-1, C-4, C-5, C-7 | ~5 |
| B. Community files (Pillar 2) | CONTRIBUTING/CoC/SUPPORT/GOVERNANCE/ROADMAP/CODEOWNERS + 3 issue templates + PR template + verify_pre_flip required-files update | ~10 |
| C. Type and coverage cleanups | C-2, C-3, C-6 | ~6 |
| D. Documentation site (Pillar 5) | mkdocs + plugins setup, content migration of 35 pages, docs.yml workflow, mike versioning, threat-model.md, versioning.md, openssf-application.md | ~15 |
| E. Supply-chain setup (Pillar 4) | Dependabot, gitleaks workflow, Trivy workflow integration, SBOM tooling (cyclonedx-py + syft), SLSA workflow templates, cosign config | ~8 |
| F. Distribution (Pillar 6 — including the atomic rename) | Hatchling migration + source rename (single atomic task), pyproject build-system, project.scripts, release-please config, release.yml | ~8 |
| G. Docker hardening (Pillar 4 continued) | Dockerfile digest pin, USER non-root, HEALTHCHECK, multi-arch buildx | ~3 |
| H. verify_pre_flip extensions (Pillar 7) | check_release_workflow_present, check_pypi_name_reserved, check_security_settings | ~3 |
| I. Test release dry-run | Tag `v0.99.0-rc.1` push, validate full release.yml end-to-end, verify cosign signature, verify PyPI upload (rc-release), yank rc | ~2 |
| J. Launch-doc + final verification | launch-procedure.md content, CHANGELOG Phase 3+4 entries, full pre-flip 11/11 PASS | ~3 |

**Total: ~63 tasks.**

## Global Acceptance Criteria (Mega-Plan complete)

- All 8 existing verify_pre_flip checks PASS + 3 new checks PASS (with
  token) or SKIP (without).
- 11 GitHub workflows present: 8 from Phase 2 + `release.yml` +
  `docs.yml` + `gitleaks.yml`.
- `mkdocs build --strict` exits 0; site renders on
  `klein-business.github.io/legal-text-mcp-de` after public flip.
- Test release `v0.99.0-rc.1` end-to-end: PyPI wheel/sdist (PEP 740
  attestation), GHCR multi-arch image (cosign-signed), Python + OCI
  SBOMs, SLSA provenance files. The rc is yanked after verification.
- CodeQL: no error/high findings on main.
- Trivy: no HIGH/CRITICAL on the released OCI image.
- Mypy strict passes on `scripts/` and on the five migrated `mcp/`
  modules (C-2).
- Coverage floor raised based on improved measurements (C-6).
- All community + ops docs present and cross-linked.
- README badge row includes CI, coverage, PyPI version, OpenSSF
  Scorecard, Apache 2.0.
- 28 GitHub-Insights Community Standards categories all green.

## Out of Scope (also for Phase 3+4)

- Distroless OCI base.
- Mypy strict on ALL `mcp/` modules (only the simplest five plus any
  new modules introduced in this phase).
- 100% test coverage on `normalizer.py` (focused improvements only;
  remaining gaps tracked).
- Custom docs domain (stays on `github.io`).
- Sponsorship button configuration.
- Multi-language docs (English only at v1.0.0).
- Performance optimisation beyond preserving current characteristics.
- Corpus expansion (additional countries, additional EU acts beyond
  what is already in the runtime).
- Direct manual GitHub-UI steps remain the user's responsibility;
  the plan documents them in `launch-procedure.md` but does not
  execute them.

## Risks

| # | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| P34-1 | Source rename `mcp/` → `src/legal_text_mcp_de/` breaks tests/imports | high | high | Atomic single task; full test-suite verification before and after; documented single-commit-revert plan |
| P34-2 | `mcp` PyPI package name (Anthropic SDK) keeps conflicting at runtime | low | medium | Rename eliminates the problem; imports use `from mcp import ...` for SDK and `from legal_text_mcp_de import ...` for own modules |
| P34-3 | Mypy strict ratchet on `mcp/` modules produces hundreds of errors | medium | medium | Per-module selection: start with the five simplest; rest deferred |
| P34-4 | Coverage floor raise fails because `normalizer.py` is hard to test | medium | low | Conservative bump (e.g., 86 → 88); full normalizer coverage tracked as post-launch work |
| P34-5 | `release.yml` test tag `v0.99.0-rc.1` fails | medium | medium | RC tag mechanism allows iteration; release.yml can be developed in dry-run mode |
| P34-6 | OpenSSF Scorecard score < 8 after all measures | medium | low | Score-impacting controls (branch protection, signed commits, SAST, dependency review) are all included; expected score ≥ 9 |
| P34-7 | User forgets PyPI Trusted Publisher setup before tag push | low | high | launch-procedure.md sequences it first; `check_pypi_name_reserved` warns; documented in CHANGELOG |
| P34-8 | Public-flip tag (`v1.0.0`) pushed before everything is steady | low | high | Pre-flip gate requires 11/11 PASS; manual tag push only after audit; rollback plan documented |
| P34-9 | mkdocs site needs one-time GitHub Pages Settings step (branch source) | low | low | docs.yml documented in launch-procedure.md as Day-0 prerequisite |
| P34-10 | Mega-plan size (~63 tasks) — execution time/cost | high | medium | User accepted; plan clearly segmented A–J for pauses; subagent-driven keeps per-task context focused |
| P34-11 | Hatchling build-backend incompatibility with current source layout reveals only at `uv build` time | medium | medium | Section F starts with a hatchling-only smoke build to catch issues before the full rename |
| P34-12 | The rename invalidates the existing `.secrets.baseline` line numbers en masse | high | low | After the rename, regenerate baseline once; documented as a step in Section F |

## Open Items Carried Into the Implementation Plan

- Final list of mypy-strict-eligible `mcp/` modules confirmed during
  Section C implementation.
- Specific GitHub Action SHAs (latest stable at implementation time).
- `release.yml` job-dependency graph finalised during Section F.
- Mkdocs-material colour scheme (project palette) — defaults are fine
  unless the user prefers a specific accent colour.
- `release-please-config.json` precise schema (single-package
  manifest mode).
