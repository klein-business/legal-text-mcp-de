---
type: review
entity: implementation-plan-review
plan: "reliable-law-data-mcp"
phase: 4
status: final
reviewer: "general"
created: "2026-05-14"
---

# Implementation Plan Review: Phase 4 - Structured Normalization and Validation

> Reviewing [Phase 4 Implementation Plan](../implementation/phase-4-impl.md)
> Against [Phase 4 Scope](../phases/phase-4.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Ready

The Phase 4 implementation plan is now executable without material guessing. The revised plan stays within the Phase 4 boundary, gives concrete parser/normalizer and validation steps, preserves the Phase 7 runtime/MCP migration boundary, and addresses the prior blocking findings around DSGVO source selection, stage-aware readiness, fixture coverage, subdivision behavior, end-to-end verification, and test integrity.

## Scope Alignment

### Findings

No scope findings.

Phase 4 is limited to normalized dataset production, validation, fixture artifacts, parser coverage documentation, and normalized-dataset readiness. Resolver behavior, search indexing, MCP migration, HTTP endpoints, and runtime replacement remain explicitly deferred to later phases, matching `phase-5.md`, `phase-6.md`, and `phase-7.md`.

## Technical Feasibility

### Findings

No technical feasibility findings.

The plan correctly treats official German-law XML ZIPs and DSGVO Formex XML as separate source kinds. It also aligns with the current codebase reality: existing `mcp/parser.py` and `mcp/server.py` are legacy Markdown/runtime surfaces, while Phase 4 creates a new normalized data layer for later phases.

## Prior Finding Verification

| Prior Area | Status | Verification |
| ---------- | ------ | ------------ |
| DSGVO article source | Fixed | `source-matrix.md` and Phase 4 Step 3 require German Cellar expression `0004.02` `DOC_2` for article extraction, with `DOC_1` treated only as metadata/TOC if stored. Tests must reject metadata-only `DOC_1` and Dutch `0017.02` as article fixtures. |
| Readiness semantics | Fixed | `contracts.md` now defines `normalized_dataset` and `serving_dataset` stages. Phase 4 may emit only normalized-dataset readiness; serving-ready remains blocked until Phase 6 search index validation. |
| Fixture coverage | Fixed | Step 7 enumerates every `fixture-inventory.md` citation, including all BDSG fixtures and all DSGVO article fixtures, and the testing plan requires coverage assertions against the inventory. |
| Subdivision behavior | Fixed | Step 5 defines conservative mappings for Absatz, Satz, Nummer, and Buchstabe and requires `SUBDIVISION_UNPARSED` known-issue output with full parent text where parsing is unsafe. |
| Verify command depth | Fixed | The verify command includes new normalizer and validation tests, and the test matrix requires an end-to-end normalizer coordinator path from raw manifest fixtures to written normalized package, validation summary, and normalized readiness output. |
| Existing tests | Fixed | The test integrity section explicitly forbids disabling, skipping, xfail-ing, deleting, or weakening Phase 2/3 tests and existing legacy parser/library tests to make Phase 4 pass. |

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Finalize Normalized Models and Readiness Types | Yes | Yes | None. |
| 2 | Parse German GII XML ZIP Snapshots | Yes | Yes | None. |
| 3 | Parse DSGVO Formex Act XML Separately | Yes | Yes | None. |
| 4 | Implement EGBGB Article Container and Child Normalization | Yes | Yes | None. |
| 5 | Parse Subdivisions Conservatively | Yes | Yes | None. |
| 6 | Validate Normalized Dataset Packages | Yes | Yes | None. |
| 7 | Write Normalized Fixtures and Dataset Package Layout | Yes | Yes | None. |
| 8 | Document Normalization Coverage and Known Limits | Yes | Yes | None. |

## Required Context Assessment

### Missing Context

None.

### Unnecessary Context

None material. The later phase files are useful boundary checks, not scope creep.

## Testing Plan Assessment

### Test Integrity Check

The plan now explicitly protects existing tests and prior-phase tests from being disabled, skipped, xfailed, deleted, or weakened. It also distinguishes legacy parser/library behavior, which remains unchanged during Phase 4, from new normalization tests that capture replacement behavior for later phases.

### Test Gaps

No remaining test gaps.

The primary verify command covers new GII normalization, DSGVO normalization, dataset validation, prior registry/source-import/source-matrix tests, and existing parser/library tests. The test matrix requires complete fixture inventory coverage, subdivision known-issue behavior, readiness states, URL regressions, and an end-to-end raw-fixture-to-normalized-package validation path.

### Real-World Testing

Real-world testing is adequately planned for this phase through committed raw XML fixture extracts that must reflect representative GII ZIP/Formex structures, plus Phase 2's live source probe boundary for upstream availability. This is appropriate because Phase 4 parser behavior should be deterministic in CI while still grounded in real source artifacts.

## Reality Check Validation

### Findings

No reality-check findings.

The implementation plan accurately records the current repository mismatch: there is no existing XML normalizer, current runtime parsing is Markdown-only, `LawLibrary.get` still constructs legacy URLs from display codes, and MCP runtime migration remains deferred. The plan also records the source-shape anchors needed for GII XML, EGBGB container/child records, and DSGVO `DOC_2`.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| - | - | - | No findings. | Proceed with Phase 4 implementation. |

Severity counts: Critical 0, Major 0, Minor 0, Note 0.

## Recommendations

1. Proceed with Phase 4 implementation as written.
