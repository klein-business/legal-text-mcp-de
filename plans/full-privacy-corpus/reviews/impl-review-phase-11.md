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

## Overall Assessment

**Verdict**: Needs Rework

The implementation is mostly additive and the new runtime, HTTP, and MCP surfaces are present. Relationship responses stay metadata/provenance-only, legacy fixture loading remains compatible, and the reported test commands pass. However, two Phase 11 acceptance requirements are not fully met: the local HTTP/MCP E2E gate still runs only against the legacy fixture package, and generated-package validation can accept new structural unit IDs that the resolver/API rejects.

**Finding count**: Critical 0, Major 2, Minor 0, Note 0.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Existing tools continue to return compatible responses. | Yes | `mcp/server.py` keeps the existing six tools and adds three Phase 11 tools; `mcp/tests/test_mcp_tools.py` verifies the full registry and old tool behavior; targeted pytest passed with 22 tests. | None found. |
| 2 | Clients can inspect corpus coverage and source failures. | Yes | `mcp/legal_texts/dataset.py` exposes `get_corpus_coverage()` and `get_source_limitations()`; `mcp/http_api.py` exposes `/corpus/coverage` and `/corpus/source-limitations`; generated fixture tests cover one source limitation. | None found. |
| 3 | Relationship metadata is returned separately from legal text. | Yes | `NormalizedDataset.get_related_norms()` returns relationship id/type, subject/object refs, source/provenance, and target summaries only; `validation.py` rejects copied/editorial text fields in relationship records; tests assert no serialized `text` field in the relationship response. | None found. |
| 4 | New citation units are accepted or rejected deterministically. | Partial | `models.py` normalizes `recital`, `chapter`, `section`, `annex`, and `container`; resolver tests cover numeric `chapter:1`, `section:1`, `annex:1`, and `container:1`. | Major finding 2: generated-package validation accepts non-numeric structural IDs such as `container:recitals`, but `parse_norm_reference()` rejects them before lookup. |
| 5 | Local HTTP/MCP E2E passes against representative generated fixture package. | No | `scripts/verify_e2e.py` passes, but it hardcodes `mcp/tests/fixtures/normalized` and asserts `generated_package_present is False`. | Major finding 1: no local HTTP/MCP transport E2E runs against `mcp/tests/fixtures/generated_package`. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Load coverage, limitations, and relationships in `NormalizedDataset`, with legacy compatibility. | Implemented optional `package.json`, manifest, source limitations, relationships, and state-law coverage loading; legacy package returns empty generated metadata. | No. | Meets the loader objective. |
| 2 | Add shared runtime methods. | `LegalTextRuntime` delegates coverage, limitations, and related-norm lookup through the dataset. | No. | Meets the shared service objective. |
| 3 | Add MCP tools additively. | `get_corpus_coverage`, `get_source_limitations`, and `get_related_norms` are registered without removing existing tools. | No. | Meets MCP surface objective. |
| 4 | Add HTTP endpoints/models. | `/corpus/coverage`, `/corpus/source-limitations`, and `/laws/{code}/norms/{norm:path}/relationships` are present; relationship route is before the norm catch-all. | No. | Meets HTTP surface objective. |
| 5 | Add resolver/API coverage for new units. | Numeric new units are supported and tested. | Yes. | Generated-package validation and resolver grammar disagree for non-numeric structural IDs, leaving some valid records unreachable by API. |

## Code Quality Assessment

### Findings

- **Major**: Generated-package validation and resolver grammar disagree for new structural unit values. `validate_norms()` checks that the unit is one of the allowed generated units and that `canonical_id == law_id/norm_id`, but it does not enforce the resolver's numeric value grammar. The resolver regex only accepts `[0-9]+[a-z]?` values for all units, so package-valid records like `container:recitals`, `chapter:fixture`, or `annex:i` cannot be resolved through `get_norm()` or the HTTP/MCP norm paths. Align the package schema and resolver grammar, then add positive and negative API tests for whichever value set is intended.

