---
type: review
entity: implementation-plan-review
plan: "full-privacy-corpus"
phase: 4
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 4 - GII bulk normalization and coverage gates

> Reviewing [Phase 4 Implementation Plan](../implementation/phase-4-impl.md)
> Against [Phase 4 Scope](../phases/phase-4.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Ready

The r2 revisions are sufficient for execution. The implementation plan now covers Phase 4's bulk GII normalization scope, generated-registry path, parser-variant matrix, terminal-state manifest validation, full-discovery gate evidence, and BDSG/TDDDG critical-law exception handling without requiring implementers to infer the risky integration details.

## Scope Alignment

### Findings

- The plan remains aligned with Phase 4: it covers discovered GII source normalization, representative parser structures, source failure states, fixture coverage, full-discovery terminal-state gates, and critical named GII law checks.
- It avoids deferred scope from later phases, including DSGVO recitals, EU neighbor acts, state-law adapters, relationship graph metadata, and runtime performance tuning beyond correctness gates.
- The parser-variant matrix deliverable is explicitly represented as either `docs/features/gii-parser-variant-matrix.md` or `mcp/tests/fixtures/gii/parser-variant-matrix.json`, with concrete expected output fields.

## Technical Feasibility

### Findings

- The plan correctly identifies the current static-registry limitation in `mcp/legal_texts/normalizer.py::normalize_snapshot` and requires a generated GII registry or generated law-record map before bulk normalization.
- The generated-registry direction fits the existing `mcp/legal_texts/registry.py` collision model while adding the missing Phase 4 source-path and alias-migration checks before parsing.
- Terminal states are anchored to the Phase 1 manifest contract through `validate_corpus_manifest(..., require_terminal_states=True)`, which avoids a separate ad hoc coverage format.
- Parser expansion is feasible and appropriately bounded by fixture-backed variants. Current `mcp/legal_texts/gii_xml.py::parse_gii_zip` supports only paragraph and article-child patterns, and the plan now states expected `unit`, `norm_id`, `status`, URL suffix, `children`, and text/null behavior for added structural classes.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Add bulk GII normalization orchestration | Yes | Yes | No issue. Generated registry construction, terminal-state persistence, and manifest validation are explicit. |
| 2 | Extend GII parser variant coverage | Yes | Yes | No issue. The variant matrix defines expected normalized output behavior for the new structures. |
| 3 | Generate stable canonical IDs and provenance | Yes | Yes | No issue. Alias preservation, migration entries, collision failure, and generated-package validation are specified. |
| 4 | Add terminal-state and critical-law gates | Yes | Yes | No issue. The CLI contract, output evidence, opt-in full-discovery command, and critical-law exception rule are concrete. |

## Required Context Assessment

### Missing Context

- None material. The plan lists the current code anchors and the Phase 1-3 prerequisite artifacts needed for execution.

### Unnecessary Context

- None material.

## Testing Plan Assessment

### Test Integrity Check

The testing plan is adequate. It has one primary fast verify command, includes the earlier-phase manifest and generated-package validation tests that Phase 4 depends on, preserves existing GII normalizer and registry behavior, and explicitly prohibits weakening parse failures into policy exclusions.

### Test Gaps

- None identified.

### Real-World Testing

Real-world testing is explicitly planned through the opt-in full-discovery command:

`PYTHONPATH=mcp uv run --group dev python scripts/verify_gii_corpus_gate.py --discovery-artifact .artifacts/gii-discovery/latest.json --package-dir .artifacts/gii-corpus/package --output .artifacts/gii-corpus/gate.json`

The plan correctly keeps this separate from the fast fixture-backed pytest command while requiring persisted evidence for full-discovery terminal-state coverage.

## Reality Check Validation

### Findings

- The Reality Check accurately describes current code: `normalize_snapshot` resolves through the static `LawRegistry`, `import_snapshot` is tied to `SOURCE_SPECS` and raises on source failures, and `parse_gii_zip` currently handles only the basic paragraph/article patterns.
- It correctly marks `mcp/legal_texts/manifest.py`, `mcp/legal_texts/gii_toc.py`, and generated-package validation as Phase 1-3 prerequisite outputs rather than current baseline files before those phases execute.
- The r2 revision closes the prior critical-law ambiguity by stating that reachable `parse_failed` and `unsupported_format` outcomes fail the BDSG/TDDDG critical-law gate.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| - | - | - | No findings. | Proceed to implementation when Phase 1-3 prerequisites are complete. |

## Recommendations

1. Proceed with Phase 4 implementation after Phase 3 discovery artifacts and Phase 1-2 validation/package contracts are available.
