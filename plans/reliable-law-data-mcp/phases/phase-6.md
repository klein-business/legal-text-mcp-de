---
type: planning
entity: phase
plan: "reliable-law-data-mcp"
phase: 6
status: completed
created: "2026-05-14"
updated: "2026-05-14"
---

# Phase 6: Search Index and Result Contract

> Part of [reliable-law-data-mcp](../plan.md)

## Objective

Implement full-text search over normalized laws with a stable JSON result contract, selected-law filtering, safe query handling, deterministic snippets, and scores.

## Scope

### Includes

- Search indexing from normalized norm records.
- All-law and selected-law searches.
- Results containing norm ID, title, snippet, URL, score, law canonical ID, and source metadata as needed.
- Safe handling for query syntax errors.
- Default snippets without HTML fragments; optional highlight field may be added only if deliberately modeled.
- Query normalization, snippet length, normalized public score, and tie-breaking rules from [contracts.md](../contracts.md).
- Search tests with stable fixture expectations.

### Excludes (deferred to later phases)

- HTTP and MCP transport endpoints beyond shared search service behavior.
- Advanced semantic search, embeddings, or ranking beyond deterministic Phase 1 full-text search.
- User-specific search history or tenancy.

## Prerequisites

- [x] Phase 4 normalized records exist.
- [x] Phase 3 registry can validate selected law filters.

## Deliverables

- [x] Search service over normalized data.
- [x] Search result contract and error payloads.
- [x] `INVALID_QUERY` behavior for empty or unsafe search input.
- [x] Deterministic search configuration for query normalization, snippet generation, normalized public score calculation, and tie-breaking.
- [x] Fixture-backed search index tests.
- [x] Regression coverage for avoiding default `<b>` HTML fragments in API output.

## Acceptance Criteria

- [x] Search can run over all loaded laws.
- [x] Search can be restricted to selected canonical law codes.
- [x] Invalid selected laws produce structured law errors.
- [x] Query syntax errors are handled without silent empty success responses.
- [x] Empty, punctuation-only, or otherwise unsafe search input returns `INVALID_QUERY`.
- [x] Result snippets and scores follow the deterministic rules in [contracts.md](../contracts.md), including tie-break sorting by score, canonical law ID, and norm ID.
- [x] Tests do not assert raw backend scores; they assert the normalized public score contract and deterministic ordering.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 3 | blocked-by | Uses canonical law IDs for filtering. |
| Phase 4 | blocked-by | Indexes normalized records. |
| Phase 7 | blocks | MCP `search_laws` wraps this service. |
| Phase 8 | blocks | HTTP `GET /search` wraps this service. |

## Notes

- SQLite FTS5 may remain acceptable if the API contract hides storage-specific markup and query errors.
