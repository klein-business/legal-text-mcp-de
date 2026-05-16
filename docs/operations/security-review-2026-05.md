<!--
SPDX-License-Identifier: Apache-2.0
Copyright 2026 klein-business
-->

# Security Review — May 2026

This document records the security review performed at the v1.0.0
public release. It satisfies the OpenSSF Best Practices Gold criterion
`security_review` (a documented security review within the last 5 years).

- **Project**: `legal-text-mcp-de` v1.0.0
- **Commit reviewed**: `main` at 2026-05-16 (tag `v1.0.0`)
- **Reviewer**: Martin Klein (`flitzrrr`, sole maintainer at v1.0.0)
- **Review window**: 2026-05-14 to 2026-05-16
- **Next scheduled review**: 2026-11 (six-month cadence) or before any
  release that introduces auth, persistence, or multi-tenant features

## Scope

The review covers everything published in the v1.0.0 release surface:

- Python package `legal-text-mcp-de` on PyPI (1.0.0) — wheel + sdist
- Container image `ghcr.io/klein-business/legal-text-mcp-de:1.0.0`
  for `linux/amd64` and `linux/arm64`
- Source tree on `main` at the v1.0.0 tag
- GitHub Actions release pipeline (`.github/workflows/release.yml`)
  including PyPI Trusted Publisher, SLSA-3 provenance, cosign keyless,
  Syft + CycloneDX SBOM
- Documentation site at `https://klein-business.github.io/legal-text-mcp-de/`

Out of scope (no implementation in v1.0.0):

- User authentication or session management
- Multi-tenant data isolation
- Persistent storage of user-provided data
- Third-party integrations beyond data sources
  (`gesetze-im-internet.de`, EUR-Lex / Cellar)

## Threat model summary

