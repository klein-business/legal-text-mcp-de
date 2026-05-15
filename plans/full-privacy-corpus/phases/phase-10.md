---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 10
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 10: Runtime coverage and relationship APIs

> Part of [full-privacy-corpus](../plan.md)

## Objective

Expose full-corpus coverage, source limitations, and relationship metadata
through stable MCP and HTTP runtime surfaces while preserving existing tool
behavior.

## Scope

### Includes

- Runtime access to corpus manifest status and source limitations.
- Runtime access to relationship records.
- Additive MCP/HTTP surfaces for corpus coverage and related norms if needed.
- Backwards compatibility tests for existing tools.
- E2E tests against generated fixture package.

### Excludes (deferred to later phases)

- Search ranking changes.
- Full production corpus performance tuning.
- Additional source-family imports.

## Prerequisites

- [ ] Phase 2 generated package format is complete.
- [ ] Phase 4 GII normalization status is available.
- [ ] Phase 7 relationship records are available.
- [ ] Phase 9 state-law adapter outcomes are available or explicitly deferred.

## Deliverables

- [ ] Runtime coverage and source limitation access.
- [ ] Related-norm lookup behavior if approved by implementation planning.
- [ ] MCP and HTTP tests for coverage and relationship surfaces.
- [ ] Backwards compatibility checks for existing MCP/HTTP tools.

## Acceptance Criteria

- [ ] Existing tools continue to return compatible responses.
- [ ] Clients can inspect corpus coverage and source failures.
- [ ] Relationship metadata is returned separately from legal text.
- [ ] Local HTTP/MCP E2E passes against representative generated fixture package.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 2 | blocked-by | Requires package metadata and loader support. |
| Phase 7 | blocked-by | Requires relationship records. |
| Phase 11 | blocks | Scaling phase validates runtime behavior under larger data. |

## Notes

This phase should remain additive unless a versioned API change is explicitly
planned.
