---
type: review
entity: implementation-review
plan: "full-privacy-corpus"
phase: 12
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Review: Phase 12 - Scaling, search, and operational corpus gates R2

> Reviewing implementation of [Phase 12](../phases/phase-12.md)
> Against [Implementation Plan](../implementation/phase-12-impl.md), [Plan](../plan.md), and prior review [impl-review-phase-12.md](impl-review-phase-12.md)

## Overall Assessment

**Verdict**: Needs Rework

The rework resolves the broad placeholder-bundle problem: section-specific validators now reject empty DSGVO, EU-neighbor, state-law, relationship, GII, and benchmark artifacts, and benchmark threshold misses are represented as `passed_with_migration_decisions` with exit 0 when no validation/load error occurs. However, Phase 12 still should not be accepted because the critical-law evidence gate can pass cross-wired imported evidence for the wrong critical law, the release-blocking limitation fallback remains under-specified, and the default release gate still includes live network tests unless explicitly skipped.

**Finding count**: Critical 1, Major 2, Minor 0, Note 0.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | PR CI does not require full corpus download/import. | Partial | `scripts/verify_release.py` does not call `benchmark_corpus_runtime.py` or `verify_full_corpus_bundle.py`; `mcp/tests/test_operational_corpus_gates.py` asserts those scripts are absent from the release gate. | The default release gate still includes `mcp/tests/test_source_matrix_live.py` and only skips it with `SKIP_LIVE_SOURCE_MATRIX=true`, so live network remains opt-out rather than explicit opt-in. |
| 2 | Full-corpus smoke checks can run explicitly or on schedule. | Yes | `scripts/verify_full_corpus_bundle.py` composes explicit artifacts; `scripts/benchmark_corpus_runtime.py` is an explicit benchmark command. | No scheduled workflow was reviewed, but explicit operation is in place and acceptable for this phase. |
| 3 | Full-corpus import gate persists manifest artifacts with terminal-state coverage for all discovered GII sources. | Yes | `validate_gii_artifact()` requires positive discovered count, terminal-state coverage, imported count consistency, generated package path/hash, and critical-law outcomes. | No blocking gap found in the reworked coverage checks. |
| 4 | Validation bundle persists DSGVO counts, selected expression/document, version/consolidation policy, and content hash. | Yes | `validate_dsgvo_artifact()` requires policy and selected-source CELEX, Cellar work, expression, document, language, version policy, consolidation policy, content hash, expected/actual counts, and boundary samples. | None found. |
| 5 | Validation bundle persists BDSG and TDDDG successful import and MCP/HTTP resolution evidence from GII provenance, or a release-blocking upstream source limitation. | No | `critical_law_evidence()` now loads `gii.generated_package.path` and derives runtime, MCP, and HTTP evidence. | The imported path can still resolve an arbitrary first `generated_norm_ids` entry, even if it belongs to another critical law, and the fallback limitation can pass without required upstream evidence fields. |
| 6 | Validation bundle persists EU neighbor imported-or-limited states. | Yes | `validate_eu_neighbors_artifact()` requires seeded CELEX coverage, AI Act/Data Act CELEXs, per-CELEX `source_results`, imported evidence, or limitation evidence. | None found. |
| 7 | Validation bundle persists all 16 state-law imported-or-limited outcomes. | Partial | `validate_state_law_artifact()` requires `total_states == 16`, imported + limited == 16, a coverage artifact, and per-entry imported-or-limited evidence. | It does not require the fixed German state-code set or uniqueness; the success fixture uses fictional `S01`-`S16` state codes, so a fake 16-row artifact can pass. |
| 8 | Validation bundle persists relationship graph discovered-or-limited records and validation status. | Yes | `validate_relationships_artifact()` requires nonempty relationships or limitations and calls `validate_privacy_scope_seed()`. | None found. |
| 9 | Runtime load budget is 120 seconds or less, or a migration decision is recorded. | Yes | `benchmark_corpus_runtime.py` defaults to 120000 ms and emits `passed_with_migration_decisions` with `review_dataset_loading_strategy` when the load threshold is missed. | None found. |
| 10 | Search p95 is under 1 second, or a search-index migration decision is recorded. | Yes | Benchmark default is 1000 ms and `test_bundle_accepts_threshold_misses_with_complete_migration_decisions()` verifies the accepted migration-decision path. | None found. |
| 11 | Runtime memory budget is 2 GB or less, or a package-format migration decision is recorded. | Yes | Benchmark default is 2048 MB and output includes dataset, search, and combined memory fields. | None found. |
| 12 | Generated production data remains excluded from Git. | Yes | `.gitignore` excludes `.artifacts/`, `data/sources/raw/`, `data/normalized/`, `data/generated/`, `data/full-corpus/`, `data/corpus-bundles/`, and `data/benchmarks/` while preserving fixture directories. | None found. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Add benchmark fixture/generator helpers with runtime/search/memory evidence and threshold decisions. | Implemented in `scripts/benchmark_corpus_runtime.py` and `mcp/tests/test_search_scaling.py`. | No | Prior threshold/default and memory-accounting findings are resolved. |
| 2 | Add opt-in full-corpus gate scripts with required evidence sections. | Implemented in `scripts/verify_full_corpus_bundle.py` with section-specific validators. | Yes | Much improved, but critical-law and state-law validation still accept invalid evidence shapes. |
| 3 | Validate dataset exclusion and artifact handling. | `.gitignore` and operational hygiene tests cover generated data exclusions. | No | Meets the generated-data exclusion objective. |
| 4 | Add package-format/search migration decision records. | Benchmark emits migration decisions and bundle accepts complete decisions. | No | Prior threshold decision finding is resolved. |

