---
type: review
entity: implementation-review
plan: "full-privacy-corpus"
phase: 12
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Review: Phase 12 - Scaling, search, and operational corpus gates

> Reviewing implementation of [Phase 12](../phases/phase-12.md)
> Against [Implementation Plan](../implementation/phase-12-impl.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Rework

The implementation keeps ordinary release verification fixture-backed and adds useful benchmark/bundle scaffolding, but the full-corpus validation bundle does not yet enforce the Phase 12 evidence contract. It can pass with placeholder `status: ready` artifacts for DSGVO, EU neighbors, state laws, and relationships, and the critical-law and threshold handling do not prove the required release evidence. These gaps directly affect multiple Phase 12 acceptance criteria, so the phase should not be accepted as complete.

**Finding count**: Critical 1, Major 3, Minor 0, Note 0.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | PR CI does not require full corpus download/import. | Yes | `scripts/verify_release.py` includes fixture-backed tests and does not call `benchmark_corpus_runtime.py` or `verify_full_corpus_bundle.py`; `mcp/tests/test_operational_corpus_gates.py` asserts this. | None found. |
| 2 | Full-corpus smoke checks can run explicitly or on schedule. | Partial | `scripts/benchmark_corpus_runtime.py` and `scripts/verify_full_corpus_bundle.py` are explicit commands, and prior phase scripts produce input artifacts. | No scheduled workflow was added; explicit operation exists, but the bundle gate currently accepts incomplete evidence. |
| 3 | Full-corpus import gate persists manifest artifacts with terminal-state coverage for all discovered GII sources. | Partial | GII gate artifacts include `terminal_state_coverage` and `critical_law_outcomes`; the bundle records the GII artifact path and hash. | The Phase 12 bundle does not validate discovered-source counts or terminal-state coverage. |
| 4 | Validation bundle persists DSGVO counts, selected expression/document, version/consolidation policy, and content hash. | No | `verify_full_corpus_bundle.py` only summarizes generic `counts`; `verify_dsgvo_full_counts.py` does not emit the validated `content_hash` in the artifact. | The bundle can pass without DSGVO counts, policy fields, selected document/expression, or content hash. |
| 5 | Validation bundle persists BDSG and TDDDG successful import and MCP/HTTP resolution evidence from GII provenance, or a release-blocking upstream limitation. | Partial | `critical_law_evidence()` requires GII `critical_law_outcomes` and accepts `tdddg` or legacy `ttdsg`. | It does not require MCP/HTTP resolution evidence, generated norms, strict GII source provenance, or source-unavailable upstream evidence for release-blocking limitations. |
| 6 | Validation bundle persists EU neighbor imported-or-limited states. | No | The bundle stores the EU neighbor artifact path, hash, schema, and summarized counts if present. | It does not validate `source_results`, required CELEX outcomes, or imported-or-limited terminal states. |
| 7 | Validation bundle persists all 16 state-law imported-or-limited outcomes. | No | The bundle stores the state-law artifact path, hash, schema, and summarized counts if present. | It does not require `total_states == 16` or validate per-state imported/limited outcomes. |
| 8 | Validation bundle persists relationship graph discovered-or-limited records and validation status. | No | The bundle stores the relationship artifact path and hash. | It does not validate relationship records, source limitations, validation status, or discovered-or-limited coverage. |
| 9 | Runtime load budget is 120 seconds or less, or a migration decision is recorded. | Partial | `benchmark_corpus_runtime.py` records `load_time_ms` and migration decisions. | Defaults are stricter than the phase budget, and threshold misses make the benchmark and bundle fail even when a migration decision is recorded. |
| 10 | Search p95 is under 1 second, or a search-index migration decision is recorded. | Partial | Benchmark output records sampled search timings and p95. | Same threshold/decision issue as above; default search threshold is 100 ms rather than the phase's 1 second. |
| 11 | Runtime memory budget is 2 GB or less, or a package-format migration decision is recorded. | Partial | Benchmark output records estimated memory and migration decisions. | Default memory threshold is 512 MB, and memory estimation excludes the `SearchService` rows built for runtime search. |
| 12 | Generated production data remains excluded from Git. | Yes | `.gitignore` excludes `.artifacts/`, `data/sources/raw/`, `data/normalized/`, `data/generated/`, `data/full-corpus/`, `data/corpus-bundles/`, and `data/benchmarks/` while preserving fixture directories. | None found. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Add benchmark fixture/generator helpers with runtime/search/memory evidence and threshold decisions. | Added `scripts/benchmark_corpus_runtime.py` and `mcp/tests/test_search_scaling.py`. | Yes | Useful scaffolding, but defaults do not match Phase 12 budgets and memory excludes search rows. |
| 2 | Add opt-in full-corpus gate scripts with required evidence sections. | Added `scripts/verify_full_corpus_bundle.py`. | Yes | The script composes artifact wrappers but does not validate most required evidence fields. |
| 3 | Validate dataset exclusion and artifact handling. | Added `.gitignore` rules and hygiene tests. | No | Meets the exclusion objective. |
| 4 | Add package-format/search migration decision records. | Benchmark emits `migration_decisions`. | Yes | Decisions are generated, but threshold misses still fail the benchmark/bundle, so the "or decision recorded" acceptance path is not usable. |

## Code Quality Assessment

### Findings

- `scripts/verify_full_corpus_bundle.py` centralizes artifact wrapping cleanly, but its validation boundary is too shallow for a release gate: `load_artifact()` treats any JSON artifact without `validation_errors` as ready, and `build_bundle()` only rejects runtime readiness and critical-law status.
- `scripts/benchmark_corpus_runtime.py` is deterministic and dependency-light, but its measured memory does not cover all objects created for serving/search and its defaults conflict with the phase thresholds.
- `.gitignore` and release-gate hygiene are scoped and consistent with the phase.

## Testing Assessment

### Verify Command Result

- **Command**: Not re-run by reviewer; the user supplied implementer verification output.
- **Exit Code**: Not applicable.
- **Result**: Review was based on source inspection and the supplied digest to avoid creating additional test artifacts during an implementation review.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `mcp/tests/test_operational_corpus_gates.py` | Benchmark fields, migration-decision emission, bundle happy path, missing artifacts, critical-law outcomes, release-gate hygiene. | Partial | It explicitly proves incomplete artifacts can pass: the legacy-`ttdsg` test passes with empty DSGVO/EU/state/relationship artifacts. |
| `mcp/tests/test_search_scaling.py` | Search and benchmark behavior over a generated temporary package with 120-160 norms. | Partial | Good regression coverage for fixture behavior, but not representative enough to validate full-corpus-scale memory/search budgets. |
| `.gitignore` assertions | Generated corpus exclusions do not ignore fixtures. | Yes | None found. |
| `scripts/verify_release.py` assertions | Operational tests are included while opt-in heavy scripts are not called by default. | Yes | None found. |

### Real-World Testing

Not performed by this reviewer. The implementer reports an opt-in bundle run against `.artifacts/...` inputs and a benchmark against the generated fixture package; live network/full import validation was intentionally not required for PR CI, which is consistent with Phase 12 scope. The residual risk is that the opt-in bundle can mark incomplete or placeholder artifacts as valid.

## Scope Compliance

### Findings

- No out-of-scope live network or full import work was added to the default release gate.
- The implementation stayed within operational scripts, tests, release-gate configuration, and ignore rules.

## Regression Risk

### Test Integrity Check

- [x] No reviewed Phase 12 tests were deleted.
- [x] No reviewed Phase 12 tests were disabled.
- [x] No reviewed Phase 12 assertions were weakened.
- [ ] All pre-existing tests were independently re-run by this reviewer.

### Findings

- I did not independently re-run the full test suite. The review relies on the supplied verification digest for pass/fail status and on source inspection for correctness findings.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Critical | Validation bundle | `verify_full_corpus_bundle.py` can exit successfully with placeholder artifacts for DSGVO, EU neighbors, state law, and relationships because it only wraps path/hash/schema/summary and checks `validation_errors`; it does not enforce required counts, policies, hashes, terminal outcomes, or validation status. | Add section-specific validators for GII, DSGVO, EU neighbors, state law, and relationships. Require the exact Phase 12 fields and fail on missing or mismatched evidence. Add negative tests proving each required field/outcome is enforced. |
| 2 | Major | Critical laws | `critical_law_evidence()` accepts an imported critical law based on a `law` object or `generated_law_ids` alone, and accepts any release-blocking limitation flag; it does not require MCP/HTTP resolution evidence from GII provenance or strict upstream-source-unavailable evidence. | Persist and validate critical-law import evidence including GII source path/source ID, generated norm IDs, package/runtime resolution, MCP and HTTP probe results, or a `source_unavailable` limitation with official upstream evidence and `release_blocking: true`. |
| 3 | Major | Threshold decisions | The benchmark emits migration decisions but also sets `status: failed` and exits non-zero when thresholds are missed; the bundle then rejects failed benchmark artifacts, so the phase's "budget met or migration decision recorded" acceptance path cannot pass. Defaults also use 5s/100ms/512MB instead of 120s/1s/2GB. | Align default thresholds with Phase 12 and model threshold misses as acceptable only when a complete migration decision record is present, or require a separate reviewed decision artifact that the bundle validates. |
| 4 | Major | Runtime memory benchmark | `run_benchmark()` builds `SearchService(dataset)` for sampled search but estimates memory using only `estimate_size_bytes(dataset)`, excluding the in-memory search rows that are part of runtime search behavior. | Include the search service/index rows in memory accounting, or explicitly record separate dataset and search-index memory estimates and gate the combined runtime footprint. |

## Recommendations

1. Block Phase 12 acceptance until the validation bundle enforces all required full-corpus evidence sections and critical-law proof.
2. Rework the benchmark threshold/migration-decision semantics so the documented acceptance alternatives are actually representable.
3. Add negative tests for missing DSGVO policy/hash, wrong article/recital counts, missing EU/state outcomes, incomplete relationship validation status, weak critical-law evidence, and threshold-miss decision handling.
