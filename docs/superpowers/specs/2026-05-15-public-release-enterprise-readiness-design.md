---
type: design
topic: public-release-enterprise-readiness
date: 2026-05-15
status: review
---

# Public Release & Enterprise Readiness Design

## Decision

The `klein-business/legal-text-mcp-de` repository transitions from a
proprietary commercial codebase into a public, Apache-2.0-licensed open
source project at **Tier C — enterprise-procurable** quality. The
transition is staged across four phases and concludes with the public
flip and `v1.0.0` release. All artefacts published from `v1.0.0` onward
are reproducible, signed, attested, and accompanied by an SBOM.

## Strategic Inputs (User-Confirmed)

| Decision | Choice |
| --- | --- |
| Release model | True open source (community-welcoming) |
| OSS license | Apache 2.0 |
| Ambition tier | Tier C — enterprise-procurable |
| Maintainer model | Solo-maintainer + hard-fork; klein-business as copyright holder, Martin Klein named maintainer |
| Phasing | Staged; repo stays private until end of Phase 4; public flip with `v1.0.0` |
| Documentation language | English |
| Upstream | `floleuerer/deutsche-gesetze-mcp` — verified MIT (Copyright (c) 2025 Florian Leuerer); preserved in `NOTICE` |
| Contact address | `martin@klein.business` (used as backup for SECURITY and CoC) |
| CODEOWNERS handle | `@klein-business` (organisation account) |
| Type checker | mypy strict |
| Coverage floor | `max(85, measured baseline)` |
| Python support | 3.12 and 3.13 (CI matrix); `pyproject.toml` `requires-python = ">=3.12"` |
| Distroless image | Out of scope for v1.0.0 |

## Principles

1. **Source hygiene first.** No official legal text content is committed
   to the repository. The repo ships tooling and references; data
   ingestion remains an external runtime step against
   `gesetze-im-internet.de` and EUR-Lex/Cellar.
2. **Reproducibility and provenance.** Every published artefact (PyPI
   wheel/sdist, OCI image) is traceable to a source revision via SLSA-3
   build provenance and cryptographically signed via Sigstore cosign
   (OCI) or PEP 740 attestations (Python).
3. **Clean attribution.** Upstream MIT terms for code originating from
   `floleuerer/deutsche-gesetze-mcp` are preserved in `NOTICE` and
   `licenses/MIT-floleuerer.txt`. New work is Apache 2.0 under
   klein-business copyright.
4. **Disclaimer-first communication.** "No legal advice", "best-effort
   provenance", and "local infrastructure" disclaimers are prominent in
   README, MCP server description, and every release announcement.
5. **Solo-maintainer-sustainable.** Automation over manual steps.
   Release process is fully automated from tag push to signed
   artefacts. DCO (not CLA) is used to keep contribution friction low
   for the maintainer.
6. **Conservative defaults.** Tier C targets mature, well-supported
   tooling. Experimental or single-vendor tooling stays out of the
   critical release path.

## Pillars (In Scope)

The transition covers seven coordinated work pillars. Each pillar
defines artefacts, acceptance criteria, and verification gates. Pillars
are not independent subsystems; they are facets of one coherent goal
and are sequenced into four delivery phases (see "Phasing").

### Pillar 1 — Legal, Licence, Repository Identity

Establishes the legal and visual foundation for a public Apache-2.0
project.

**Artefacts:**

- `LICENSE` — full Apache 2.0 text. Copyright line:
  `Copyright 2026 klein-business`.
- `NOTICE` — Apache-2.0-mandated notice file. Contains:
  - Upstream attribution: derivative work of
    `floleuerer/deutsche-gesetze-mcp` (Copyright (c) 2025 Florian
    Leuerer, MIT). MIT terms preserved in
    `licenses/MIT-floleuerer.txt`.
  - Third-party attribution block for runtime dependencies that
    require it (audited at implementation time; typically none for
    permissive deps, but `roman-numbers`, `lxml`, and
    `beautifulsoup4` to be checked).
  - Data source statement: `gesetze-im-internet.de` reuse status
    under §5 UrhG; EUR-Lex reuse under Commission Decision
    2011/833/EU. The repository distributes no editorial legal text.
