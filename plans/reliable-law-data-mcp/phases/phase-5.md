---
type: planning
entity: phase
plan: "reliable-law-data-mcp"
phase: 5
status: completed
created: "2026-05-14"
updated: "2026-05-14"
---

# Phase 5: Citation Resolver

> Part of [reliable-law-data-mcp](../plan.md)

## Objective

Implement precise citation resolution over normalized data without legal interpretation or guessed fallback logic. The resolver must return structured JSON for exact citations and machine-readable errors for invalid, missing, or ambiguous inputs.

## Scope

### Includes

- `resolve_citation(code, unit, paragraph_or_article, child_unit?, child_value?, absatz?, satz?, nummer?, buchstabe?)`.
- Support for `§` and `Art.` norm addressing.
- Canonical identifier grammar from [contracts.md](../contracts.md), including `par:{value}`, `art:{value}`, suffix norms, invalid ranges, and subdivision paths.
- Article-plus-section resolver behavior for `egbgb/art:246a/par:1` and user input `EGBGB Art. 246a § 1`.
- Subdivision lookup for Absatz, Satz, Nummer, and Buchstabe where normalized data supports it.
- Controlled suggestions for ambiguous aliases.
- `LAW_NOT_FOUND`, `NORM_NOT_FOUND`, `AMBIGUOUS_LAW_ALIAS`, and `INVALID_CITATION` behavior.
- Golden JSON tests for all required citation fixtures.

### Excludes (deferred to later phases)

- Search ranking and search snippets.
- Legal advice or legal assessment.
- LLM-driven citation parsing.
- HTTP and MCP transport wiring except shared service-level resolver code.

## Prerequisites

- [x] Phase 3 alias registry is complete.
- [x] Phase 4 normalized records and validation are complete.
- [x] Canonical citation grammar is fixed by Phase 1 contracts.

## Deliverables

- [x] Resolver service/function with structured request and response models.
- [x] Machine-readable error payloads for invalid citation cases.
- [x] Golden JSON outputs for required fixture citations.
- [x] Tests for exact hits, missing laws, missing norms, ambiguous aliases, and invalid subdivisions.

## Acceptance Criteria

- [x] Required citations resolve to canonical law ID, display name, source metadata, URL, full text, and requested subdivisions.
- [x] EGBGB `Art. 246a`, DSGVO article fixtures, suffix norms such as UWG `§ 5a`, and invalid range requests are covered by golden JSON or error fixtures.
- [x] `EGBGB Art. 246a` returns structural container metadata and child references; `EGBGB Art. 246a § 1` returns text-bearing golden JSON.
- [x] Structured request `resolve_citation(code="EGBGB", unit="art", paragraph_or_article="246a", child_unit="par", child_value="1")` is covered by golden tests.
- [x] Ambiguous aliases produce suggestions and do not select a law silently.
- [x] Missing norms return `NORM_NOT_FOUND` with enough context for clients to recover.
- [x] Invalid citation shape returns `INVALID_CITATION`.
- [x] The resolver never fabricates legal text or legal meaning.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 3 | blocked-by | Needs alias resolution. |
| Phase 4 | blocked-by | Needs normalized norms and subdivisions. |
| Phase 7 | blocks | MCP `resolve_citation` wraps this service. |
| Phase 8 | blocks | HTTP norm lookup can reuse resolver behavior. |

## Notes

- The resolver should be transport-independent so MCP and HTTP layers share exactly the same behavior.
