---
type: documentation
entity: feature
feature: "scope-and-invariants"
version: 1.4
---

# Feature: scope-and-invariants

> Part of [legal-text-mcp-de](../overview.md)

This file intentionally remains at `docs/features/known-issues.md` so existing
external links continue to resolve. Its content is not an open bug backlog. It
documents product scope, source-system invariants, and compatibility notes that
the runtime and release gate preserve deliberately.

## Scope Boundaries

- The supported scope is the fixture-backed legal-audit dataset documented in
  [supported laws](supported-laws.md), not a complete mirror of every German
  law.
- Search is deterministic lexical search with normalized public scores. It does
  not claim legal relevance ranking.
- The HTTP API is local/server-side read-only infrastructure. Accounts, billing,
  authorization, and tenant isolation remain outside the runtime contract.
- Tools return source text, citations, and metadata. They do not perform legal
  advice, legal classification, or hallucinated fallback generation.
- MCP streamable HTTP must be exercised with an MCP client. A plain request to
  `/mcp` without MCP protocol headers is not a readiness or tool-call check.

## Source Invariants

- EGBGB `Art. 246a` is a structural container. The text-bearing child fixture is
  `Art. 246a § 1`, represented as `egbgb/art:246a/par:1`.
- The upstream GII URL for the EGBGB `Art. 246a` container currently returns
  `404`; the child URL for `Art. 246a § 1` is the verified text-bearing source.
  The container keeps structured source-anomaly metadata instead of inventing a
  working upstream URL. The fixture code for this case is
  `UPSTREAM_CONTAINER_URL_UNAVAILABLE`.
- Fine-grained subdivision parsing is conservative. If a subdivision cannot be
  extracted deterministically, the full norm text is preserved.
- DSGVO provenance is intentionally separate from GII and uses Cellar XML. It is
  not imported through the German-law source pipeline.
- `tddsg` and `pangv` are intentionally invalid GII source paths in the source
  matrix. They are regression checks so aliases cannot silently become upstream
  URLs. The valid paths are `ttdsg` and `pangv_2022`.

## Compatibility Metadata

- API payloads keep the `known_issues` field name for backwards compatibility.
  New entries should describe structured source-anomaly metadata or other
  non-fatal provenance caveats, not unresolved product work.