- `licenses/MIT-floleuerer.txt` — verbatim upstream MIT licence text.
- `AUTHORS.md` — primary author Martin Klein. Acknowledgement block for
  Florian Leuerer (original author).
- `CHANGELOG.md` — "Keep a Changelog" 1.1.0 + SemVer 2.0.0 format.
  Initial entry for `v1.0.0` written at public-flip time.
- `README.md` — full English rewrite:
  - Apache 2.0 licence badge replaces proprietary badge.
  - Badge row: CI, coverage, PyPI version, OpenSSF Scorecard, OpenSSF
    Best Practices, Apache 2.0.
  - Hero section: one-line description, three-paragraph "what / why /
    not-what" with disclaimer.
  - Sections: Features, Quickstart (Claude Desktop config snippet,
    `uvx` invocation, Docker invocation, HTTP smoke test), Data
    sources & provenance, MCP tools summary (with deep links to docs
    site), HTTP API summary, Operability (Security, SBOM, SLSA,
    cosign verify snippet), Contributing link, License,
    Acknowledgements.
- `pyproject.toml` updates:
  - Switch from `[tool.uv] package = false` to an installable layout
    with an explicit build backend (recommended: `hatchling`). Move
    the runtime source from `mcp/` to a packaged path consumable by
    the build backend (the existing `mcp/__init__.py` already exists;
    a `[tool.hatch.build.targets.wheel]` selector or rename to a
    distinct top-level package name avoids collision with the
    `mcp` PyPI client SDK used as a dependency — to be decided in
    Phase 1 implementation).
  - `license = "Apache-2.0"` (PEP 639 SPDX expression).
  - `requires-python = ">=3.12"`.
  - `[project.urls]` with Homepage (docs site), Repository, Issues,
    Changelog, Security.
  - `[project.scripts] legal-text-mcp-de = "<package>.server:main"`
    enabling `uvx legal-text-mcp-de`. A `main()` entry function is
    added to `server.py` if not present.
  - PyPI classifiers: `License :: OSI Approved :: Apache Software
    License`, `Development Status :: 5 - Production/Stable`,
    `Programming Language :: Python :: 3.12`, `:: 3.13`, plus topic
    classifiers.
- `assets/readme-banner.svg` — update embedded licence badge to
  Apache 2.0.
- `docs-legacy/` audit — confirm it contains only historical
  documentation. Remove any internal-only material.

**GitHub repository metadata (set at public-flip, not in repo):**

- Description: one-line summary.
- Homepage: docs site URL.
- Topics: `mcp`, `mcp-server`, `model-context-protocol`,
  `claude-desktop`, `legal-tech`, `german-law`, `gesetze`, `dsgvo`,
  `gdpr`, `python`, `fastapi`.
- Branch protection on `main`: required status checks (all Phase 2/4
  workflows must pass), linear history, signed commits required. For
  the solo-maintainer model, "Require pull request reviews" is
  enabled with "Require review from Code Owners" but with
  "Allow specified actors to bypass required pull requests" set to
  `@klein-business`; bypasses are audited via GitHub's
  branch-protection log. The audit path is documented in
  `GOVERNANCE.md`.
- Settings: Issues on, Discussions on, Wiki off.

**Verification gate (`scripts/verify_pre_flip.py`, new):**

- `LICENSE` SHA-256 matches the canonical Apache-2.0 text.
- `NOTICE`, `AUTHORS.md`, `CHANGELOG.md`, `licenses/MIT-floleuerer.txt`
  exist and reference the expected entities.
- No occurrence of the strings `proprietary commercial` or
  `All rights reserved.` outside of git history.
- `pyproject.toml` version matches the most recent CHANGELOG entry.
- `detect-secrets` finds no unaudited secrets.