## Testing Assessment

### Verify Command Result

- **Command**: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_runtime_coverage_relationships.py mcp/tests/test_http_api.py mcp/tests/test_mcp_tools.py mcp/tests/test_resolver.py`
- **Exit Code**: 0
- **Result**: 22 passed.

- **Command**: `PYTHONPATH=mcp uv run --group dev python scripts/verify_e2e.py`
- **Exit Code**: 0
- **Result**: HTTP CLI E2E OK; MCP streamable HTTP E2E OK. This result is legacy-fixture-only.

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: 205 passed; HTTP CLI E2E OK; MCP streamable HTTP E2E OK. The release verifier reuses the same legacy-fixture-only E2E script.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `mcp/tests/test_runtime_coverage_relationships.py` | Legacy empty metadata, generated package metadata/limitation/relationship loading, metadata-only relationship response. | Yes. | Does not exercise transport E2E. |
| `mcp/tests/test_http_api.py` | HTTP coverage, limitation, relationship endpoints through `TestClient`, including generated package fixture. | Yes. | In-process only; does not satisfy local server E2E. |
| `mcp/tests/test_mcp_tools.py` | Tool registry, structured return values, generated-package relationship tools through internal tool manager. | Yes. | In-process only; does not satisfy streamable HTTP MCP E2E for generated packages. |
| `mcp/tests/test_resolver.py` | Legacy citations, child article/paragraph behavior, recital lookup, and numeric generated unit lookup. | Partially. | Does not cover package-valid non-numeric structural unit IDs or explicit negative tests for new unit grammar. |
| `scripts/verify_e2e.py` | Local HTTP and MCP process startup and legacy endpoint/tool behavior. | Partially. | It does not run against the representative generated fixture package required by Phase 11. |

### Real-World Testing

Performed partially. I reran the local HTTP/MCP E2E command and the skipped-live release verifier successfully, but both use the legacy normalized fixture. Real local transport testing against `mcp/tests/fixtures/generated_package` was not performed and remains a Phase 11 acceptance gap.

## Scope Compliance

### Findings

- No scope-expansion findings. The implementation stays within the Phase 11 runtime/API/testing scope and does not add new importers, source-family behavior, or legal-text content.

## Regression Risk

### Test Integrity Check

- [x] No reviewed Phase 11 tests were deleted.
- [x] No reviewed Phase 11 tests were disabled.
- [x] No reviewed Phase 11 assertions were weakened in the inspected files.
- [x] Targeted Phase 11 tests and skipped-live release verifier pass.

### Findings

- **Major**: The E2E gate does not exercise the generated package path. `scripts/verify_e2e.py` sets `DATASET = ROOT / "mcp" / "tests" / "fixtures" / "normalized"` and asserts `coverage["generated_package_present"] is False`, so the passing E2E result cannot catch transport/startup regressions in generated-package coverage, limitations, or relationships. Add a generated-package E2E pass or parameterize the script and include assertions for `generated_package_present: true`, non-empty source limitations, and the generated relationship lookup.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | E2E Coverage | Local HTTP/MCP E2E is legacy-fixture-only and does not test the representative generated package required by Phase 11. | Add or parameterize an E2E run for `mcp/tests/fixtures/generated_package` and assert generated coverage, source limitation, and relationship responses over HTTP and MCP transport. |
| 2 | Major | Resolver Contract | Generated-package validation can accept structural/new unit IDs that the resolver/API rejects, making valid package records unreachable. | Align validation and resolver value rules; either reject non-numeric structural IDs during package validation or support them in `parse_norm_reference()`/structured resolution, with positive and negative API tests. |

## Recommendations

1. Rework required before acceptance: add generated-package HTTP/MCP E2E coverage to the local E2E/release gate.
2. Rework required before acceptance: make the generated-package citation-unit contract and resolver grammar consistent for new units, especially structural containers and annex/chapter/section values.
