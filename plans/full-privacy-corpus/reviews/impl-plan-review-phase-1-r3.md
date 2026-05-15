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

**Verdict**: Ready

The r2 revision resolves the prior material gaps: it now defines `validation_mode` precedence, makes source-family provenance validation concrete, includes the `canonical_ids` and `relationship_sources` manifest sections in the schema contract, and adds the existing registry data file to required context. The plan is executable without guessing and stays within Phase 1 by defining and testing the manifest contract without wiring it into runtime package loading.

## Scope Alignment

### Findings

- The implementation plan covers the gated Phase 1 deliverables: manifest schema, source-family identifiers, terminal-state requirements, provenance matrix, canonical ID/alias/collision policy, representative fixtures, tests, and a source-provenance documentation note.
- The plan avoids deferred work from later phases, including full GII discovery, DSGVO article/recital import, state-law adapters, runtime coverage APIs, and relationship lookup surfaces.
- The affected module list is appropriately narrow for Phase 1 because the only runtime-facing code change is additive contract code and tests under the existing MCP server module.

## Technical Feasibility

### Findings

- Creating `mcp/legal_texts/manifest.py` is technically sound. The current codebase has no corpus manifest validator, while `mcp/legal_texts/validation.py` validates only normalized law/norm package records and `mcp/legal_texts/dataset.py` loads only `laws.json`, `norms.json`, and optional `search-index.json`.
- Keeping broader manifest source-family values (`gii`, `eur-lex-cellar`, `state-law`, `third-party-scope`) separate from serving `SourceKind` is the right boundary for this phase because current serving records only support `gesetze-im-internet` and `eur-lex-cellar`.
- The revised validation-mode rule is feasible and testable: `manifest["validation_mode"]` is authoritative, omitted `require_terminal_states` derives from it, and explicit mismatches return validation errors.
- The canonical ID and relationship-source checks align with current `LawRegistry.validate` behavior while avoiding premature registry/runtime changes.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Introduce the corpus manifest model | Yes | Yes | None. |
| 2 | Add manifest validation rules | Yes | Yes | None. |
| 3 | Define canonical ID and alias policy checks | Yes | Yes | None. |
| 4 | Add representative manifest fixtures | Yes | Yes | None. |
| 5 | Add contract tests and documentation note | Yes | Yes | None. |

## Required Context Assessment

### Missing Context

- None.

### Unnecessary Context

- None.

## Testing Plan Assessment

### Test Integrity Check

The testing plan identifies existing tests that must remain meaningful, explicitly protects `mcp/tests/test_dataset_validation.py` from semantic weakening, avoids editing existing normalized fixtures merely to satisfy manifest tests, and requires additive manifest tests. It does not propose disabling or weakening current test coverage.

### Test Gaps

- None requiring revision. The plan now includes validation-mode mismatch tests, terminal-state positive/negative tests, source-family provenance positive/negative tests, canonical ID policy tests, discovery-mode tests, and regression coverage through the release gate.

### Real-World Testing

Real-world runtime testing is addressed appropriately for Phase 1. The new manifest is intentionally not consumed by runtime loading yet, so direct contract tests plus the existing release gate and E2E command are sufficient integration evidence; live full-corpus discovery/import gates belong to later phases.

## Reference Consistency

### Findings

- All referenced plan, docs, and code-anchor files exist in the current repository.
- The implementation plan accurately describes current code reality: `SourceKind` is limited to `gesetze-im-internet` and `eur-lex-cellar`, `NormUnit` is limited to `par` and `art`, the raw snapshot manifest in `importer.py` is over static `SOURCE_SPECS`, and `validate_dataset_package` does not validate corpus manifests or generated-package metadata.

## Reality Check Validation

### Findings

- The Reality Check is complete for the implementation decisions in this phase. It covers the current models, validation path, dataset loading boundary, raw snapshot manifest shape, static source specs, registry alias semantics, existing canonical IDs/aliases, and fixture dataset tests.
- The r2 additions correctly incorporate the previous missing registry-data anchor and the validation-mode/provenance mismatches discovered in earlier review.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Note | Test execution | The primary verify command currently runs the repository release gate as-is; depending on environment, `scripts/verify_release.py` may include the existing live source matrix unless `SKIP_LIVE_SOURCE_MATRIX=true` is set. This is an existing repo behavior, not a Phase 1 blocker. | Keep Phase 1 manifest tests fixture-backed. Use the established skip flag where CI needs a fully offline fast gate. |
| 2 | Note | Source limitations | The plan treats source limitations primarily through terminal-state and provenance records, while `source_limitations` is listed as an optional top-level manifest section. This is acceptable for Phase 1, but later phases should avoid inventing a second incompatible limitation schema. | When implementing, either keep limitation evidence in discovered-source terminal records or give optional `source_limitations` the same provenance/terminal-state vocabulary. |

## Recommendations

1. Proceed with implementation.
2. Preserve the stated runtime boundary: add and test `mcp/legal_texts/manifest.py` directly, but do not require existing normalized fixtures or runtime startup to consume a corpus manifest in Phase 1.