**Acceptance criteria:**

- `licensee` recognises the repository as Apache-2.0.
- README renders on GitHub with all badges resolving.
- Pre-flip audit script returns success.

### Pillar 2 — Community Health & Governance

Files that GitHub's Community Standards checklist looks for, plus the
governance documents an enterprise procurement team expects.

**Artefacts:**

- `CONTRIBUTING.md` — dev setup (`uv sync --all-groups`), branch and
  PR conventions (Conventional Commits, since `release-please` consumes
  them), test and coverage expectations, lint and format expectations,
  DCO sign-off requirement (`git commit -s`), issue-before-PR
  expectation for non-trivial changes.
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1 verbatim. Contact:
  `martin@klein.business`.
- `SECURITY.md` — vulnerability disclosure policy:
  - Reporting channel: GitHub Security Advisories (preferred);
    `martin@klein.business` as backup.
  - Response SLA: acknowledgement within 5 business days; coordinated
    disclosure within 90 days.
  - Supported versions table: initial entry `v1.x — supported`.
  - CVE assignment via GitHub as CNA.
- `SUPPORT.md` — directs questions to GitHub Discussions, not Issues.
- `GOVERNANCE.md` — solo-maintainer (BDFL) model. Decision path. Path
  for adding co-maintainers. Roadmap source is GitHub Projects (or
  Discussions).
- `ROADMAP.md` — high-level next 3–6 months. Initial entries: corpus
  expansion, additional EU acts, performance work.
- `.github/CODEOWNERS` — `* @klein-business`.
- `.github/ISSUE_TEMPLATE/`:
  - `bug_report.yml` — what happened, expected, repro, dataset/env.
  - `feature_request.yml`.
  - `config.yml` — directs support questions to Discussions and
    security to private reporting.
- `.github/PULL_REQUEST_TEMPLATE.md` — checklist: tests, docs,
  CHANGELOG entry, DCO sign-off, Conventional-Commit subject.
- DCO enforcement workflow (Phase 2 — implemented in `dco.yml`).

**Acceptance criteria:**

- GitHub Insights → Community Standards checklist is 100% green.
- A test PR from a separate account exercises the DCO check.
- Contact email receives test reports from `martin@klein.business`.

### Pillar 3 — CI/CD Hardening & Quality Gates

Refactors the existing single-workflow CI into a hardened topology with
explicit gates per concern.

**Workflow topology (`.github/workflows/`):**

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| `ci.yml` (refactored) | PR + push to `main` | Lint, typecheck, test, coverage, lock integrity, build verification |
| `e2e.yml` | PR + push + nightly | `verify_release.py` (full fixture release gate) and `verify_e2e.py` (local HTTP/MCP E2E) |
| `codeql.yml` | PR + weekly | Python SAST via CodeQL |
| `scorecard.yml` | weekly | OpenSSF Scorecard → SARIF + README badge |
| `dependency-review.yml` | PR | GitHub Dependency Review |
| `commitlint.yml` | PR | Conventional Commits enforcement |
| `dco.yml` | PR | DCO sign-off check |
| `megalinter.yml` (refactored) | PR + push | Existing MegaLinter, expanded scope |
| `release.yml` | tag `v*.*.*` | PyPI Trusted Publisher publish + GHCR signed image + SBOM + SLSA-3 provenance + GitHub Release |
| `docs.yml` | push `main` + tag | mkdocs build + GitHub Pages deploy via `mike` |

**`ci.yml` jobs (refactored):**

1. **lint** — `uv run ruff check . && uv run ruff format --check .`.
2. **typecheck** — `uv run --group dev mypy mcp scripts`. `pyproject.toml`
   adds `[tool.mypy] strict = true`. Strict profile covers
   `mcp/` and `scripts/`.
