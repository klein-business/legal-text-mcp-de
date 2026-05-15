---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 7
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 7: DSGVO scope graph and relationships

> Part of [full-privacy-corpus](../plan.md)

## Objective

Represent the `dsgvo-gesetz.de`-style scope graph as provenance-backed
relationship metadata without copying unlicensed third-party editorial text.

## Scope

### Includes

- Scope graph discovery rules subject to terms, robots policy, and provenance
  constraints.
- Relationship record contract for article, recital, topic, law, and neighbor
  act links.
- Fixtures for article-to-recital, article-to-topic, and law-to-neighbor
  relationships.
- Validation that relationship metadata is separate from official legal text.

### Excludes (deferred to later phases)

- Importing state-law texts.
- Runtime related-norm API exposure.
- Copying third-party commentary or explanatory editorial text.

## Prerequisites

- [ ] Phase 5 full DSGVO articles and recitals are complete.
- [ ] Phase 6 EU neighbor acts source family is complete enough for linked EU
      act records.

## Deliverables

- [ ] Relationship record schema and fixtures.
- [ ] Scope graph manifest records with source provenance.
- [ ] Tests proving relationships cannot masquerade as official legal text.
- [ ] Documentation of official text vs curated relationship metadata.

## Acceptance Criteria

- [ ] Discovered scope links are either mapped to official records, recorded as
      official-source limitations, or stored as third-party relationship
      metadata with provenance.
- [ ] No third-party editorial text is included as normalized legal text without
      a license-compatible basis.
- [ ] Relationship fixtures validate independently of text-bearing norms.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 5 | blocked-by | Needs DSGVO article and recital records. |
| Phase 6 | blocked-by | Needs EU neighbor records where available. |
| Phase 10 | blocks | Runtime relationship APIs depend on this schema. |

## Notes

This phase is about graph metadata, not legal advice or interpretation.
