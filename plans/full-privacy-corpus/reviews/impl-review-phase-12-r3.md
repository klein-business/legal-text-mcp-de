# Phase 12 R3 Implementation Review

## Verdict

**Needs Rework.** R2 findings for live-test release gating and state-law fixed-code validation are resolved, and the imported critical-law cross-wiring case is now rejected. The source-unavailable critical-law fallback is still under-specified enough to certify a missing BDSG/TDDDG source without real upstream evidence, so the R2 critical-law finding is not fully resolved.

Targeted verification run: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_operational_corpus_gates.py mcp/tests/test_search_scaling.py mcp/tests/test_runtime_coverage_relationships.py mcp/tests/test_dsgvo_full_counts.py` -> 33 passed.

## Severity Counts

| Severity | Count |
| -------- | ----- |
| Critical | 1 |
| Major | 0 |
| Minor | 0 |
| Note | 2 |

## Top Findings

| # | Severity | Finding | Evidence | Recommendation |
| - | -------- | ------- | -------- | -------------- |
| 1 | Critical | `source_unavailable` critical-law fallback can still pass without real upstream evidence. `_validate_limited_critical_law()` requires `limitation_id`, source fields, official GII URL, reason, timestamp, and `release_blocking`, but treats `details.source_path` alone as upstream evidence and does not require HTTP/status/content evidence or explicit `official_upstream_evidence`. I confirmed `build_bundle()` returns exit code 0 for a BDSG `source_unavailable` limitation containing only `details.source_path` plus `release_blocking`, with no HTTP/status/content evidence and no official-upstream evidence flag. | `scripts/verify_full_corpus_bundle.py:374` checks the fallback; `scripts/verify_full_corpus_bundle.py:398` accepts any one of `http_status`, `error_code`, `content_type`, or `source_path`, so `source_path` alone satisfies the upstream-evidence branch. The R2 test at `mcp/tests/test_operational_corpus_gates.py:471` catches a completely bare limitation, but not the still-weak limitation shape. | Require a substantive upstream evidence signal such as `http_status`, `error_code`, or `content_type`, and require explicit official upstream evidence for release-blocking `source_unavailable` critical-law limitations. Add a regression test for the passing weak shape described above. |
| 2 | Note | R2 release-gate finding is resolved. | `scripts/verify_release.py:11` keeps default `TESTS` fixture-backed, `scripts/verify_release.py:43` isolates `LIVE_TESTS`, and `scripts/verify_release.py:46` includes live source probes only when `RUN_LIVE_SOURCE_MATRIX=true`. Tests at `mcp/tests/test_operational_corpus_gates.py:528` and `mcp/tests/test_operational_corpus_gates.py:544` cover default exclusion and opt-in inclusion. | No further action for the R2 release-gate finding. |
| 3 | Note | R2 state-law fixed-code finding is resolved. | `scripts/verify_full_corpus_bundle.py:18` imports `FIXED_STATE_CODES`, and `scripts/verify_full_corpus_bundle.py:493` through `scripts/verify_full_corpus_bundle.py:514` rejects duplicate, missing, and unknown state codes. The success fixture now uses `FIXED_STATE_CODES`, and `mcp/tests/test_operational_corpus_gates.py:401` covers unknown/missing state-code rejection. | No further action for the R2 state-law finding. |