3. **test** — `uv run --group dev pytest --cov=mcp --cov-report=xml
   --cov-fail-under=<coverage-floor>` across the Python 3.12/3.13
   matrix on `ubuntu-latest`. Coverage floor is computed at Phase 2
   start (`max(85, baseline)`).
4. **lock-integrity** — `uv lock --check`.
5. **build** — `uv build` to produce sdist and wheel. Artefacts uploaded
   for downstream release-gate inspection.

**Pre-commit (`.pre-commit-config.yaml`):** ruff (check + format),
mypy, `detect-secrets`, `markdownlint-cli2`, `actionlint`, `shellcheck`
(for `prepare_data/` scripts). The same hooks run as required CI
checks; pre-commit is a developer convenience layer.

**Required status checks (branch protection on `main`):** all CI jobs
above + CodeQL + Scorecard + DCO + Dependency-Review + Commitlint +
MegaLinter + E2E.

**`scripts/verify_pre_flip.py`** introduced in Phase 1 evolves through
Phase 2 to include: workflow-set assertion (no stale workflows),
required-status-check assertion, branch-protection assertion (queried
via GitHub API at audit time).

**Acceptance criteria:**

- Coverage baseline measured and floor enforced; floor never drops.
- Mypy strict passes on `mcp/` and `scripts/`.
- All required checks block `main`-direct-push.
- Python 3.13 matrix passes (or `requires-python` adjusted with a
  documented reason).

### Pillar 4 — Security & Supply-Chain

Tier-C scope: SBOM, SLSA-3 provenance, signing, scoring, scanning,
disclosure.

**Dependabot (`.github/dependabot.yml`):**

- Ecosystems: `pip` (parses `pyproject.toml`), `github-actions`,
  `docker`. Weekly schedule. Group by severity (security / minor /
  patch). Default reviewer `klein-business`. Label `dependencies`.

**OpenSSF posture:**

- Scorecard workflow (Pillar 3) runs weekly, publishes SARIF, README
  badge present. Target ≥ 8.
- OpenSSF Best Practices self-certification: silver-level. Application
  filed on Day 1 post-flip. Application answers pre-drafted in
  `docs/operations/openssf-application.md` during Phase 4.

**Static analysis:**

- CodeQL (Python language pack) on PR and weekly.
- Trivy on OCI image build (PR + release). Fail on `HIGH`/`CRITICAL`
  unless documented waiver in `.trivyignore`.

**SBOM generation:**

- Python: `cyclonedx-py environment` produces CycloneDX 1.6 SBOM from
  the `uv.lock`-resolved environment. Output attached to GitHub Release
  as asset.
- OCI: `syft` produces CycloneDX SBOM. Output attached to image via
  `cosign attest --predicate`.

**SLSA-3 build provenance:**

- Python: `slsa-framework/slsa-github-generator` Python builder
  produces provenance. Attestation attached to GitHub Release and
  uploaded to PyPI via PEP 740 in the publish step.
- OCI: `slsa-framework/slsa-github-generator` Docker builder produces
  provenance. Attestation attached to image via cosign.

**Signing (Sigstore cosign):**

- All OCI images keyless-signed using GitHub Actions OIDC → Fulcio.
- Verification snippet documented in `SECURITY.md` and README:

  ```bash
  cosign verify ghcr.io/klein-business/legal-text-mcp-de:v1.0.0 \
    --certificate-identity-regexp 'https://github.com/klein-business/.*' \
    --certificate-oidc-issuer https://token.actions.githubusercontent.com
  ```

- Python distribution: PEP 740 Sigstore attestation via
  `pypa/gh-action-pypi-publish` (built-in).

**Image hardening (Dockerfile changes):**

- Pin `python:3.12-slim` base by digest (`@sha256:...`).
- Add `USER 10001:10001` for non-root execution. Adjust paths for
  permissions.
- Add `HEALTHCHECK` against `GET /health`.
- Multi-arch build (`linux/amd64`, `linux/arm64`) via
  `docker/build-push-action` with QEMU setup.
