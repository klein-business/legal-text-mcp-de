# Phase 12 R5 Implementation Review

## Verdict

**Needs Rework.** The exact R4 empty-value bypass is fixed, but the remaining Critical finding is not fully resolved: `_has_substantive_upstream_evidence()` still accepts a boolean `http_status` as substantive upstream evidence because `bool` is an `int` subclass in Python. I found no separate new Phase 12 blocker.

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
| 1 | Critical | `source_unavailable` critical-law fallback can still pass without substantive upstream evidence. `http_status: true` is accepted as an integer status value, allowing a release-blocking BDSG limitation with no real HTTP status, error code, content type, or explicit `official_upstream_evidence`. | `scripts/verify_full_corpus_bundle.py:410` to `scripts/verify_full_corpus_bundle.py:412` uses `isinstance(http_status, int) and http_status > 0`, which treats `True` as valid. A manual bundle probe with `details: {"source_path": "bdsg_2018", "http_status": true, "release_blocking": true}` returned `exit_code=0`, `critical_laws.evidence.bdsg_2018.status="ready"`, and no BDSG critical-law errors. `mcp/tests/test_operational_corpus_gates.py:519` covers empty strings and `http_status: 0`, but not boolean `http_status`. | Require `type(http_status) is int and http_status > 0` or explicitly reject booleans before accepting numeric status evidence. Add a regression test for `http_status: true`. |
| 2 | Note | The R4 empty-value case is fixed. | `scripts/verify_full_corpus_bundle.py:413` to `scripts/verify_full_corpus_bundle.py:417` requires non-empty string `error_code` / `content_type` or `official_upstream_evidence is True`, and `mcp/tests/test_operational_corpus_gates.py:519` rejects blank evidence values. `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_operational_corpus_gates.py -q` passed with `21 passed`. | Keep the empty-value regression test. |
