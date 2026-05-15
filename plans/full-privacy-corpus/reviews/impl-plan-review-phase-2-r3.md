---
type: review
entity: implementation-plan-review
plan: "full-privacy-corpus"
phase: 2
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 2 - Generated package format and runtime compatibility

> Reviewing [Phase 2 Implementation Plan](../implementation/phase-2-impl.md)
> Against [Phase 2 Scope](../phases/phase-2.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Ready

The r2 revisions address the previously blocking issues: relationship targets are now limited to official records or source limitations, documentation updates have concrete file targets, package hash self-reference is resolved by excluding `package.json`, and the test integrity constraints now explicitly forbid disabling or weakening existing tests. The implementation plan is concrete enough to execute once the declared Phase 1 prerequisite is present.

## Scope Alignment

### Findings

- The plan now covers all Phase 2 deliverables: generated package metadata, manifest/readiness/source-limitation/relationship files, backwards-compatible legacy package loading, additive citation-unit validation, runtime readiness failure semantics, small fixtures, validation tests, and documentation.
- The plan stays within Phase 2 by preserving MCP/HTTP tool behavior and deferring relationship lookup APIs, large production datasets, GII bulk import, and search tuning to later phases.

## Technical Feasibility

### Findings

- The generated-package detection approach aligns with the current loader path: `NormalizedDataset.__init__` already calls `validate_dataset_package`, and `LegalTextRuntime.from_settings` already surfaces startup `LegalTextError` details through readiness failures.
- The additive citation-unit plan is feasible because it explicitly avoids changing resolver normalization in this phase; current `normalize_unit("section")` maps to `par`, and resolver parsing remains limited to existing `par`/`art` behavior.
- The relationship validation plan is now technically coherent: Phase 2 targets are only `law`, `norm`, or `source_limitation`, and unresolved `external_source` targets are explicitly rejected.
- The package hash rule is actionable because `content_hashes` excludes `package.json` and has a required test case.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Define generated package metadata and optional files | Yes | Yes | Clear package fields, generated-vs-legacy trigger, readiness caveat, and hash rule. |
| 2 | Add additive citation-unit validation | Yes | Yes | Correctly separates generated-record validation from current resolver normalization. |
| 3 | Validate manifest and normalized-record consistency | Yes | Yes | Clear entry point and loader/runtime integration; depends on Phase 1 manifest code existing. |
| 4 | Add relationship record schema validation | Yes | Yes | Relationship types, target kinds, provenance, duplicate ID, external target, and no-editorial-text rules are explicit. |
| 5 | Preserve runtime and transport behavior | Yes | Yes | Regression targets preserve existing MCP/HTTP and resolver behavior. |
| 6 | Document generated package schemas | Yes | Yes | Concrete docs targets cover package/citation/readiness and source-limitation/relationship provenance semantics. |

## Required Context Assessment

### Missing Context

- None material. The plan lists the current validation, loader, runtime, resolver, tests, release gate, Phase 1 plan artifacts, and documentation files needed to execute the work.

### Unnecessary Context

- None material.

## Testing Plan Assessment

### Test Integrity Check

The test integrity constraints are adequate. The plan names existing MCP tool and resolver tests that must remain authoritative, preserves `par`/`art` assertions, forbids weakening source validation to make fixtures pass, and explicitly prohibits disabling, skipping, xfail-ing, or weakening existing tests unless a Phase 2 requirement demands a replacement assertion that preserves the behavior boundary.

### Test Gaps

- None blocking. The testing plan covers positive and negative generated-package validation, manifest/record disagreement, malformed units, relationship provenance/type/target errors, unresolved external targets, package hash behavior, legacy loader compatibility, documentation updates, local MCP/HTTP E2E, and regression tests.

### Real-World Testing

Real-world / integration testing is planned. The primary verify command is `PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`; the current release script runs pytest over the fixture suite and then `scripts/verify_e2e.py`, which exercises local HTTP and MCP streamable HTTP behavior against the fixture dataset.

## Reference Consistency

### Findings

- **Note**: `mcp/legal_texts/manifest.py` and `validate_corpus_manifest` are referenced as Phase 1 outputs and are not present in the current repository snapshot. This is consistent with Phase 2 being blocked by Phase 1, but execution should verify that Phase 1 has landed before starting Step 3.

## Reality Check Validation

### Findings

- The Reality Check accurately describes the current code anchors: legacy package validation only checks `laws.json`, `norms.json`, and optionally `search-index.json`; `readiness.json` is written but not consumed; `NormUnit` only includes `par` and `art`; `normalize_unit("section")` maps to `par`; and resolver parsing is currently `par`/`art`-oriented.
- The r2 documentation gap is now reflected both in Step 6 and the Reality Check notes.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Note | Execution Prerequisite | Phase 2 references `mcp/legal_texts/manifest.py` and `validate_corpus_manifest`, which are planned Phase 1 outputs and are not present in the current repository snapshot. | Before executing Phase 2 Step 3, confirm Phase 1 has landed and the manifest validator names still match the Phase 2 implementation plan. |

## Recommendations

1. Proceed with Phase 2 after confirming the Phase 1 manifest contract implementation is present.