- Distroless migration deferred (out of scope for v1.0.0).

**Secret scanning:**

- GitHub-native secret scanning + push protection enabled in repo
  settings.
- `gitleaks-action` on PRs for custom organisational patterns.
- `detect-secrets` integrated into pre-commit and CI.

**Vulnerability disclosure workflow:**

- Private Vulnerability Reporting enabled.
- `SECURITY.md` defines reporting path and SLAs (see Pillar 2).
- `docs/security/threat-model.md` — brief STRIDE-style threat model
  for the HTTP and MCP attack surfaces. Tier-C documentation
  requirement.

**Acceptance criteria:**

- Scorecard score ≥ 8 on first public measurement.
- `release.yml` runs successfully on test tag `v0.99.0-rc.1` and
  produces signed wheel/sdist with PEP 740 attestation, multi-arch
  GHCR image signed by cosign, SBOMs (Python + OCI), and SLSA
  provenance files.
- `cosign verify` snippet from README returns success against the
  test release.
- CodeQL has no `error` or `high`-severity findings on `main`.

### Pillar 5 — Documentation Site

Public-facing documentation hosted on GitHub Pages, version-aware.

**Stack:**

- `mkdocs` + `mkdocs-material` theme.
- Plugins: `mkdocstrings[python]`, `mkdocs-mermaid2-plugin`,
  `mkdocs-git-revision-date-localized-plugin`, `mike` (version
  manager), `mkdocs-redirects`.

**Structure (`docs/` migration):**

Existing files in `docs/features/` and `docs/modules/` are preserved
and extended with mkdocs-material idioms (admonitions, content tabs
for client-specific examples, Mermaid sequence diagrams for MCP and
HTTP flows).

```
docs/
├── index.md                      (landing)
├── quickstart/
│   ├── claude-desktop.md
│   ├── cursor.md
│   ├── uvx.md
│   └── docker.md
├── concepts/
│   ├── data-modes.md
│   ├── provenance.md
│   └── mcp-and-http-surface.md
├── tools/                        (one page per MCP tool)
├── api/                          (HTTP API + embedded Swagger UI)
├── operations/
│   ├── security.md
│   ├── sbom.md
│   ├── verify-with-cosign.md
│   ├── versioning.md
│   ├── threat-model.md
│   └── launch-procedure.md
├── contributing/                 (mirror of CONTRIBUTING.md)
├── changelog.md                  (mirror of CHANGELOG.md)
├── roadmap.md
└── community/
    ├── code-of-conduct.md
    ├── governance.md
    └── support.md
```

**Deploy (`docs.yml`):**

- On push to `main`: deploy preview at `dev` alias.
- On tag `v*.*.*`: `mike deploy --push --update-aliases <version>
  latest`.
- Host on GitHub Pages at
  `klein-business.github.io/legal-text-mcp-de`.

**Analytics:** none. Privacy-conscious default.

**Acceptance criteria:**

- Site builds without warnings.
- All cross-links resolve.
- `mike` lists `v1.0.0` aliased to `latest` after release.
- Search returns results for MCP tool names and law identifiers.

### Pillar 6 — Distribution (PyPI + GHCR)

**PyPI:**

- Package name: `legal-text-mcp-de`. Verify availability and reserve
  during Phase 4. Fallback names: `mcp-server-legal-text-de`,
  `klein-legal-text-mcp`. Document chosen name in README.
- Publish via PyPI Trusted Publisher (GitHub Actions OIDC). No API
  token in repository secrets.
- PEP 740 attestations published with each release.
- Long description = `README.md`.
- Entry point: `legal-text-mcp-de = mcp.server:main` (enables
  `uvx legal-text-mcp-de`).

**GHCR:**

- Image: `ghcr.io/klein-business/legal-text-mcp-de`.
- Tags per release: `v1.0.0`, `v1.0`, `v1`, `latest`,
  `sha-<short>`.
- Multi-arch (amd64, arm64).
- Signed via cosign keyless.
- SBOM and SLSA provenance attached as attestations.

