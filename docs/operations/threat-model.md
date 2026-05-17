# Threat model

This document records the threat model for legal-text-mcp-de using
the STRIDE framework. It is reviewed at each major release.

## Scope

Components in scope:

- **MCP transport** (streamable HTTP, default port 8001).
- **HTTP API** (FastAPI, default port 8080).
- **Dataset loader** (validates and loads `DATASET_PATH` content).
- **Source discovery / generation pipeline**
  (`prepare_data/prepare_gesetze_im_internet.sh` and the runtime
  fetchers in `mcp/legal_texts/`).

Out of scope:

- Underlying Python and uv runtime (assumed trustworthy when
  installed from verified sources).
- The Anthropic MCP SDK (`mcp` PyPI package) — relied upon as a
  trusted dependency; security tracked via Dependabot.
- External sources (gesetze-im-internet.de, EUR-Lex/Cellar) — out of
  scope but their availability and integrity are observed via the
  generation pipeline.

## STRIDE table

### Spoofing

| Threat | Asset | Mitigation |
| --- | --- | --- |
| Malicious MCP client impersonates an authorized integration | MCP transport | The server has no built-in authentication; rely on network-level isolation (localhost-only by default). For network-exposed deployments, place behind an authenticating reverse proxy. |
| Attacker spoofs source URLs in generation pipeline | Dataset content | Source URLs are pinned in code (`mcp/legal_texts/sources.py`); fetched content is SHA-256-hashed and recorded; manifest entries carry the URL the bytes came from. |

### Tampering

| Threat | Asset | Mitigation |
| --- | --- | --- |
| Modification of dataset files at rest | DATASET_PATH content | Dataset loader validates JSON schemas at startup (`STRICT_STARTUP=true` recommended). No in-place modification at runtime; mount read-only in Docker. |
| Modification of release artefacts in transit | PyPI wheel/sdist; GHCR image | PyPI: PEP 740 Sigstore attestations. GHCR: cosign keyless signatures. SLSA-3 provenance attestations verifiable from `slsa-framework/slsa-verifier`. |

### Repudiation

| Threat | Asset | Mitigation |
| --- | --- | --- |
| Maintainer denies origin of a release | Released artefacts | Sigstore certificates tie each signature to a specific GitHub Actions workflow identity in the project repo. SLSA provenance documents the build. |

### Information disclosure

| Threat | Asset | Mitigation |
| --- | --- | --- |
| Server logs leak sensitive request data | Server logs | Structured logging is best-effort; no PII is processed because the data is public legal text and incoming queries do not include user identifiers. Operators may add their own log scrubbing. |
| Stack traces in HTTP responses | HTTP API | FastAPI returns generic 500 responses for unexpected exceptions; detailed traces only in server logs. |

### Denial of service

| Threat | Asset | Mitigation |
| --- | --- | --- |
| Resource exhaustion from large queries | Server | No built-in rate limiting; deploy behind a reverse proxy with limits for network-exposed setups. Search uses bounded result sets. |
| Path traversal in `DATASET_PATH` | Server | Path is validated; only files under the resolved path are read. |

### Elevation of privilege

| Threat | Asset | Mitigation |
| --- | --- | --- |
| Container runs as root | OCI image | The released image runs as UID 10001 (non-root). |
| Arbitrary code execution via malicious dataset | Server | Dataset parsing uses JSON, not pickle or eval. Schema validation rejects unexpected types. |

## Residual risks

- The server has no authentication. Localhost-only or
  proxy-authenticated deployment is the assumed posture.
- Generation pipeline pulls from public sources without TLS pinning
  beyond Python's default certificate validation. Compromise of an
  upstream certificate authority would not be detected by this
  project.

## Review

Reviewed: 2026-05-17 (v2.0.0 GA close).
Next review: at v2.1.0 or any architectural change affecting the MCP
or HTTP surface (notably: new Resource URIs, new Smart Tools, or
changes to the Sampling helpers).
