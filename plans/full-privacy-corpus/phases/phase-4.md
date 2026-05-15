---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 4
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 4: GII bulk normalization and coverage gates

> Part of [full-privacy-corpus](../plan.md)

## Objective

Normalize discovered GII XML ZIP sources into generated law and norm records at
bulk scale, while preserving explicit source failures.

## Scope

### Includes

- Bulk GII normalization over discovered manifest entries.
- Parser coverage for representative GII structural patterns.
- Source failure records for unavailable, unsupported, and parse-failed payloads.
- Generated fixture subset for fast tests.
- Network-heavy sampled bulk import gate.

### Excludes (deferred to later phases)

- DSGVO recitals and EU neighbor acts.
- State-law adapters.
- Relationship graph metadata.
- Runtime performance tuning beyond correctness gates.

## Prerequisites

- [ ] Phase 3 complete GII discovery coverage is complete.

## Deliverables

- [ ] GII bulk normalization path.
- [ ] Representative GII fixture corpus with multiple legal structure patterns.
- [ ] Tests proving imported GII records have stable canonical IDs and
      provenance.
- [ ] Coverage gate that reports imported vs failed GII sources.

## Acceptance Criteria

- [ ] All parseable fixture GII ZIPs produce validated law and norm records.
- [ ] Parse failures are recorded in the manifest instead of being silently
      omitted.
- [ ] Generated full corpus data remains excluded from Git.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 3 | blocked-by | Requires discovered GII source records. |
| Phase 10 | blocks | Runtime coverage APIs need normalized source status. |
| Phase 11 | blocks | Scaling checks need bulk-generated data. |

## Notes

This phase is the core GII import work but still ends with a stable fixture gate.
