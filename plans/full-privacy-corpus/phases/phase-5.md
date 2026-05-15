---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 5
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 5: Full DSGVO articles and recitals

> Part of [full-privacy-corpus](../plan.md)

## Objective

Expand DSGVO support from selected fixture articles to full official EUR-Lex /
Cellar coverage of articles 1-99 and all recitals.

## Scope

### Includes

- Full DSGVO article coverage from official German-language EUR-Lex/Cellar
  source records.
- DSGVO recitals as first-class citation units.
- Citation resolution and search fixtures for articles and recitals.
- Source metadata for CELEX, Cellar work/expression/document, language,
  retrieval timestamp, and content hash.

### Excludes (deferred to later phases)

- AI Act and Data Act import.
- Relationship graph links between articles, recitals, and topics.
- State-law privacy sources.

## Prerequisites

- [ ] Phase 1 manifest contract is complete.
- [ ] Phase 2 generated package format is complete.

## Deliverables

- [ ] DSGVO full article fixtures and parser coverage.
- [ ] DSGVO recital fixtures and parser coverage.
- [ ] Resolver tests for `dsgvo_eu_2016_679/art:*` and
      `dsgvo_eu_2016_679/recital:*`.
- [ ] Documentation update describing article and recital citation units.

## Acceptance Criteria

- [ ] DSGVO articles 1-99 resolve in generated corpus checks.
- [ ] DSGVO recitals resolve as citation units.
- [ ] Existing selected DSGVO article behavior remains backwards compatible.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 1 | blocked-by | Requires shared provenance and manifest states. |
| Phase 2 | blocked-by | Requires package support for new citation units. |
| Phase 7 | blocks | Relationship graph needs articles and recitals. |

## Notes

This phase uses official EUR-Lex/Cellar text, not `dsgvo-gesetz.de` editorial
content.
