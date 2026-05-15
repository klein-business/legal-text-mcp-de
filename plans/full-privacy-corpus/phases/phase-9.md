---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 9
status: completed
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 9: German state-law machine-readable and HTML adapters

> Part of [full-privacy-corpus](../plan.md)

## Objective

Implement state-law adapters for jurisdictions whose Phase 8 inventory classifies
their official privacy-law sources as machine-readable or stable HTML.

## Scope

### Includes

- Machine-readable state-law adapters identified by Phase 8.
- Stable HTML state-law adapters identified by Phase 8.
- Normalized law and norm records for supported adapter classes.
- Representative fixtures for each implemented adapter class.
- Citation ID tests that encode state jurisdiction.

### Excludes (deferred to later phases)

- PDF-only state-law sources.
- Limitation-only states without usable official sources.
- Runtime related-norm API exposure.

## Prerequisites

- [x] Phase 8 state-law inventory is complete.

## Deliverables

- [x] Official source adapters for machine-readable state-law sources.
- [x] Official source adapters for stable HTML state-law sources.
- [x] State-law normalized fixtures for supported adapter classes.
- [x] Validation tests for state-law provenance and citation IDs.

## Acceptance Criteria

- [x] Every machine-readable or stable HTML state from Phase 8 has imported
      records or a justified source limitation if implementation proves
      infeasible.
- [x] State-law canonical IDs encode jurisdiction clearly.
- [x] State-law records do not collide with GII or EUR-Lex records.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 8 | blocked-by | Requires official source inventory and adapter grouping. |
| Phase 11 | blocks | Runtime APIs should expose imported state-law records. |

## Notes

This phase is intentionally split from PDF and limitation handling to keep a
single execution session realistic.
