---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 11
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 11: Scaling, search, and operational corpus gates

> Part of [full-privacy-corpus](../plan.md)

## Objective

Validate that generated corpus packages can be built, loaded, searched, and
served at production-corpus scale without making PR CI slow or flaky.

## Scope

### Includes

- Runtime package loading benchmarks for larger generated datasets.
- Search index behavior over larger fixture or generated packages.
- Network-heavy corpus gate definitions.
- Scheduled or explicit full-corpus smoke-check workflow.
- Dataset exclusion and artifact handling rules.

### Excludes (deferred to later phases)

- Adding new source families.
- Changing legal-text semantics.
- Hosted production deployment.

## Prerequisites

- [ ] Phase 4 GII bulk normalization is complete.
- [ ] Phase 10 runtime coverage APIs are complete.

## Deliverables

- [ ] Corpus-scale benchmark criteria.
- [ ] Fast CI remains fixture-backed.
- [ ] Network-heavy corpus checks are runnable outside ordinary PR CI.
- [ ] Search and runtime behavior are validated against a larger package.

## Acceptance Criteria

- [ ] PR CI does not require full corpus download/import.
- [ ] Full-corpus smoke checks can run explicitly or on schedule.
- [ ] Runtime load/search behavior meets documented thresholds or triggers a
      package-format decision.
- [ ] Generated production data remains excluded from Git.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 4 | blocked-by | Needs bulk-generated GII data path. |
| Phase 10 | blocked-by | Needs runtime surfaces for coverage and readiness. |
| Phase 12 | blocks | Release docs should reflect operational gate behavior. |

## Notes

This phase decides whether JSON remains sufficient or whether sharded JSONL or
SQLite-backed lookup is required.
