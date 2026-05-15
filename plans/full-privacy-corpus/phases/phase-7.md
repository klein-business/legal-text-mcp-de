---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 7
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 7: EU neighbor acts source family

> Part of [full-privacy-corpus](../plan.md)

## Objective

Add official EUR-Lex/Cellar source support for EU privacy and digital neighbor
acts from the approved scope graph, starting with AI Act and Data Act.

## Scope

### Includes

- Source-family contract for additional EU acts.
- Seed CELEX records for AI Act (`32024R1689`) and Data Act (`32023R2854`).
- Language and version policy for official German-language EUR-Lex/Cellar text.
- Representative fixtures for AI Act and Data Act when German official text is
  reachable.
- Manifest source limitations for seeded or discovered EU acts without usable
  official German text.

### Excludes (deferred to later phases)

- Runtime related-norm API exposure.
- State-law adapters.
- Full text import for EU acts outside the approved scope graph.

## Prerequisites

- [ ] Phase 1 manifest contract is complete.
- [ ] Phase 2 generated package format is complete.
- [ ] Phase 5 DSGVO EUR-Lex parser path is complete or reusable.
- [ ] Phase 6 scope policy and seed graph inventory is complete.

## Deliverables

- [ ] EU neighbor source records and fixtures.
- [ ] Parser and validation tests for representative EU acts.
- [ ] Source limitation records for unreachable or unsupported official sources.
- [ ] CELEX/language/version policy documentation.

## Acceptance Criteria

- [ ] AI Act and Data Act resolve from official EUR-Lex/Cellar provenance when
      source text is available.
- [ ] Missing or unsupported official sources are represented as manifest
      limitations, not silent omissions.
- [ ] Additional EU acts are imported only when present in the approved scope
      graph or explicitly added to the seed list.
- [ ] Existing DSGVO behavior remains unchanged.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 5 | blocked-by | Reuses DSGVO EUR-Lex parsing and metadata patterns. |
| Phase 6 | blocked-by | Requires concrete seed graph and policy decision. |
| Phase 11 | blocks | Runtime relationship APIs can link EU acts after records exist. |

## Notes

This phase is bounded by a seed graph and does not create an unbounded EU law
importer.
