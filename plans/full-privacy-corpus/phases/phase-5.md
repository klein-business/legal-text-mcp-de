---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 5
status: completed
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
- All 173 DSGVO recitals as first-class citation units from the same official
  source family.
- EUR-Lex/Cellar version and consolidation policy for DSGVO, including how
  selected expression/document metadata, corrigenda, amendments, stand/version
  information, and content hashes are recorded.
- Citation resolution and search fixtures for articles and recitals.
- Source metadata for CELEX, Cellar work/expression/document, language,
  retrieval timestamp, and content hash.

### Excludes (deferred to later phases)

- AI Act and Data Act import.
- Relationship graph links between articles, recitals, and topics.
- State-law privacy sources.

## Prerequisites

- [x] Phase 1 manifest contract is complete.
- [x] Phase 2 generated package format is complete.

## Deliverables

- [x] DSGVO full article fixtures and parser coverage.
- [x] DSGVO recital fixtures and parser coverage.
- [x] Official-source check documenting the selected CELEX/Cellar source,
      German language expression, article count, and recital count.
- [x] DSGVO version/consolidation policy record with tests or source checks that
      fail if an unintended German expression/document is selected.
- [x] Resolver tests for `dsgvo_eu_2016_679/art:*` and
      `dsgvo_eu_2016_679/recital:*`.
- [x] Documentation update describing article and recital citation units.

## Acceptance Criteria

- [x] DSGVO articles 1-99 resolve in generated corpus checks.
- [x] DSGVO recitals 1-173 resolve as citation units.
- [x] DSGVO source metadata records the selected CELEX/Cellar expression,
      document, language, version/consolidation policy, and content hash.
- [x] Existing selected DSGVO article behavior remains backwards compatible.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 1 | blocked-by | Requires shared provenance and manifest states. |
| Phase 2 | blocked-by | Requires package support for new citation units. |
| Phase 7 | blocks | Relationship graph needs articles and recitals. |

## Notes

This phase uses official EUR-Lex/Cellar text, not `dsgvo-gesetz.de` editorial
content.
