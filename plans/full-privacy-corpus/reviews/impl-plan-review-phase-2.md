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

The plan is directionally aligned with Phase 2, but it is not yet concrete enough for reliable execution. It leaves the generated package schemas underspecified, does not resolve how strict validation is wired into runtime readiness, assumes Phase 1 symbols that are not present in the current codebase, and the verify command does not satisfy the phase's MCP/HTTP E2E acceptance criterion.

## Scope Alignment

### Findings

- Phase 2 requires documented generated package, citation-unit, and relationship package schemas, plus runtime readiness semantics for generated packages (`phase-2.md:50-55`). The implementation plan names `package.json`, `source-limitations.json`, and `relationships.json`, but does not define required fields, versioning, count fields, source-limitation record shape, relationship type enum, or readiness-state behavior.
- The plan stays within Phase 2 by deferring relationship lookup APIs and bulk data import, which matches the phase exclusions.

## Technical Feasibility

### Findings

- Current `NormalizedDataset` only calls `validate_dataset_package`, reads `laws.json` and `norms.json`, and builds indexes (`mcp/legal_texts/dataset.py:17-31`). The proposed separate strict generated-package helper (`phase-2-impl.md:101`) is feasible for tests, but the plan does not say how generated packages are identified or when the loader invokes strict validation, so a generated package with inconsistent manifest/package metadata could still load through the normal runtime path.
- Current package validation only checks `laws.json`, `norms.json`, and serving `search-index.json` (`mcp/legal_texts/validation.py:21-38`); it does not require or parse `readiness.json`. The implementation plan's Reality Check says startup expects readiness (`phase-2-impl.md:113`), which is inaccurate and hides a real integration gap for Phase 2 readiness semantics.
- Expanding `NormUnit` while preserving resolver behavior is technically possible, but the plan needs a more precise split between "record schema accepts these units" and "resolver intentionally rejects or does not parse these units until later." Current `normalize_unit` maps `"section"` to `"par"` (`mcp/legal_texts/models.py:120-126`), which conflicts with adding `section` as its own citation unit unless the plan explicitly changes validation to avoid using `normalize_unit` for generated-record units.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Define generated package metadata and optional files | No | Partial | Names files but does not define schemas, required/optional status in strict mode, versioning, counts, source-failure/source-limitation fields, or docs update location. |
| 2 | Add additive citation-unit validation | Partial | Partial | Names the unit set, but does not address `normalize_unit("section") -> "par"` or define allowed value patterns for recital/chapter/section/annex/container. |
| 3 | Validate manifest and normalized-record consistency | Partial | Partial | Depends on `mcp/legal_texts/manifest.py::validate_corpus_manifest`, which does not exist in the current repo before Phase 1 is implemented; also does not specify loader integration. |
| 4 | Add relationship record schema validation | No | Partial | Does not define supported relationship types, relationship ID format, provenance fields, or target record encoding, so implementers must invent the contract. |
| 5 | Preserve runtime and transport behavior | Yes | Yes | Regression target is clear, but it does not cover generated-package readiness behavior or real MCP/HTTP E2E. |

## Required Context Assessment

### Missing Context

- `mcp/legal_texts/runtime.py` - needed because Phase 2 includes runtime readiness semantics and current readiness responses are synthesized from loaded dataset state.
- `mcp/legal_texts/normalizer.py` - needed to understand existing `readiness.json` production and avoid designing a package contract that validation/loading ignores.
- `scripts/verify_e2e.py` or `scripts/verify_release.py` - needed because Phase 2 acceptance explicitly requires MCP and HTTP E2E checks, while the test plan only lists in-process pytest modules.
- `mcp/legal_texts/manifest.py` - should be listed as a prerequisite artifact after Phase 1 exists; in the current codebase it is absent, so Phase 2 execution must begin by verifying the prerequisite landed.

### Unnecessary Context

- None material.

## Testing Plan Assessment

### Test Integrity Check

The plan identifies existing tests that must remain authoritative and explicitly says not to weaken `validate_norms` source requirements. It does not say that no existing tests will be disabled or weakened generally, and it does not distinguish tests that should be updated for intentional generated-package behavior from tests that must remain untouched.

### Test Gaps

