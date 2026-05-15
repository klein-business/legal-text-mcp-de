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

The revised implementation plan is now concrete enough to execute. It aligns with the Phase 4 scope, addresses the static-registry and terminal-manifest integration risks identified in the first review, defines parser-variant evidence, and separates fast fixture verification from the opt-in full-discovery gate required for real corpus coverage.

## Scope Alignment

### Findings

- Scope is aligned with Phase 4: GII bulk normalization, representative parser variants, source failure states, generated fixture coverage, full-discovery terminal-state gates, and BDSG/TDDDG critical-law checks are all covered.
- The plan avoids deferred areas such as DSGVO recitals, EUR-Lex neighbor acts, state-law adapters, relationship graph metadata, and runtime performance tuning.
- The parser-variant matrix deliverable is now represented as either `docs/features/gii-parser-variant-matrix.md` or `mcp/tests/fixtures/gii/parser-variant-matrix.json`, with expected normalized output fields.

## Technical Feasibility

### Findings

- The plan correctly identifies that current `mcp/legal_texts/normalizer.py::normalize_snapshot` resolves entries through the static `LawRegistry`, and it now specifies a generated GII registry or generated law-record map before bulk normalization.
- The generated-registry direction is feasible against current `mcp/legal_texts/registry.py` semantics because duplicate law IDs and alias collisions are already validation concepts, while Phase 4 can add source-path collision checks before parsing.
- The terminal-state artifact is now tied to the Phase 1 manifest contract through `validate_corpus_manifest(..., require_terminal_states=True)`, avoiding an incompatible ad hoc coverage format.
- Parser expansion is feasible but non-trivial: current `mcp/legal_texts/gii_xml.py::parse_gii_zip` only emits `par` and `art`/article-child records, so the matrix-driven fixture approach is the right guardrail for adding `annex`, `section`, `container`, and repealed/title-only cases.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Add bulk GII normalization orchestration | Yes | Yes | No blocking issue. The generated registry and terminal-state artifact requirements make the current static-registry mismatch explicit. |
| 2 | Extend GII parser variant coverage | Yes | Yes | No blocking issue. Expected units, IDs, statuses, URLs, children, and text/null behavior are now required in a fixture-backed matrix. |
| 3 | Generate stable canonical IDs and provenance | Yes | Yes | No blocking issue. Alias/migration and generated-package linkage are explicit. |
| 4 | Add terminal-state and critical-law gates | Yes | Yes | Minor clarification recommended for which critical-law limitation states can satisfy the release-blocking exception. |

## Required Context Assessment

### Missing Context

- None material. The plan lists the relevant current code anchors and earlier-phase prerequisite artifacts.

### Unnecessary Context

- None material.

## Testing Plan Assessment

### Test Integrity Check

The testing plan is adequate for this phase. It includes one primary fast verify command, preserves existing GII normalizer, registry, resolver, corpus-manifest, and generated-package contracts, and states that parse failures must not be reclassified as policy exclusions. The opt-in gate command separately covers network-heavy/full-discovery evidence without making ordinary fixture verification depend on live network access.

### Test Gaps

- **Minor**: The BDSG/TDDDG gate should explicitly reject parser failures or unsupported-format outcomes as satisfying the critical-law exception unless the artifact separately classifies them as release-blocking upstream source limitations. The plan says "imported-and-resolvable evidence or release-blocking upstream limitations", but making the accepted terminal states explicit in the script tests would prevent an implementation from treating ordinary parser gaps as acceptable critical-law evidence.

### Real-World Testing

Real-world testing is explicitly planned through `scripts/verify_gii_corpus_gate.py --discovery-artifact <path> --package-dir <path> --output <path>`. The plan correctly keeps this as an opt-in explicit or scheduled gate while using committed fixtures for the primary development/CI command.

## Reality Check Validation

### Findings

- The Reality Check is honest about current code: `normalize_snapshot` is static-registry based, `import_snapshot` is tied to `SOURCE_SPECS`, and `parse_gii_zip` supports only the existing paragraph/article patterns.
- The plan also correctly marks `mcp/legal_texts/manifest.py`, `mcp/legal_texts/gii_toc.py`, and generated-package validation as prerequisite outputs from Phases 1-3 rather than current baseline files before those phases execute.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Minor | Testing | Critical-law limitation tests do not explicitly constrain which non-imported terminal states may satisfy the BDSG/TDDDG release-blocking exception. | Add fixture cases proving reachable parser failures or unsupported formats fail the critical-law gate unless classified as release-blocking upstream source limitations under the manifest/package contract. |

## Recommendations

1. Add the critical-law negative fixture cases above when implementing `scripts/verify_gii_corpus_gate.py`.
