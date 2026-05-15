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

**Verdict**: Needs Revision

The revised implementation plan is substantially more executable than the prior version: it defines concrete package fields, separates generated-package validation from legacy fixture loading, calls out the current `readiness.json` mismatch, and uses the release gate that includes MCP/HTTP E2E checks. It still needs revision because the relationship target contract now permits `external_source` without defining how that satisfies the phase acceptance rule that targets resolve to official records or source limitations, and the plan does not assign the required documentation deliverables to concrete files or steps.

## Scope Alignment

### Findings

- Phase 2 requires documented generated package, citation-unit, and relationship record schemas. The implementation plan contains schema details in the plan text, but no implementation step or affected module writes those schemas into project documentation.
- Phase 2 acceptance requires relationship targets to resolve to official records or source limitations. Step 4 additionally allows `external_source` targets, but does not define a resolution rule that keeps those targets within the accepted official-record/source-limitation set.
- The plan correctly preserves existing MCP/HTTP behavior and defers relationship lookup APIs, bulk corpus generation, and search performance work to later phases.

## Technical Feasibility

### Findings

- The generated-package detection strategy is feasible with the current loader shape: `NormalizedDataset.__init__` already routes startup through `validate_dataset_package`, and `LegalTextRuntime.from_settings` already surfaces `LegalTextError` details through readiness failure paths.
- Additive citation-unit validation is feasible if implemented as a record-validation path separate from `normalize_unit`, because current `normalize_unit("section")` maps to `par` and the resolver only parses `par`/`art`.
- The relationship validation plan needs a tighter target model. Allowing `external_source` without specifying whether it must resolve through the manifest, a source limitation, or an official record can produce packages that pass schema validation while failing Phase 2 acceptance.
- The package metadata requirement for `content_hashes for package files` is directionally sound, but should specify whether `package.json` is excluded from its own hash set or hashed by a canonicalized/self-excluded rule.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Define generated package metadata and optional files | Partial | Partial | Schema fields are concrete, but documentation file targets are missing and `content_hashes` self-hash behavior is unspecified. |
| 2 | Add additive citation-unit validation | Yes | Yes | Separates generated-record validation from resolver normalization and preserves existing `par`/`art` behavior. |
| 3 | Validate manifest and normalized-record consistency | Yes | Yes | Defines generated-package detection, strict validation entry point, and runtime readiness integration. Execution remains gated on the Phase 1 manifest module existing. |
| 4 | Add relationship record schema validation | Partial | Partial | Enumerates relationship fields and types, but `external_source` target resolution conflicts with or weakens the phase target-resolution acceptance criterion. |
| 5 | Preserve runtime and transport behavior | Yes | Yes | Regression targets are clear and avoid Phase 11 API scope creep. |

## Required Context Assessment

### Missing Context

- `docs/features/source-provenance.md` or the specific documentation file that will receive the generated-package, citation-unit, and relationship schema documentation. Phase 2 deliverables require documented schemas, and the plan should tell implementers where to update them.

### Unnecessary Context

- None material.

## Testing Plan Assessment

### Test Integrity Check

The plan names existing MCP tool and resolver tests that must remain authoritative, preserves `par`/`art` assertions, and explicitly forbids weakening `validate_norms` source requirements. It does not explicitly state that no existing tests may be disabled or weakened generally; because the implementation changes shared validation and runtime startup paths, that should be added to the integrity constraints.

### Test Gaps

- Add explicit negative tests for `relationships.json` records that use `external_source` targets without a corresponding official record, source limitation, or allowed manifest/source resolution.
- Add package hash tests that define and verify the intended `package.json` hashing rule.
- Add a documentation verification target or acceptance check showing that generated package, citation-unit, and relationship schemas were documented in the chosen docs file.

### Real-World Testing

Real-world / integration testing is planned. The primary verify command is `PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`, and the current release script runs `scripts/verify_e2e.py` after pytest, which covers local HTTP and MCP streamable HTTP behavior against the fixture dataset.

## Reference Consistency

### Findings

- `mcp/legal_texts/manifest.py` and `validate_corpus_manifest` are referenced as Phase 1 outputs and are not present in the current repository snapshot. This is acceptable because Phase 2 is explicitly blocked by Phase 1, but execution should re-check that prerequisite before starting Step 3.

## Reality Check Validation

### Findings

- The revised Reality Check accurately records that current validation/loading does not require or consume `readiness.json`.
- The revised Reality Check accurately records the `section` normalization issue and the current resolver's `par`/`art` assumptions.
- The Reality Check does not mention the documentation gap even though `docs/features/law-loading-and-indexing.md` currently documents only the four-file normalized serving package and Phase 2 deliverables require documented generated-package schemas.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Scope Alignment | Step 4 permits `external_source` relationship targets without defining how they satisfy Phase 2's requirement that targets resolve to official records or source limitations. | Remove `external_source` from Phase 2 targets, or define a strict resolution rule that maps it through the manifest/source-limitation contract and add negative tests for unresolved external targets. |
| 2 | Major | Documentation | The implementation plan does not include concrete documentation edits for the generated package, citation-unit, and relationship schemas required by Phase 2 deliverables. | Add an implementation step or extend Step 1 with exact docs file targets, likely `docs/features/law-loading-and-indexing.md` and/or `docs/features/source-provenance.md`. |
| 3 | Major | Testing | Test integrity constraints do not explicitly state that existing tests must not be disabled or weakened generally. | Add a blanket test-integrity constraint forbidding disabled/weakened existing tests except for explicitly justified requirement changes. |
| 4 | Minor | Technical Feasibility | `content_hashes for package files` does not define whether or how `package.json` hashes itself. | Specify that `package.json` is excluded from `content_hashes`, or define a canonical self-excluded hashing algorithm and test it. |

## Recommendations

1. Tighten the relationship target contract before execution, especially `external_source` handling.
2. Add concrete documentation update targets for the Phase 2 schema deliverables.
3. Strengthen the test-integrity constraints with a general no-disable/no-weaken rule.
4. Define the package hash rule for `package.json`.
