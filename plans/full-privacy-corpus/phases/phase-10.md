---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 10
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 10: German state-law PDF adapters and source limitations

> Part of [full-privacy-corpus](../plan.md)

## Objective

Handle state-law privacy sources that Phase 8 classifies as PDF-only,
unstructured, unstable, or limitation-only.

## Scope

### Includes

- PDF source adapter only where official source stability and extraction quality
  meet the manifest/provenance contract.
- Source limitation records for states without usable official sources.
- Fixtures for one supported PDF extraction class if implemented.
- Negative tests for unsupported or unstable source formats.

### Excludes (deferred to later phases)

- Machine-readable and stable HTML state sources already handled by Phase 9.
- Runtime related-norm API exposure.
- Manual transcription of legal text.

## Prerequisites

- [ ] Phase 8 state-law inventory is complete.
- [ ] Phase 9 machine-readable and stable HTML adapter outcomes are known.

## Deliverables

- [ ] PDF adapter or explicit limitation for every remaining state.
- [ ] Source limitation records for unsupported states.
- [ ] Tests proving unsupported sources are visible as limitations.
- [ ] Updated state-law coverage summary.

## Acceptance Criteria

- [ ] Every one of 16 states has either imported records or an explicit source
      limitation after Phases 9 and 10.
- [ ] No state-law text is manually transcribed or invented.
- [ ] PDF extraction, if implemented, records official source URL, content hash,
      extraction method, and parser version.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 8 | blocked-by | Requires source classification. |
| Phase 9 | blocked-by | Handles preferred adapter classes first. |
| Phase 11 | blocks | Runtime APIs should expose final state-law coverage. |

## Notes

This phase closes state-law coverage without pretending every state necessarily
has an equally parseable source.
