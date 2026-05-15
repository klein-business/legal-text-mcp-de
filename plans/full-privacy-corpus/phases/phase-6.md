---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 6
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 6: EU neighbor acts source family

> Part of [full-privacy-corpus](../plan.md)

## Objective

Add official EUR-Lex/Cellar source support for EU privacy and digital neighbor
acts discovered from the target privacy corpus, including AI Act and Data Act
where German official text is available.

## Scope

### Includes

- Source-family contract for additional EU acts.
- CELEX/Cellar metadata requirements for every imported EU act.
- Representative fixtures for at least AI Act and Data Act if official German
  sources are reachable.
- Manifest source limitations for discovered EU acts without usable official
  German text.

### Excludes (deferred to later phases)

- Relationship graph between EU acts and DSGVO topics.
- State-law adapters.
- Full text import for every possible EU digital regulation outside the
  discovered target scope.

## Prerequisites

- [ ] Phase 1 manifest contract is complete.
- [ ] Phase 2 generated package format is complete.
- [ ] Phase 5 DSGVO EUR-Lex parser path is complete or reusable.

## Deliverables

- [ ] EU neighbor source records and fixtures.
- [ ] Parser and validation tests for representative EU acts.
- [ ] Source limitation records for unreachable or unsupported official sources.

## Acceptance Criteria

- [ ] AI Act and Data Act resolve from official EUR-Lex/Cellar provenance when
      source text is available.
- [ ] Missing or unsupported official sources are represented as manifest
      limitations, not silent omissions.
- [ ] Existing DSGVO behavior remains unchanged.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 5 | blocked-by | Reuses DSGVO EUR-Lex parsing and metadata patterns. |
| Phase 7 | blocks | Relationship graph can link EU acts after records exist. |

## Notes

This phase should stay bounded to acts discovered from the approved privacy
corpus scope.
