---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 8
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 8: German state-law source family inventory

> Part of [full-privacy-corpus](../plan.md)

## Objective

Inventory official source options for all 16 German state privacy laws and
classify each state for adapter implementation or explicit source limitation.

## Scope

### Includes

- One source-family inventory record per German state.
- Official source URL candidates and source-format classification.
- Adapter class assignment for each state: machine-readable, stable HTML, PDF,
  or limitation-only.
- Reachability and stability checks for machine-readable, stable HTML, and PDF
  sources.
- Manifest limitation records for states without a stable usable official source.

### Excludes (deferred to later phases)

- Full state-law parser implementation.
- Runtime exposure of state-law records.
- Relationship graph links to state-law norms.

## Prerequisites

- [ ] Phase 1 manifest contract is complete.

## Deliverables

- [ ] State-law source inventory covering all 16 states.
- [ ] Source-format classification for each state.
- [ ] Adapter-class grouping that assigns states to Phase 9 or Phase 10.
- [ ] Fixture or manifest records for representative states and limitations.
- [ ] Documentation of state-law source-family constraints.

## Acceptance Criteria

- [ ] Every German state has an explicit inventory outcome.
- [ ] No state is treated as missing without a recorded source limitation.
- [ ] Official source provenance is captured before parser work begins.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 1 | blocked-by | Uses shared manifest and limitation contract. |
| Phase 9 | blocks | Machine-readable and stable HTML adapter work depends on inventory outcomes. |
| Phase 10 | blocks | PDF and limitation handling depends on inventory outcomes. |

## Notes

This phase prevents the later state-law implementation from hiding source
availability uncertainty.