## Code Quality Assessment

### Findings

- The validators are clearer and more maintainable than the initial wrapper-only implementation, and negative tests now exercise missing section evidence.
- The critical-law validator is still not strict enough for a release gate: `_validate_imported_critical_law()` checks that `generated_law_ids` and `generated_norm_ids` are nonempty, but it does not verify that they contain the required canonical law or that the resolved norm's law/source provenance matches the critical-law outcome.
- The release gate still relies on an opt-out environment variable for live network tests, which is the wrong default for Phase 12's fast fixture-backed gate.

## Testing Assessment

### Verify Command Result

- **Command**: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_operational_corpus_gates.py mcp/tests/test_search_scaling.py mcp/tests/test_runtime_coverage_relationships.py mcp/tests/test_dsgvo_full_counts.py`
- **Exit Code**: 0
- **Result**: 29 passed

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: 231 passed plus legacy/generated-package HTTP and MCP E2E checks passed

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `mcp/tests/test_operational_corpus_gates.py` | Bundle success, missing artifacts, placeholder rejection, weak critical-law fields, weak limitation terminal state, benchmark migration decisions, release-gate hygiene. | Partial | It does not test cross-wired critical-law evidence, under-specified `source_unavailable` fallback evidence, or default live-network exclusion. |
| `mcp/tests/test_search_scaling.py` | Larger fixture loading/search and benchmark memory fields. | Yes | Fixture scale is small but appropriate for fast PR coverage. |
| `mcp/tests/test_dsgvo_full_counts.py` | DSGVO policy/source/count/hash/boundary artifact generation and negative cases. | Yes | None found. |
| State-law bundle fixture in `test_operational_corpus_gates.py` | 16 state rows and imported/limited counts. | Partial | The passing fixture uses fictional `S01`-`S16` state codes, so it does not prove the bundle enforces the actual German state set. |

### Real-World Testing

Live network/full import testing was not performed by this reviewer, and Phase 12 should not require it in the default PR/release path. Local fixture-backed runtime, benchmark, bundle, and release verification were performed as listed above.

## Scope Compliance

### Findings

- No full-corpus download/import was added to the default release script.
- The rework stayed within operational scripts, tests, and generated-data ignore rules.

## Regression Risk

### Test Integrity Check

- [x] No reviewed Phase 12 tests were deleted.
- [x] No reviewed Phase 12 tests were disabled.
- [x] No reviewed Phase 12 assertions were weakened.
- [x] The targeted and release-gate test commands above pass locally.

### Findings

- The remaining risk is false-positive operational evidence: the bundle can still certify some malformed artifacts as ready, which weakens release confidence rather than breaking runtime behavior directly.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Critical | Critical-law evidence | `scripts/verify_full_corpus_bundle.py` can pass invalid critical-law evidence. `_validate_imported_critical_law()` only checks nonempty `generated_law_ids`/`generated_norm_ids` and resolves the first norm ID (`lines 247-273`), so a `bdsg_2018` outcome can point at `tdddg/par:25` and still pass runtime, MCP, and HTTP resolution. `_validate_limited_critical_law()` (`lines 306-328`) also accepts a bare `source_unavailable` limitation with official-looking GII URL and `release_blocking: true`, without `limitation_id`, retrieval/decision timestamp, HTTP/status detail, or explicit official upstream evidence. I confirmed both cases return bundle exit code 0 in a temporary negative check. | Bind critical-law evidence to the required canonical law: require `generated_law_ids` to include the canonical ID, every validated norm ID to start with `<canonical>/`, the generated package law/norm source metadata to match the outcome `source_id`/`source_path`/GII URL, and all three resolution channels to resolve that canonical law. For fallback limitations, enforce the failure-taxonomy fields and official upstream evidence, not just `release_blocking`. Add negative tests for cross-wired BDSG/TDDDG evidence and under-specified source-unavailable limitations. |
| 2 | Major | Release gate | `scripts/verify_release.py` includes `mcp/tests/test_source_matrix_live.py` in `TESTS` by default (`lines 11-16`) and only removes it when `SKIP_LIVE_SOURCE_MATRIX=true` (`lines 46-51`). That makes live network opt-out, while Phase 12 review focus requires no live network in the default PR/release gate and allows explicit opt-in instead. | Invert the gate: exclude live source probes by default and include them only with an explicit opt-in variable or separate command/workflow. Add a test that `selected_tests()` omits `test_source_matrix_live.py` by default and includes it only when opted in. |
| 3 | Major | State-law evidence | `validate_state_law_artifact()` checks count/length and per-row imported-or-limited fields (`lines 388-426`), but not the fixed German state-code set or uniqueness. The passing operational fixture uses fictional `S01`-`S16` state codes (`mcp/tests/test_operational_corpus_gates.py` lines 215-239), so the bundle can pass a fake 16-row state artifact instead of proving all 16 German state-law outcomes. | Validate against `FIXED_STATE_CODES` or reuse `validate_state_law_coverage()` with the inventory/package context. Require unique expected state codes and add negative tests for duplicate, unknown, and missing state codes in the bundle validator. |

## Recommendations

1. Block Phase 12 acceptance until the critical-law validator rejects cross-wired imported evidence and weak `source_unavailable` fallback evidence.
2. Make live source probes explicit opt-in for the default release gate.
3. Tighten state-law bundle validation to prove the actual 16 German states, not just any 16 rows.
