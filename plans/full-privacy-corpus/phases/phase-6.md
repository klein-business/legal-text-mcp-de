---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 6
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 6: DSGVO scope policy and seed graph inventory

> Part of [full-privacy-corpus](../plan.md)

## Objective

Make the `dsgvo-gesetz.de`-style scope graph executable by deciding the terms,
robots, licensing, and fallback policy before any source-family implementation
depends on it.

## Scope

### Includes

- Policy decision record for using `dsgvo-gesetz.de` as a scope and relationship
  reference.
- Fallback manually maintained seed graph if automated crawling or reuse is not
  permitted.
- Seed relationship inventory for DSGVO articles, recitals, topics, BDSG, TDDDG,
  LDSG, AI Act, Data Act, and other discovered neighbor resources.
- Transformation rules from approved seed/fallback graph entries into validated
  package relationship records.
- Minimum EU neighbor seed list with CELEX targets:
  `32024R1689` for AI Act and `32023R2854` for Data Act.
- Rules for adding additional EU or German neighbor sources discovered from the
  approved scope graph.

### Excludes (deferred to later phases)

- Importing EU neighbor act full text.
- Importing state-law full text.
- Runtime relationship lookup APIs.
- Copying third-party editorial text.

## Prerequisites

- [ ] Phase 1 manifest contract is complete.
- [ ] Phase 5 full DSGVO articles and recitals are complete.

## Deliverables

- [ ] Scope graph policy decision record.
- [ ] Seed graph manifest or manually maintained fallback graph.
- [ ] Relationship record generation rules that target the Phase 2 package
      schema.
- [ ] Minimum EU neighbor seed list including AI Act and Data Act CELEX IDs.
- [ ] Relationship-source limitation records when automated discovery is not
      permitted.

## Acceptance Criteria

- [ ] Implementation has a permitted discovery path or an explicit fallback seed
      graph before relationship work proceeds.
- [ ] AI Act and Data Act have concrete CELEX identifiers or source limitations.
- [ ] No phase depends on unapproved third-party crawling or copied editorial
      text.
- [ ] Approved seed/fallback graph entries can be converted into package
      relationship records whose targets are official records or source
      limitations.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 1 | blocked-by | Uses shared policy-exclusion and provenance fields. |
| Phase 5 | blocked-by | Needs DSGVO article and recital targets. |
| Phase 7 | blocks | EU neighbor acts consume the seed list. |

## Notes

This phase converts the external website dependency into a governed scope input
instead of a late implementation surprise.
