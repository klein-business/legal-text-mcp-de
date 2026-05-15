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
- Parser-variant fixture matrix for known GII XML structural variants.
- Required explicit or scheduled full-discovery terminal-state coverage gate.
- Critical named GII privacy-law import checks for BDSG and TDDDG.

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
- [ ] Parser-variant matrix documenting covered GII XML structures and examples.
- [ ] Tests proving imported GII records have stable canonical IDs and
      provenance.
- [ ] Coverage gate that reports terminal state for every discovered GII source.
- [ ] Critical-law gate proving BDSG and TDDDG import successfully from GII
      provenance or emit explicit release-blocking upstream source limitations.

## Acceptance Criteria

- [ ] All parseable fixture GII ZIPs produce validated law and norm records.
- [ ] Parse failures are recorded in the manifest instead of being silently
      omitted.
- [ ] Full-discovery coverage gate proves every discovered GII source has exactly
      one terminal state.
- [ ] BDSG and TDDDG generated records resolve from the normalized package with
      GII provenance, unless a release-blocking source limitation is recorded.
- [ ] Sampled parser checks are used only for parser regression coverage, not as
      proof of full corpus completeness.
- [ ] Generated full corpus data remains excluded from Git.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 3 | blocked-by | Requires discovered GII source records. |
| Phase 10 | blocks | Runtime coverage APIs need normalized source status. |
| Phase 11 | blocks | Scaling checks need bulk-generated data. |

## Notes

This phase is the core GII import work but still ends with a stable fixture gate.
