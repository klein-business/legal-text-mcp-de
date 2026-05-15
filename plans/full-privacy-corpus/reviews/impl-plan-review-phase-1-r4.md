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

The Phase 1 implementation plan is executable without guessing and stays within the gated scope. It now gives concrete schema, validation-mode, terminal-state, source-family provenance, canonical-ID, fixture, and test requirements, while preserving the current runtime boundary by not wiring the manifest into `NormalizedDataset` or existing normalized fixtures in this phase.

## Scope Alignment

### Findings

No findings.

The implementation plan covers the Phase 1 deliverables: manifest schema and validation rules, source-family identifiers, terminal-state requirements, provenance matrix, deterministic canonical ID and alias policy, representative fixtures, validation tests, release-gate integration, and a source-provenance documentation note. It does not include deferred work such as full GII discovery, DSGVO import expansion, state-law adapters, runtime coverage APIs, or relationship lookup surfaces.

## Technical Feasibility

### Findings

No findings.

The proposed additive `mcp/legal_texts/manifest.py` boundary matches the current codebase. Existing validation in `mcp/legal_texts/validation.py` is normalized-record focused, `mcp/legal_texts/dataset.py` loads only normalized package files, `mcp/legal_texts/importer.py` writes a raw snapshot manifest over static `SOURCE_SPECS`, and `mcp/legal_texts/models.py` still limits serving `SourceKind` and `NormUnit` to the current runtime contract. Keeping the broader corpus manifest vocabulary separate until later package/runtime phases is technically sound.

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

None.

### Unnecessary Context

None.

The required context list includes the governing plan and phase scope, source-provenance and loading docs, the current model, validation, dataset, importer, source, and registry modules, existing registry data, current dataset and registry tests, and the release gate that must include the new contract tests.

## Testing Plan Assessment

### Test Integrity Check

The testing plan protects existing coverage: `mcp/tests/test_dataset_validation.py` must remain semantically unchanged except for additive assertions, existing normalized fixtures must not be edited merely to satisfy manifest tests, and new negative cases must use explicit invalid manifest fixtures. It also requires adding the new manifest tests to `scripts/verify_release.py`.

### Test Gaps

No findings.

The plan includes positive and negative tests for terminal states, source-family provenance, validation-mode conflicts, duplicate discovered sources, manifest envelope/package metadata, canonical ID collisions, CELEX and state-law policy failures, relationship-source law-ID rejection, source limitations, discovery-mode behavior, and existing normalized dataset regression coverage.

### Real-World Testing

Real-world testing is addressed at the right level for Phase 1. This phase defines a fixture-backed manifest contract and intentionally does not change runtime serving behavior, so direct contract tests plus the repository release gate are sufficient. Network-heavy full-corpus discovery and terminal-coverage evidence remain deferred to later phases that actually perform discovery/import work.

## Reference Consistency

### Findings

No findings.

All referenced plan, phase, docs, test, data, and code-anchor paths exist in the current repository. The implementation plan accurately describes the current anchors: serving records know only `gesetze-im-internet` and `eur-lex-cellar`, normalized validation does not know about corpus manifests, runtime package loading does not consume a corpus manifest, the importer manifest is a raw snapshot list, `SOURCE_SPECS` is fixture-sized and static, and `LawRegistry.validate` only covers current alias collisions.

## Reality Check Validation

### Findings

No findings.

The Reality Check is honest and complete for Phase 1. It records the material mismatches between the desired generated-corpus contract and the current fixture-backed runtime, and the implementation steps reflect those mismatches by adding an isolated manifest contract and tests rather than prematurely changing runtime package semantics.

## Findings Summary

| Severity | Count |
| -------- | ----- |
| Critical | 0 |
| Major | 0 |
| Minor | 0 |
| Note | 0 |

No Critical, Major, Minor, or Note findings were identified.

## Recommendations

1. Proceed with Phase 1 implementation as planned.
