---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 12
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 12: Scaling, search, and operational corpus gates

> Part of [full-privacy-corpus](../plan.md)

## Objective

Validate that generated corpus packages can be built, loaded, searched, and
served at production-corpus scale without making PR CI slow or flaky.

## Scope

### Includes

- Runtime package loading benchmarks for larger generated datasets.
- Search index behavior over larger fixture or generated packages.
- Required explicit or scheduled network-heavy corpus gate definitions.
- Scheduled or explicit full-corpus smoke-check workflow.
- Persisted full-corpus validation evidence bundle.
- Dataset exclusion and artifact handling rules.
- Initial performance thresholds and decision framework.

### Excludes (deferred to later phases)

- Adding new source families.
- Changing legal-text semantics.
- Hosted production deployment.

## Prerequisites

- [ ] Phase 4 GII bulk normalization is complete.
- [ ] Phase 11 runtime coverage APIs are complete.

## Deliverables

- [ ] Corpus-scale benchmark criteria.
- [ ] Fast CI remains fixture-backed.
- [ ] Network-heavy corpus checks are runnable outside ordinary PR CI.
- [ ] Search and runtime behavior are validated against a larger package.
- [ ] Package-format decision record if initial thresholds are missed.

## Acceptance Criteria

- [ ] PR CI does not require full corpus download/import.
- [ ] Full-corpus smoke checks can run explicitly or on schedule.
- [ ] Full-corpus import gate persists manifest artifacts with terminal-state
      coverage for all discovered GII sources.
- [ ] Full-corpus validation bundle persists DSGVO article/recital counts,
      selected expression/document, version/consolidation policy, and content
      hash.
- [ ] Full-corpus validation bundle persists BDSG and TDDDG successful import and
      MCP/HTTP resolution evidence from GII provenance, or a release-blocking
      upstream source limitation.
- [ ] Full-corpus validation bundle persists EU neighbor imported-or-limited
      states.
- [ ] Full-corpus validation bundle persists all 16 state-law imported-or-limited
      outcomes.
- [ ] Full-corpus validation bundle persists relationship graph
      discovered-or-limited records and validation status.
- [ ] Initial runtime load budget is 120 seconds or less on the documented
      benchmark environment, or a package-format migration decision is recorded.
- [ ] Initial sampled search budget is p95 under 1 second on the documented
      benchmark environment, or a search-index migration decision is recorded.
- [ ] Initial runtime memory budget is 2 GB or less on the documented benchmark
      environment, or a package-format migration decision is recorded.
- [ ] Generated production data remains excluded from Git.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 4 | blocked-by | Needs bulk-generated GII data path. |
| Phase 11 | blocked-by | Needs runtime surfaces for coverage and readiness. |
| Phase 13 | blocks | Release docs should reflect operational gate behavior. |

## Notes

This phase decides whether JSON remains sufficient or whether sharded JSONL or
SQLite-backed lookup is required.
