---
type: review
entity: implementation-review
plan: "full-privacy-corpus"
phase: 11
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Review: Phase 11 - Runtime coverage and relationship APIs

> Reviewing implementation of [Phase 11](../phases/phase-11.md)
> Against [Implementation Plan](../implementation/phase-11-impl.md) and [Plan](../plan.md)
> Re-review after [previous implementation review](impl-review-phase-11.md)

## Overall Assessment

**Verdict**: Needs Rework

The previous E2E coverage finding is resolved: `scripts/verify_e2e.py` now runs separate legacy and generated-package HTTP/MCP server pairs and asserts generated coverage, source limitations, and relationship lookup over both transports. The resolver/validator contract was also substantially hardened for slug-like structural values and numeric `par`/`art`/`recital` values, but one validation/runtime normalization gap remains: generated-package validation still accepts uppercase citation values that public resolver paths lowercase before lookup, making package-valid records unreachable.

**Finding count**: Critical 0, Major 1, Minor 0, Note 0.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Existing tools continue to return compatible responses. | Yes | `mcp/server.py` keeps the original tools and adds `get_corpus_coverage`, `get_source_limitations`, and `get_related_norms`; `mcp/tests/test_mcp_tools.py` verifies the full registry and old tool behavior. Targeted pytest passed with 61 tests. | None found. |
| 2 | Clients can inspect corpus coverage and source failures. | Yes | `mcp/legal_texts/dataset.py` exposes `get_corpus_coverage()` and filtered `get_source_limitations()`; `mcp/http_api.py` exposes `/corpus/coverage` and `/corpus/source-limitations`; MCP exposes matching tools. Runtime, HTTP, MCP, and E2E tests cover the generated-package fixture. | None found. |
| 3 | Relationship metadata is returned separately from legal text. | Yes | `NormalizedDataset.get_related_norms()` returns relationship ID/type, endpoints, provenance, and target summary without relationship `metadata` or legal text; `validation.py` rejects copied/editorial text fields; tests assert no serialized `text` field in relationship output. | None found. |
| 4 | New citation units are accepted or rejected deterministically. | Partial | `mcp/legal_texts/resolver.py` accepts slug-like values for `chapter`, `section`, `annex`, and `container`, keeps `par`/`art`/`recital` numeric, and preserves `art:246a/par:1`; `mcp/tests/test_resolver.py` covers slug-like structural positives and malformed negatives. `mcp/legal_texts/validation.py` enforces unit/value and norm_id/value alignment for generated packages. | Major finding 1: validation accepts uppercase values that resolver canonicalization lowercases before lookup. |
| 5 | Local HTTP/MCP E2E passes against representative generated fixture package. | Yes | `scripts/verify_e2e.py` defines `GENERATED_PACKAGE`, runs `run_case("generated-package", ...)`, and asserts generated-package coverage, limitation, and relationship responses over HTTP and MCP. The command passed locally. | None found. |

## Previous Findings Re-Review

| Previous Finding | Current Status | Evidence |
| ---------------- | -------------- | -------- |
| Major: E2E Coverage | Resolved | `scripts/verify_e2e.py` now runs both `legacy` and `generated-package` cases. Generated HTTP checks assert `generated_package_present is True`, one source limitation, and `rel-dsgvo-art5-limitation`; generated MCP checks assert the same over streamable HTTP. |
| Major: Resolver Contract | Mostly resolved, one residual edge remains | The resolver accepts slug-like structural values and rejects malformed structural/numeric values through public APIs. Generated-package validation rejects malformed structural values, malformed numeric values, and norm_id/value mismatches. The remaining gap is case normalization: validation accepts uppercase values that resolver lookup normalizes to lowercase. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Load coverage, limitations, and relationships in `NormalizedDataset`, with legacy compatibility. | Implemented optional package metadata, manifest summary, source limitations, relationships, and state-law coverage loading; legacy packages return empty generated metadata. | No. | Meets the loader objective. |
| 2 | Add shared runtime service methods. | `LegalTextRuntime` delegates coverage, limitations, and related-norm lookup through the dataset. | No. | Meets the shared service objective. |
| 3 | Add MCP tools additively. | `get_corpus_coverage`, `get_source_limitations`, and `get_related_norms` are registered without removing existing tools. | No. | Meets the MCP surface objective. |
| 4 | Add HTTP endpoints/models. | `/corpus/coverage`, `/corpus/source-limitations`, and `/laws/{code}/norms/{norm:path}/relationships` are present and tested. | No. | Meets the HTTP surface objective. |
| 5 | Add resolver/API coverage for new units. | Slug-like new units and malformed values are covered in resolver tests; generated-package validation has positive and negative unit/value tests. | Partial. | The value case-normalization contract is still not validation-aligned. |

## Code Quality Assessment

### Findings

