---
type: review
entity: implementation-plan-review
plan: "full-privacy-corpus"
phase: 1
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 1 - Manifest and corpus contract foundation

> Reviewing [Phase 1 Implementation Plan](../implementation/phase-1-impl.md)
> Against [Phase 1 Scope](../phases/phase-1.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The implementation plan is close to executable and correctly preserves the current runtime boundary: `NormalizedDataset` still loads only normalized package files, `validate_dataset_package` remains record-package focused, and the proposed manifest tests can be added without rewiring serving startup. However, the plan still leaves two contract-defining areas under-specified: source-family provenance validation and the precedence between manifest `validation_mode` and the validation helper flag. Those gaps matter because Phase 1 is the contract foundation that later source adapters will rely on.

## Scope Alignment

### Findings

- The plan stays within Phase 1 by adding a manifest model, fixtures, tests, and a provenance documentation note without implementing GII discovery, DSGVO bulk import, state-law adapters, or runtime API changes.
- Phase 1 requires a source-family-specific provenance completeness matrix. The implementation plan names provenance requirements and says helpers should be data-driven by `(source_family, terminal_state)`, but the actual required fields listed in Step 2 are generic terminal-state fields rather than the concrete GII, EUR-Lex/Cellar, state-law, and third-party-scope matrix from the plan.

## Technical Feasibility

### Findings

- Creating `mcp/legal_texts/manifest.py` is feasible and consistent with the current codebase. Existing `mcp/legal_texts/validation.py` validates normalized law/norm records only, and `mcp/legal_texts/dataset.py` does not currently consume a corpus manifest, so direct manifest unit tests are the right Phase 1 integration point.
- The proposed canonical ID checks align with the current `LawRegistry.validate` collision behavior while correctly avoiding runtime registry changes in this phase.
- The validation API is ambiguous: the manifest schema includes `validation_mode` (`discovery` or `terminal`), while Step 2 also adds `validate_corpus_manifest(..., require_terminal_states: bool = True)`. The plan does not define which source of truth wins when they disagree, so an implementation could accidentally accept a `terminal` manifest in discovery mode or reject a valid `discovery` manifest under the default flag.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Introduce the corpus manifest model | Yes | Mostly | Top-level schema lists the envelope, but omits the `canonical_ids` and `relationship_sources` sections later introduced in Step 3. |
| 2 | Add manifest validation rules | Mostly | Mostly | Source-family provenance requirements and `validation_mode` precedence need to be explicit. |
| 3 | Define canonical ID and alias policy checks | Mostly | Yes | Required cases are clear, but the exact schema shape for `canonical_ids` and `relationship_sources` should be added to Step 1. |
| 4 | Add representative manifest fixtures | Yes | Yes | Fixture coverage is concrete and appropriately small. |
| 5 | Add contract tests and documentation note | Yes | Yes | Tests and docs target the right files and preserve existing fixture dataset tests. |

## Required Context Assessment

### Missing Context

- `mcp/legal_texts/data/laws.v1.json` - useful for preserving existing hand-authored aliases and canonical IDs when defining alias migration examples.

### Unnecessary Context

- None.

## Testing Plan Assessment

### Test Integrity Check

The plan identifies existing tests that must continue passing, explicitly protects `mcp/tests/test_dataset_validation.py` from semantic weakening, avoids editing existing normalized fixtures merely to satisfy manifest tests, and requires additive manifest tests. It does not propose disabling or weakening existing coverage.

### Test Gaps

- Add explicit tests for disagreement between `validation_mode` and `require_terminal_states` once the intended precedence is defined.
- Add at least one positive and one negative test for each source-family provenance row, not only each terminal state.

### Real-World Testing

The primary verify command runs the full release gate and local E2E script, which is enough integration coverage for Phase 1 because the new manifest is intentionally not wired into runtime loading yet. The focused manifest tests are unit-level by design; the remaining risk is contract completeness, not runtime integration.

## Reference Consistency

### Findings

- All referenced code-anchor files exist in the current repository.
- The implementation plan correctly observes that `SourceKind` currently supports only `gesetze-im-internet` and `eur-lex-cellar`, `NormUnit` currently supports only `par` and `art`, and current package validation does not validate a corpus manifest.

## Reality Check Validation

### Findings

- The Reality Check is accurate for the examined code anchors: `import_snapshot` writes a raw snapshot manifest over static `SOURCE_SPECS`, `validate_dataset_package` only checks normalized package files, and registry alias collision checks do not cover generated source-family ID rules.
- The Reality Check should be extended to mention `mcp/legal_texts/data/laws.v1.json` because the plan relies on preserving existing aliases and canonical IDs while defining migration rules.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Scope / validation contract | The implementation plan does not concretely define the source-family-specific provenance matrix it is supposed to validate. Step 2 lists terminal-state fields but omits required GII fields such as TOC/XML ZIP/source path/stand-date status, EUR-Lex/Cellar CELEX and document metadata, state jurisdiction/source format, and third-party scope robots/terms/target provenance. | Add a data-driven matrix to the implementation plan mapping each source family to required metadata, and require tests that fail when each family-specific field is missing. |
| 2 | Major | Technical feasibility | `validation_mode` and `require_terminal_states` overlap without a defined precedence rule. This can produce inconsistent discovery versus terminal validation behavior. | Define whether `validation_mode` is authoritative, whether the helper flag is removed, or whether mismatches are validation errors; add focused tests for the chosen behavior. |
| 3 | Minor | Step actionability | Step 1's schema contract omits `canonical_ids` and `relationship_sources`, but Step 3 says to add and validate those manifest-level sections. | Add those sections to the Step 1 schema contract with minimal expected shapes so fixtures and validators do not invent incompatible structures. |
| 4 | Minor | Required context | Existing registry data in `mcp/legal_texts/data/laws.v1.json` is not listed as required context even though alias preservation and migration examples depend on current canonical IDs and aliases. | Add the registry data file to Required Context. |

## Recommendations

1. Add the concrete source-family provenance matrix and corresponding positive/negative test expectations.
2. Resolve the `validation_mode` versus `require_terminal_states` precedence before implementation.
3. Add `canonical_ids` and `relationship_sources` to the top-level schema description.
4. Add `mcp/legal_texts/data/laws.v1.json` to Required Context.
