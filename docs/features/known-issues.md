---
type: documentation
entity: feature
feature: "known-issues"
version: 1.1
---

# Feature: known-issues

> Part of [legal-text-mcp-de](../overview.md)

## Current Phase 1 Limits

- Phase 1 supports a focused legal-audit fixture set, not every German law.
- EGBGB `Art. 246a` is a structural container. The text-bearing child fixture is `Art. 246a § 1`, represented as `egbgb/art:246a/par:1`.
- Fine-grained subdivision parsing is conservative. If a subdivision cannot be extracted deterministically, the full norm text is preserved and the limitation is represented as structured known-issue metadata.
- Search is deterministic plain-text search with normalized public scores, not legal relevance ranking.
- DSGVO provenance is separate from GII and uses Cellar XML; it is not imported through the German-law source pipeline.
- The HTTP API is local/server-side read-only infrastructure. It is not a SaaS API surface with accounts, billing, authorization, or tenant isolation.
- No tool performs legal advice, legal classification, or hallucinated fallback generation.

## Known Invalid Source Paths

The source matrix intentionally checks invalid upstream paths so alias handling cannot accidentally become URL generation:

- `tddsg` is a historical/user alias; the valid GII source path is `ttdsg`.
- `pangv` is a user/display alias; the valid GII source path is `pangv_2022`.
