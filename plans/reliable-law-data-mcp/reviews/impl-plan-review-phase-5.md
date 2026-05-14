---
type: review
entity: implementation-plan-review
plan: "reliable-law-data-mcp"
phase: 5
status: final
reviewer: "primary"
created: "2026-05-14"
---

# Implementation Plan Review: Phase 5 - Citation Resolver

> Reviewing [Phase 5 Implementation Plan](../implementation/phase-5-impl.md)
> Against [Phase 5 Scope](../phases/phase-5.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The implementation plan is broadly aligned with the resolver phase and correctly keeps transport wiring out of scope. It is not yet executable without interpretation because subdivision selection lacks a stable response contract and one important missing-subdivision error path is explicitly left as an either/or decision.

## Scope Alignment

### Findings

- The plan stays within Phase 5 by implementing only the shared resolver service, dataset lookup, errors, and golden JSON fixtures. No MCP or HTTP transport work is pulled forward.

## Technical Feasibility

### Findings

- The approach is feasible over the Phase 4 normalized dataset and Phase 3 registry, but subdivision output is under-specified. `contracts.md` defines `SubdivisionRecord`, and the Phase 5 plan says subdivision filters should return precise accesses, yet `CitationResponse` has no field for the selected Absatz/Satz/Nummer/Buchstabe result. Implementers would have to choose between mutating `norm.text`, returning only full norm text, or inventing a new response key.
- The missing-subdivision path is not deterministic. Step 5 allows `NORM_NOT_FOUND` or "a structured subdivision-not-found detail" for a well-formed but absent subdivision. Because the approved Phase 1 error codes do not include a separate subdivision code, the plan must pin one exact behavior and details shape before implementation.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Add Dataset Lookup Layer | Yes | Yes | None. |
| 2 | Implement Citation Request Validation | Yes | Yes | None. |
| 3 | Resolve Law Aliases Through Registry | Yes | Yes | None. |
| 4 | Implement Norm and Child Norm Lookup | Yes | Yes | None. |
| 5 | Implement Subdivision Selection | Partial | Partial | Response shape and absent-subdivision error semantics are unresolved. |
| 6 | Write Golden JSON Fixtures | Yes | Partial | Golden fixtures cannot be exact for subdivision requests until the response shape is fixed. |
| 7 | Add Resolver Error Tests | Yes | Yes | None once Step 5 is clarified. |
| 8 | Document Resolver Service Boundary | Yes | Yes | None. |

## Required Context Assessment

### Missing Context

- `mcp/legal_texts/data/laws.v1.json` should be listed because resolver tests must verify actual committed registry data, not only registry behavior described by Phase 3.

## Testing Plan Assessment

### Test Integrity Check

The plan explicitly forbids disabling, skipping, xfail-ing, deleting, or weakening Phase 2-4 tests and legacy parser/library tests. It also scopes resolver tests to normalized fixtures rather than raw XML or legacy Markdown, which protects the prior-phase boundaries.

### Test Gaps

- Add a resolver integration test that loads the normalized fixture package through the new dataset loader, rather than only constructing in-memory records. Without that test, the resolver and dataset package layout can drift while unit tests still pass.

### Real-World Testing

Phase 5 does not need network or live upstream testing because Phases 2-4 own source fetching and normalization. It still needs a service-level integration test against the generated normalized fixture package to represent the real runtime data path.

## Reality Check Validation

### Findings

- The reality check correctly identifies that the current repository has no resolver service and that MCP migration is deferred. It should add the committed registry artifact as a concrete data anchor because the resolver depends on that file, not only on the registry module.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Contract | `CitationResponse` does not define where selected Absatz/Satz/Nummer/Buchstabe data is returned. | Add a stable optional selection field to `contracts.md` and require Phase 5 goldens to assert it. |
| 2 | Major | Error behavior | Step 5 leaves well-formed but absent subdivision requests as `NORM_NOT_FOUND` or another structured detail. | Pin the behavior to one approved error code and exact `error.details` keys. |
| 3 | Minor | Context | The registry JSON artifact is missing from Required Context. | Add `mcp/legal_texts/data/laws.v1.json` as required context and a reality-check anchor. |
| 4 | Minor | Testing | No explicit resolver integration test loads the normalized fixture package through the dataset loader. | Add a test requirement for the real normalized fixture package path. |

## Recommendations

1. Extend `CitationResponse` with an optional selected subdivision payload and align Phase 5 Step 5/golden tests with it.
2. Define absent subdivision as a deterministic approved error response, preferably `NORM_NOT_FOUND` with `details.missing_component="subdivision"`, `details.parent_norm_id`, and `details.subdivision_path`.
3. Add the registry artifact and normalized fixture package to Phase 5 Required Context and test requirements.
