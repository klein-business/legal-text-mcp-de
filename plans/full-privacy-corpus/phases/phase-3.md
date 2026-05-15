---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 3
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 3: Complete GII discovery coverage

> Part of [full-privacy-corpus](../plan.md)

## Objective

Discover the complete official GII source catalog from
`https://www.gesetze-im-internet.de/gii-toc.xml` and record every TOC item in
the corpus manifest.

## Scope

### Includes

- GII TOC fetch and parse behavior.
- Manifest records for every discovered `<item>` and official `xml.zip` link.
- Discovery count reporting through generated metadata.
- Failure handling for unreachable TOC or malformed TOC payloads.
- Tests with representative TOC fixtures and a required explicit or scheduled
  live discovery gate that records the current TOC count.

### Excludes (deferred to later phases)

- Parsing every GII XML ZIP into norms.
- Runtime exposure of the full GII corpus.
- Relationship graph work.

## Prerequisites

- [ ] Phase 1 manifest contract is complete.
- [ ] Phase 2 generated package format is complete.

## Deliverables

- [ ] GII TOC discovery manifest records.
- [ ] Tests proving `discovered_gii_items` equals fixture TOC item count.
- [ ] Explicit or scheduled network-heavy check for live GII TOC schema and
      count, with persisted output.
- [ ] Documentation of complete GII coverage measurement.

## Acceptance Criteria

- [ ] Every TOC item in the fixture TOC has exactly one manifest record.
- [ ] Discovery does not rely on the old hand-maintained `GERMAN_SOURCES` list.
- [ ] Live discovery can report the current TOC item count without importing all
      payloads.
- [ ] A live or recorded live-gate artifact proves the fetched TOC count used by
      the import run.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 1 | blocked-by | Requires terminal manifest states. |
| Phase 2 | blocked-by | Requires package metadata target. |
| Phase 4 | blocks | Bulk normalization consumes discovered GII source records. |

## Notes

This phase defines "complete GII" as all official TOC entries, not all website
HTML pages or assets.