See [the project `SECURITY.md`](https://github.com/klein-business/legal-text-mcp-de/blob/main/SECURITY.md) for the canonical threat model.
Key points carried forward into this review:

- The runtime is **local or server-side infrastructure** with no SaaS,
  no accounts, no PII processing, no auth.
- The MCP server and HTTP API expose **read-only** access to a
  pre-validated legal-text corpus. No write paths to user-controlled
  storage.
- Data sources are **trusted publishers** (German federal government
  via `gesetze-im-internet.de`, EU institutions via Cellar/EUR-Lex)
  consumed over HTTPS with content-type verification.
- The release pipeline is the security boundary: any compromise must
  go through Trusted-Publisher OIDC, sigstore TUF chain, or branch
  protection.

## Security requirements considered

1. **Confidentiality**: no user-supplied data is persisted; corpus
   data is public-record law text. No confidentiality concerns at the
   application layer.

2. **Integrity**: every release artifact carries cryptographic
   provenance (PEP 740 attestations for PyPI, cosign keyless for
   container, SLSA-3 build provenance for both). The corpus loader
   validates fixtures against a checksum manifest before serving.

3. **Availability**: rate limiting and request validation are
   delegated to the deployment layer (operator's reverse proxy);
   the application does not implement DoS protection itself. This is
   documented in `SECURITY.md`.

4. **Supply-chain integrity**: covered by hardened CI workflows
   (15 third-party actions pinned by SHA), Dependabot security
   updates, Scorecard, CodeQL, Trivy, Gitleaks.

5. **Disclosure / response**: Private Vulnerability Reporting is
   enabled at the org level; SECURITY.md commits to a 14-day initial
   response and a 60-day fix SLA.

## Review activities performed

### Manual code audit

The following modules were read line-by-line for security-relevant
patterns (path traversal, deserialization, command injection,
SSRF, time-of-check / time-of-use):

- `src/legal_text_mcp_de/server.py` — MCP transport entry point
- `src/legal_text_mcp_de/http_api.py` — FastAPI surface
- `src/legal_text_mcp_de/config.py` — pydantic-settings env loading
- `src/legal_text_mcp_de/legal_texts/sources.py` — upstream source
  loading
- `src/legal_text_mcp_de/legal_texts/parser.py` — XML / HTML parsing
- `src/legal_text_mcp_de/legal_texts/normalizer.py` — corpus
  normalisation
- `scripts/verify_pre_flip.py` — pre-release safety gate
- `scripts/verify_uv_runtime_docker.py` — container image gate

**Findings**: none with severity ≥ medium. Two low-severity
observations were filed for the next maintenance window:

- The HTTP API does not currently enforce a request body size limit
  at the FastAPI layer. The operator's reverse proxy is expected to
  do so. Tracked in [#TBD] — `good first issue`.
- The MCP transport does not authenticate the client. This is by
  design for the local-or-server-side deployment model; documented
  in `SECURITY.md` as an operator responsibility. No code change
  needed; documentation already covers it.

### Automated analysis (run on `main` at v1.0.0)

- **CodeQL** extended-suite (`.github/workflows/codeql.yml`): 0
  findings.
- **Trivy** container scan: 0 high/critical CVEs against
  `ghcr.io/klein-business/legal-text-mcp-de:1.0.0`. One transitive
  `rustls-webpki` advisory (GHSA-82j2-j2ch-gfr8) was fixed by bumping
  `uv` from 0.10.12 to 0.11.14 in PR #40.
- **Gitleaks**: 0 leaked secrets on `main`. `detect-secrets` baseline
  in `.secrets.baseline` accounts for known acceptable patterns
  (hashed test fixtures).
- **OpenSSF Scorecard**: monthly run; baseline score ≥ 6 across all
  checks.
- **GitHub Dependency Review**: 0 blocked dependencies on PR #16
  (Phase 3+4 atomic rename) and all subsequent PRs.

### Architecture review

- The Dockerfile runs as non-root UID 10001, uses a pinned base
  image digest, sets `UV_CACHE_DIR=/tmp/uv-cache`, and defines a
  `HEALTHCHECK` against `/health`.
- Branch protection on `main`: 14 required status checks,
  `required_signatures=true`, `required_linear_history=true`,
  `enforce_admins=true`, `required_pull_request_reviews=1`. The sole
  bypass-allowlist entry is the maintainer `flitzrrr`.
- The release pipeline (`release.yml`) uses GitHub OIDC for PyPI
  Trusted Publisher and cosign keyless signing. No long-lived
  credentials are stored in repository secrets.

### Supply-chain review

- All 15 third-party GitHub Actions used in CI are SHA-pinned. The
  pin set was re-verified during the v1.0.0 release (PR #59 corrected
  two fake SHAs that had slipped into `release.yml`).
- Python dependencies are loosely pinned in `pyproject.toml` and
  exactly resolved in `uv.lock`. Dependabot is configured for
  weekly version updates and immediate security updates via the
  `uv` ecosystem.
- The OCI base image (`python:3.12-slim`) is pinned by digest, with
  a documented refresh cadence.

## Mitigations and follow-ups

| # | Item | Action | Owner | Target |
|---|---|---|---|---|
| 1 | HTTP body-size limit | File `good first issue` to add `request_max_body_size` configuration | maintainer | Next minor |
| 2 | Branch-coverage gate | Lift coverage measurement to include branches (`branch=true`) and gate at 80% | maintainer | v1.1.0 |
| 3 | Co-maintainer onboarding | Recruit a second maintainer to enable `two_person_review` | maintainer | 2026 H2 |
| 4 | Six-month review | Re-run this template at 2026-11 with diff against this report | maintainer | 2026-11-16 |

## Conclusion

`legal-text-mcp-de` v1.0.0 is fit for public, server-side deployment.
The threat model is narrow (no PII, no auth, read-only public law
text). Automated analysis (CodeQL, Trivy, Gitleaks, dependency
review) produces zero blocking findings. Release artefacts are
cryptographically attested end-to-end (PEP 740, cosign keyless,
SLSA-3). The two observed gaps are documentation/configuration
matters, not exploitable vulnerabilities.

The project is approved for public release at v1.0.0.

— Martin Klein (`flitzrrr`), 2026-05-16
