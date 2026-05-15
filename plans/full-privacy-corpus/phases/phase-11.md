---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 11
status: completed
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 11: Runtime coverage and relationship APIs

> Part of [full-privacy-corpus](../plan.md)

## Objective

Expose full-corpus coverage, source limitations, and relationship metadata
through stable MCP and HTTP runtime surfaces while preserving existing tool
behavior.

## Scope

### Includes

- Runtime access to corpus manifest status and source limitations.
- Runtime access to relationship records from the validated Phase 2 package
  schema.
- Additive MCP/HTTP surfaces for corpus coverage and related norms if needed.
- Positive and negative resolver/API tests for new citation units.
- Backwards compatibility tests for existing tools.
- E2E tests against generated fixture package.

### Excludes (deferred to later phases)

- Search ranking changes.
- Full production corpus performance tuning.
- Additional source-family imports.

## Prerequisites

- [x] Phase 2 generated package format is complete.
- [x] Phase 4 GII normalization status is available.
- [x] Phase 7 EU neighbor records and relationship targets are available.
- [x] Phase 9 and Phase 10 state-law outcomes are available.

## Deliverables

- [x] Runtime coverage and source limitation access.
- [x] Related-norm lookup behavior over validated package relationship records
      if approved by implementation planning.
- [x] MCP and HTTP tests for coverage and relationship surfaces.
- [x] Backwards compatibility checks for existing MCP/HTTP tools.
- [x] Negative tests for malformed units, missing relationships, unavailable
      corpus entries, and source limitations.

## Acceptance Criteria

- [x] Existing tools continue to return compatible responses.
- [x] Clients can inspect corpus coverage and source failures.
- [x] Relationship metadata is returned separately from legal text.
- [x] New citation units are accepted or rejected deterministically.
- [x] Local HTTP/MCP E2E passes against representative generated fixture package.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 2 | blocked-by | Requires package metadata and loader support. |
| Phase 6 | blocked-by | Requires approved relationship seed/fallback graph conversion rules. |
| Phase 4 | blocked-by | Requires GII import status and limitations. |
| Phase 7 | blocked-by | Requires EU neighbor and relationship targets. |
| Phase 9 | blocked-by | Requires state-law imported records for preferred source formats. |
| Phase 10 | blocked-by | Requires remaining state-law limitations. |
| Phase 12 | blocks | Scaling phase validates runtime behavior under larger data. |

## Notes

This phase should remain additive unless a versioned API change is explicitly
planned.