**Release automation:** `release-please-action`. Conventional Commits
on `main` produce a release PR that bumps `pyproject.toml` version and
`CHANGELOG.md`. Merging the release PR creates a tag, which triggers
`release.yml`.

**Versioning policy (`docs/operations/versioning.md`):**

- SemVer 2.0.0 strict.
- Stability contract for MCP tool signatures and HTTP API routes
  starts at `v1.0.0`.
- Breaking changes require major-version bump; deprecation announced
  in CHANGELOG and tool description at least two minor versions
  ahead.
- Support window: current `v1.x`. After a future major release, the
  prior `v(N-1).x` receives security patches for six months.

**Acceptance criteria:**

- `uvx legal-text-mcp-de --version` returns the installed version.
- `docker pull ghcr.io/klein-business/legal-text-mcp-de:v1.0.0`
  succeeds.
- GitHub Release for `v1.0.0` carries sdist, wheel, Python SBOM, OCI
  SBOM, SLSA provenance files, and SHA-256 checksums.
- `release-please` correctly proposes the next bump based on commit
  history.

### Pillar 7 — Launch Procedure (Public-Flip Day 0)

**Pre-flip audit checklist (mechanically verified via
`scripts/verify_pre_flip.py`):**

1. `verify_release.py` green.
2. `verify_pre_flip.py` green (LICENSE hash, NOTICE, no proprietary
   strings, no unaudited secrets, version-CHANGELOG match).
3. Most recent `main` CI run green across all required workflows.
4. Scorecard score ≥ 8 (manual verification of latest run).
5. CodeQL has no `error` or `high` findings.
6. Test release `v0.99.0-rc.1` completed successfully end-to-end.
7. mkdocs build clean on preview branch.
8. Branch protection on `main` active with all required checks.
9. Private Vulnerability Reporting enabled.
10. `martin@klein.business` responds to test reports.

**Flip action (manual, documented in
`docs/operations/launch-procedure.md`):**

1. Repository Settings → Visibility → Public.
2. Set topics (list under Pillar 1).
3. Set description and homepage URL.
4. Enable Discussions; disable Wiki.
5. Optional: enable Sponsorship link.
6. Push tag `v1.0.0` → `release.yml` runs end-to-end.
7. Verify docs site is reachable and README badges resolve in the
   public render.

**Day 1 post-flip:**

- File OpenSSF Best Practices application (silver).
- Submit PR to a community-maintained MCP servers list (e.g.
  `awesome-mcp-servers`) if desired.
- Optional, user-driven communications: blog post, LinkedIn, Show HN,
  Reddit (`r/Python`, `r/legaltech`, `r/LocalLLaMA`). Not in the
  engineering scope of this design.

**Rollback plan (in case of critical issue within 24 hours of flip):**

- Repository Settings → Visibility → Private (instantaneous).
- `pypi yank` the published version with a reason field.
- Mark GHCR image as deprecated (cannot fully delete due to immutable
  digests but can remove tags); communicate via GitHub Discussion.
- Communication: GitHub Discussion announcement and CHANGELOG note.

**Acceptance criteria:** see "Global Acceptance Criteria" below.

## Phasing

| Phase | Duration | Pillars | Key deliverables |
| --- | --- | --- | --- |
| **1 — Legal & Identity** | 1–1.5 weeks | 1 | LICENSE, NOTICE, AUTHORS, CHANGELOG, README rewrite, `pyproject.toml` metadata, banner update, `docs-legacy/` audit, `verify_pre_flip.py` skeleton |
| **2 — CI/CD Hardening** | 1–1.5 weeks | 3 | `ci.yml` refactor, codeql/commitlint/dco/dependency-review workflows, mypy strict, pre-commit, Python 3.13 matrix, coverage baseline + floor, MegaLinter expansion |
| **3 — Community & Docs** | 1 week | 2, 5 | CONTRIBUTING/CoC/SECURITY/SUPPORT/GOVERNANCE/ROADMAP, issue and PR templates, CODEOWNERS, `dependabot.yml`, mkdocs-material setup with content migration, `docs.yml` workflow |
| **4 — Supply-Chain & Distribution & Launch** | 1.5–2 weeks | 4, 6, 7 | Scorecard workflow, SBOM toolchain, SLSA workflows, cosign signing, Dockerfile hardening (digest pin, USER, healthcheck, multi-arch), `release.yml` end-to-end, PyPI Trusted Publisher reservation and setup, test release `v0.99.0-rc.1`, pre-flip audit, public flip, `v1.0.0` release |