- The primary verify command does not include real MCP/HTTP E2E checks, despite the phase acceptance criterion requiring existing MCP and HTTP E2E checks against the fixture package.
- No test is named for generated-package runtime readiness semantics: missing or invalid `package.json`, `manifest.json`, `source-limitations.json`, or `relationships.json` in strict mode; generated-package readiness details; and backwards-compatible loading of legacy fixture packages.
- Relationship validation tests are described generically, but without a declared schema they cannot be implemented consistently across later phases.
- Citation-unit tests do not explicitly cover the `section` ambiguity caused by current resolver normalization, container unit/value rules, or negative cases for records whose `unit` and `norm_id` disagree.

### Real-World Testing

Real-world / integration testing is not adequately planned. `mcp/tests/test_http_api.py` and `mcp/tests/test_mcp_tools.py` are useful regression tests, but they are in-process tests; the plan should include the existing local network E2E gate or explain why it is intentionally waived for this phase.

## Reference Consistency

### Findings

- `mcp/legal_texts/manifest.py` and `validate_corpus_manifest` are referenced as Phase 1 outputs (`phase-2-impl.md:59`), but they are not present in the current repository. This is acceptable only if Phase 2 is explicitly gated on re-checking the completed Phase 1 implementation before execution.
- The Reality Check statement that `NormalizedDataset.__init__` expects `laws/norms/readiness/search-index` is wrong. Current code validates `laws.json`, `norms.json`, and optionally `search-index.json`, then reads only laws and norms (`mcp/legal_texts/dataset.py:17-24`).

## Reality Check Validation

### Findings

- The Reality Check misses the most important readiness mismatch: current docs mention `readiness.json`, but current validation/loading does not require or consume it (`mcp/legal_texts/validation.py:21-38`, `mcp/legal_texts/dataset.py:17-24`). Because Phase 2 includes runtime readiness semantics, the plan should call this out as a design decision rather than implying existing startup already uses readiness.
- The Reality Check correctly identifies current `NormUnit` and resolver limitations, but it does not note that `normalize_unit` currently treats `"section"` as a synonym for `par`, which conflicts with the planned first-class `section` unit.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Step Quality | Generated package, source-limitation, and relationship schemas are not concrete enough to execute without inventing fields and enums. | Add explicit schemas or schema tables for `package.json`, `manifest.json` integration, `source-limitations.json`, and `relationships.json`, including version, counts, IDs, relationship types, provenance, and target encoding. |
| 2 | Major | Technical Feasibility | Strict generated-package validation is not wired to runtime loading/readiness, so manifest/package inconsistencies may not be caught when serving a generated package. | Define the generated-package detection and loader path, including when `NormalizedDataset` or `LegalTextRuntime` invokes strict validation and how readiness details are reported. |
| 3 | Major | Reality Check | The plan inaccurately says startup expects `readiness.json`; current code ignores it, and Phase 2 readiness semantics are therefore underspecified. | Correct the Reality Check and add an implementation step for validating or intentionally not consuming `readiness.json` in generated packages. |
| 4 | Major | Testing | The primary verify command lacks the existing local MCP/HTTP E2E gate required by Phase 2 acceptance. | Include `scripts/verify_e2e.py`, `scripts/verify_release.py`, or a targeted equivalent, and specify the generated fixture package used by that gate. |
| 5 | Minor | Technical Feasibility | `section` is currently normalized to `par`, which conflicts with adding `section` as a first-class generated-record unit. | Specify separate generated-record unit validation or update normalization deliberately with regression tests for existing `§`/`par` behavior. |
| 6 | Minor | Required Context | Runtime, normalizer, and E2E scripts are missing from Required Context. | Add `mcp/legal_texts/runtime.py`, `mcp/legal_texts/normalizer.py`, and the relevant E2E/release verification script to Required Context. |

## Recommendations

1. Revise Steps 1 and 4 to include explicit package/source-limitation/relationship schemas and supported enum values.
2. Add a concrete loader/readiness integration decision for strict generated-package validation, including backwards-compatible behavior for the current fixture package.
3. Correct the Reality Check around `readiness.json` and call out the current `section` normalization conflict.
4. Strengthen the testing plan with real local MCP/HTTP E2E verification and generated-package strict-mode readiness tests.
