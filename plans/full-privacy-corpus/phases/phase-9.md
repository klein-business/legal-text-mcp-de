---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 9
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 9: German state-law adapters and limitations

> Part of [full-privacy-corpus](../plan.md)

## Objective

Implement official source adapters or explicit source limitations for all 16
German state privacy laws identified in the inventory.

## Scope

### Includes

- State-law parser adapters based on Phase 8 source-format classes.
- Normalized law and norm records for parseable official state-law sources.
- Source limitation records for states without usable official sources.
- Representative fixtures for each adapter class.

### Excludes (deferred to later phases)

- Relationship graph links from DSGVO topics to state-law norms unless already
  represented by existing relationship fixtures.
- Hosted production corpus generation.
- Legal advice or legal interpretation over state-law content.

## Prerequisites

- [ ] Phase 8 state-law inventory is complete.

## Deliverables

- [ ] Official source adapter or limitation for each of 16 states.
- [ ] State-law normalized fixtures for supported adapter classes.
- [ ] Validation tests for state-law provenance and citation IDs.
- [ ] Source limitation tests for unsupported states.

## Acceptance Criteria

- [ ] Every state has either imported records or an explicit source limitation.
- [ ] State-law canonical IDs encode jurisdiction clearly.
- [ ] State-law records do not collide with GII or EUR-Lex records.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 8 | blocked-by | Requires official source inventory. |
| Phase 10 | blocks | Runtime APIs should expose imported state-law records. |

## Notes

If implementation plans find this phase too large for one session, split it by
adapter class or state groups before execution.