Total expected effort: 5–6 weeks of solo-maintainer engineering. Phases
are designed to be atomic so that pauses do not require context
re-acquisition.

## Out of Scope

- **Corpus expansion** (additional countries, additional EU acts beyond
  current scope, additional fixture coverage). Tracked separately in
  `plans/full-privacy-corpus/` and as roadmap items.
- **Architectural refactoring** of the MCP and HTTP API beyond what
  Tier C operationally requires (structured logs, healthcheck, version
  endpoint).
- **Multi-maintainer onboarding and voting governance.** Solo BDFL
  remains the model.
- **Commercial offering**, hosting, pricing, SaaS layer.
- **German-language translation** of the documentation site. English
  only at v1.0.0; a German variant can follow if demand justifies it.
- **Performance optimisation** beyond preserving current latency
  characteristics.
- **Distroless or chainguard base image migration.** Deferred to a
  post-v1.0.0 minor release.
- **Custom docs domain** beyond GitHub Pages default URL.

## Risks

| # | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| 1 | Upstream licence conflict surfaces post-flip | very low | high | Verified MIT upstream; Phase 1 includes file-hash audit against upstream commit |
| 2 | PyPI package name collision | low | medium | Early reservation in Phase 4; fallback names defined |
| 3 | Scorecard score below 8 | medium | medium | Pillar 3 and 4 designs are scorecard-aligned; trial run in Phase 2 |
| 4 | CodeQL finds critical findings | medium | medium | Run added in Phase 2; remediation precedes Phase 4 |
| 5 | SBOM toolchain incompatibility with uv lockfile | low | medium | Documented fallback to `uv export` + `cyclonedx-bom` |
| 6 | Release pipeline failure on test tag | medium | low | RC tag mechanism allows iteration; `release-please` isolates release logic |
| 7 | Solo-maintainer bandwidth | medium | high | Atomic phase design; checkpointed acceptance criteria |
| 8 | Data-source licence dispute | low | medium | Repository ships no editorial text; NOTICE pre-states source positions explicitly |

## Global Acceptance Criteria (Public-Flip Day)

- `LICENSE` is Apache-2.0 and `licensee` recognises it; `NOTICE`
  references upstream MIT.
- README renders cleanly with all badges resolving; no "proprietary"
  remnants outside git history.
- GitHub Community Standards checklist is 100% green.
- `v1.0.0` release succeeds end-to-end:
  - PyPI install via `uvx legal-text-mcp-de` works.
  - GHCR image pulls on amd64 and arm64; `cosign verify` returns
    success.
  - Release page carries sdist, wheel, Python SBOM, OCI SBOM, SLSA
    provenance files, and SHA-256 checksums.
- Docs site is reachable; `mike` shows `v1.0.0` aliased to `latest`.
- OpenSSF Scorecard ≥ 8 on the first measurement after flip.
- All required status checks pass on `main`; branch protection blocks
  direct push.

## Open Items Carried Into the Implementation Plan

- Coverage baseline (measured in Phase 2; floor decided then).
- Final PyPI package name confirmed at Phase 4 start.
- Whether to enable Sponsorship link (deferred to launch day; not a
  blocker).
- Whether to apply for OpenSSF Best Practices gold-level beyond the
  silver-level Day-1 application (post-launch decision).