- **Major**: Generated-package validation accepts uppercase citation values that public resolver paths cannot resolve. `NUMERIC_NORM_VALUE_RE`, `STRUCTURAL_NORM_VALUE_RE`, and `CHILD_ART_PAR_NORM_ID_RE` in `mcp/legal_texts/validation.py` are compiled with `re.IGNORECASE`, and `_validate_norm_id_and_value()` accepts `norm_id == f"{unit}:{value}"` without checking that `value` is already canonical lowercase. The resolver path lowercases parsed values in `parse_norm_reference()` and again via `normalize_value()`, so a package-valid record such as `dsgvo_eu_2016_679/container:Recitals` is looked up as `container:recitals` and returns `NORM_NOT_FOUND`. This leaves a narrow but real version of the prior resolver-contract issue: validation can certify records that MCP/HTTP cannot serve.

## Testing Assessment

### Verify Command Result

- **Command**: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_generated_package.py mcp/tests/test_runtime_coverage_relationships.py mcp/tests/test_http_api.py mcp/tests/test_mcp_tools.py mcp/tests/test_resolver.py`
- **Exit Code**: 0
- **Result**: 61 passed.

- **Command**: `PYTHONPATH=mcp uv run --group dev python scripts/verify_e2e.py`
- **Exit Code**: 0
- **Result**: legacy HTTP CLI E2E OK; legacy MCP streamable HTTP E2E OK; generated-package HTTP CLI E2E OK; generated-package MCP streamable HTTP E2E OK.

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: 209 passed; legacy/generated-package E2E OK.

- **Command**: `PYTHONPATH=mcp uv run --group dev python - <<'PY' ... validate_generated_package(Path("mcp/tests/fixtures/generated_package"), require_search_index=True) ... PY`
- **Exit Code**: 0
- **Result**: `[]`.

### Additional Contract Probe

- **Command**: temporary generated-package mutation adding `dsgvo_eu_2016_679/container:Recitals`, followed by `validate_generated_package(..., require_search_index=True)` and `get_norm(..., "container:Recitals")`.
- **Exit Code**: 0
- **Result**: validation returned `[]`, but public lookup returned `NORM_NOT_FOUND` for `container:recitals`.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `mcp/tests/test_runtime_coverage_relationships.py` | Legacy empty metadata, generated package metadata/limitation/relationship loading, and metadata-only relationship responses. | Yes. | No issue found. |
| `mcp/tests/test_http_api.py` | HTTP coverage, limitation, relationship endpoints through `TestClient`, including the generated package fixture. | Yes. | No issue found. |
| `mcp/tests/test_mcp_tools.py` | Tool registry, existing tool compatibility, generated-package coverage/limitation/relationship tools. | Yes. | No issue found. |
| `mcp/tests/test_resolver.py` | Legacy citations, `art:246a/par:1`, recital lookup, slug-like structural lookups, malformed structural/numeric references. | Mostly. | Missing uppercase-value regression coverage for validation/runtime alignment. |
| `mcp/tests/test_generated_package.py` | Generated package metadata, hashes, manifest references, limitations, relationships, new units, malformed values, and norm_id/value mismatches. | Mostly. | Missing rejection tests for non-canonical uppercase norm values. |
| `scripts/verify_e2e.py` | Real local HTTP and MCP process startup for legacy and generated-package fixtures. | Yes. | The previous generated-package E2E gap is resolved. |

### Real-World Testing

Performed. I ran the local HTTP/MCP E2E command, which starts real HTTP and MCP server processes for both the legacy fixture and `mcp/tests/fixtures/generated_package`. External live source probes were intentionally skipped only in the release verifier via `SKIP_LIVE_SOURCE_MATRIX=true`, matching the supplied verification scope.

## Scope Compliance

### Findings

- No scope-expansion findings. The inspected implementation stays within Phase 11 runtime/API/testing scope and does not add unrelated importer behavior or legal-text content.

## Regression Risk

### Test Integrity Check

- [x] No reviewed Phase 11 tests were deleted.
- [x] No reviewed Phase 11 tests were disabled.
- [x] No reviewed Phase 11 assertions were weakened in the inspected files.
- [x] Targeted Phase 11 tests, local E2E, and skipped-live release verifier pass.

### Findings

- **Major**: The current tests do not cover the uppercase validation/runtime mismatch. Without this regression case, a future package can pass `validate_generated_package()` but remain unreachable through HTTP and MCP norm lookup.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Resolver Contract | Generated-package validation accepts uppercase citation values, but resolver/API lookup lowercases values before lookup, making package-valid records such as `container:Recitals` unreachable. | Align validation with runtime canonicalization by rejecting non-normalized values/norm IDs/canonical IDs, or preserve case consistently through resolver lookup. Add generated-package validation and resolver/API regression tests for uppercase structural values and uppercase numeric suffixes. |

## Recommendations

1. Rework required before acceptance: close the remaining value-normalization gap between generated-package validation and public resolver lookup.
2. After the fix, rerun the targeted Phase 11 suite, `scripts/verify_e2e.py`, and the skipped-live release verifier.
