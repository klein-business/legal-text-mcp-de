# Phase 12 R4 Implementation Review

## Verdict

**Needs Rework.** The exact R3 `details.source_path`-only acceptance path is resolved, but the remaining Critical finding is not fully closed: `_validate_limited_critical_law()` still accepts a release-blocking `source_unavailable` critical-law limitation with no substantive upstream evidence if one of the evidence keys is present with an empty value. I found no separate new Phase 12 blocker.

## Severity Counts

| Severity | Count |
| -------- | ----- |
| Critical | 1 |
| Major | 0 |
| Minor | 0 |
| Note | 1 |

## Top Findings

| # | Severity | Finding | Evidence | Recommendation |
| - | -------- | ------- | -------- | -------------- |
| 1 | Critical | `source_unavailable` critical-law fallback can still pass without substantive upstream evidence. The R4 change removed `details.source_path` from the upstream-evidence check, but the validator only checks that `details.http_status`, `details.error_code`, or `details.content_type` is not `None`. A BDSG limitation with required source identity, official GII URL, limitation ID, reason, timestamp, `release_blocking: true`, and `details: {"source_path": "bdsg_2018", "content_type": ""}` returns `exit_code 0` with `critical_laws.status == "ready"` and no critical-law errors. | `scripts/verify_full_corpus_bundle.py:398` to `scripts/verify_full_corpus_bundle.py:401` uses `is not None` for evidence-field presence. `mcp/tests/test_operational_corpus_gates.py:494` covers `source_path`-only evidence, but not empty or non-substantive values for the accepted evidence keys. I also ran `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_operational_corpus_gates.py::test_full_corpus_bundle_rejects_source_path_only_upstream_evidence -q` -> 1 passed. | Require typed, non-empty evidence: for example an integer `http_status`, a non-empty `error_code`, a non-empty `content_type`, or `official_upstream_evidence is True`. Add a regression test for blank evidence values. |
| 2 | Note | The exact R3 source-path-only regression is fixed. | `scripts/verify_full_corpus_bundle.py:398` to `scripts/verify_full_corpus_bundle.py:401` no longer lists `source_path` as an accepted upstream-evidence field, and `mcp/tests/test_operational_corpus_gates.py:494` rejects the previous weak shape. | Keep the regression test. |
