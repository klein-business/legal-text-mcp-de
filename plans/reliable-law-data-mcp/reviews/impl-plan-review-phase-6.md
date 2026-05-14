---
type: review
entity: implementation-plan-review
plan: "reliable-law-data-mcp"
phase: 6
status: final
reviewer: "primary"
created: "2026-05-14"
---

# Implementation Plan Review: Phase 6 - Search Index and Result Contract

> Reviewing [Phase 6 Implementation Plan](../implementation/phase-6-impl.md)
> Against [Phase 6 Scope](../phases/phase-6.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The plan is correctly scoped to a shared normalized search service and addresses the known legacy defects around HTML snippets, swallowed query errors, and display-code URL inference. It still leaves core query semantics under-specified, which would make implementation and golden search tests drift.

## Scope Alignment

### Findings

- The plan stays within Phase 6 and does not migrate MCP or HTTP transports early.
- Adding `INVALID_QUERY` is consistent with Phase 6's safe query handling requirement, but the phase document should mention it so the gated scope and shared contract stay aligned.

## Technical Feasibility

### Findings

- The selected deterministic token index is feasible for Phase 1 fixtures and avoids backend rank instability.
- The plan does not define whether multi-token queries use AND, OR, phrase matching, or another matching rule. It also does not define how token occurrences are counted for scoring once those match semantics are chosen. That gap directly affects result sets, snippets, scores, and golden JSON.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Define Search Models and Configuration | Partial | Partial | Public score formula references token frequency but does not define token match semantics. |
| 2 | Build Search Index from Normalized Dataset | Yes | Yes | None. |
| 3 | Implement Query Validation and Tokenization | Partial | Partial | Tokenization is described, but no matching semantics are pinned. |
| 4 | Resolve Selected Law Filters Through Registry | Yes | Yes | None. |
| 5 | Generate Plain-Text Snippets | Partial | Partial | Snippet anchor depends on undefined multi-token matching behavior. |
| 6 | Score and Sort Deterministically | Partial | Partial | Score normalization is defined, raw score calculation is not precise enough. |
| 7 | Validate Serving Dataset Readiness | Yes | Yes | None. |
| 8 | Write Search Goldens and Regression Tests | Partial | Partial | Goldens cannot be stable until query semantics and scoring inputs are fixed. |
| 9 | Document Search Service Boundary | Yes | Yes | None. |

## Required Context Assessment

### Missing Context

- None.

### Unnecessary Context

- None.

## Testing Plan Assessment

### Test Integrity Check

The plan preserves Phase 2-5 tests and keeps legacy parser/library tests separate until Phase 7. This is appropriate.

### Test Gaps

- Add tests for deterministic multi-token query behavior once the contract is pinned.

### Real-World Testing

The plan includes the right service-level integration path by building the index from the normalized fixture package. No live upstream testing is needed in this phase.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Search semantics | Multi-token query matching and raw score calculation are undefined. | Pin Phase 1 to explicit tokenization, AND/OR/phrase behavior, occurrence counting, and snippet anchor rules in `contracts.md` and the Phase 6 implementation plan. |
| 2 | Minor | Scope consistency | `INVALID_QUERY` was added to the shared contract but not reflected in `phase-6.md`. | Add it to Phase 6 deliverables or acceptance criteria. |

## Recommendations

1. Define exact Phase 1 search semantics before implementation.
2. Update Phase 6 scope text to mention `INVALID_QUERY`.
