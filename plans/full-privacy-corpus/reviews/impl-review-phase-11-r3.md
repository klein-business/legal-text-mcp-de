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
> Re-review after [previous implementation review](impl-review-phase-11.md) and [second re-review](impl-review-phase-11-r2.md)

## Overall Assessment

**Verdict**: Accepted

The latest rework resolves the remaining Phase 11 blocker: generated-package validation now rejects non-canonical uppercase `canonical_id`, `norm_id`, and `value` records before they can become runtime-unreachable, while resolver input canonicalization remains deterministic for client requests. The prior generated-package E2E gap also remains resolved: the local E2E verifier starts separate legacy and generated-package HTTP/MCP server pairs and asserts coverage, source limitation, and relationship behavior over both transports. I found no remaining functional or technical findings against the Phase 11 acceptance criteria.

**Finding count**: Critical 0, Major 0, Minor 0, Note 0.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Existing tools continue to return compatible responses. | Yes | `mcp/server.py` keeps the original tools and adds only `get_corpus_coverage`, `get_source_limitations`, and `get_related_norms`; `mcp/tests/test_mcp_tools.py` verifies the complete registry and legacy tool behavior. Focused pytest passed: 65 tests. | None found. |
| 2 | Clients can inspect corpus coverage and source failures. | Yes | `mcp/legal_texts/dataset.py` loads package metadata, manifest summaries, source limitations, relationships, and state-law coverage; `mcp/legal_texts/runtime.py`, `mcp/http_api.py`, and `mcp/server.py` expose shared HTTP/MCP surfaces. HTTP, MCP, runtime, and E2E checks cover generated-package limitations. | None found. |
| 3 | Relationship metadata is returned separately from legal text. | Yes | `NormalizedDataset.get_related_norms()` returns relationship IDs/types, endpoints, provenance, and target summaries without legal text; `validation.py` rejects copied/editorial text fields in relationship records; tests assert no serialized `text` appears in relationship output. | None found. |
| 4 | New citation units are accepted or rejected deterministically. | Yes | `resolver.py` accepts `recital`, `chapter`, `section`, `annex`, and `container`, with numeric validation for `par`/`art`/`recital` and slug validation for structural units. `validation.py` uses matching lowercase value grammar, and tests cover valid generated units plus malformed and uppercase package values. | None found. |
| 5 | Local HTTP/MCP E2E passes against representative generated fixture package. | Yes | `scripts/verify_e2e.py` runs both `legacy` and `generated-package` cases and asserts generated coverage, source limitations, and relationship lookup over HTTP and MCP. The command passed locally. | None found. |

## Previous Findings Re-Review

| Previous Finding | Current Status | Evidence |
| ---------------- | -------------- | -------- |
| r1 Major: E2E coverage was legacy-fixture-only. | Resolved | `scripts/verify_e2e.py` defines `GENERATED_PACKAGE`, runs `run_case("generated-package", ...)`, and asserts generated coverage, limitation, and relationship responses over HTTP and MCP. |
| r1/r2 Major: Generated-package validation and resolver grammar disagreed for structural units. | Resolved | `resolver.py` now supports slug-like structural values and rejects malformed references; `validation.py` enforces numeric vs structural value grammar for generated records. |
| r2 Major: Validation accepted uppercase package values that runtime lowercased before lookup. | Resolved | `_validate_norm_id_and_value()` rejects uppercase `canonical_id`, `value`, and `norm_id`; tests cover `container:Recitals`, `chapter:Overview`, `art:5A`, and uppercase canonical IDs. A temporary `container:Recitals` package mutation is rejected with canonical lowercase/value errors. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Load coverage, limitations, and relationships in `NormalizedDataset`, with legacy compatibility. | Implemented optional package metadata, manifest summary, source limitations, relationship records, and state-law coverage loading; legacy packages return empty generated metadata. | No. | Meets the loader objective. |
| 2 | Add shared runtime service methods. | `LegalTextRuntime` exposes shared `get_corpus_coverage()`, `get_source_limitations(...)`, and `get_related_norms(...)` methods. | No. | Meets the shared service objective. |
| 3 | Add MCP tools additively. | MCP registers three new tools without removing or renaming existing tools. | No. | Meets the MCP surface objective. |
| 4 | Add HTTP endpoints/models. | HTTP exposes `/corpus/coverage`, `/corpus/source-limitations`, and `/laws/{code}/norms/{norm:path}/relationships` with response models and OpenAPI tests. | No. | Meets the HTTP surface objective. |
| 5 | Add resolver/API coverage for new units. | Resolver and generated-package validation now share the intended lowercase canonical unit/value contract, and tests cover positives and negatives. | No. | Meets the resolver/API objective. |

## Code Quality Assessment

### Findings

No findings. The implementation is additive, keeps transport-specific behavior thin over `LegalTextRuntime`, preserves legacy package compatibility, and validates generated-package records before runtime loading. Relationship responses remain metadata/provenance-only and avoid copied legal or editorial text.

## Testing Assessment

### Verify Command Result

- **Command**: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_generated_package.py mcp/tests/test_runtime_coverage_relationships.py mcp/tests/test_http_api.py mcp/tests/test_mcp_tools.py mcp/tests/test_resolver.py`
- **Exit Code**: 0
- **Result**: 65 passed.

- **Command**: `PYTHONPATH=mcp uv run --group dev python scripts/verify_e2e.py`
- **Exit Code**: 0
- **Result**: legacy HTTP CLI E2E OK; legacy MCP streamable HTTP E2E OK; generated-package HTTP CLI E2E OK; generated-package MCP streamable HTTP E2E OK.

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: 213 passed; legacy/generated-package E2E OK.

- **Command**: direct generated-package validation and temporary uppercase `container:Recitals` mutation probe.
- **Exit Code**: 0
- **Result**: current generated fixture validates with `[]`; uppercase mutation is rejected for canonical lowercase `canonical_id`, `value`, and `norm_id`, plus structural value grammar.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `mcp/tests/test_generated_package.py` | Package validation, hashes, manifest references, limitations, relationships, generated units, malformed values, and lowercase canonicalization regressions. | Yes. | None found. |
| `mcp/tests/test_runtime_coverage_relationships.py` | Legacy empty generated metadata and generated package coverage, limitation, and relationship loading. | Yes. | None found. |
| `mcp/tests/test_http_api.py` | In-process HTTP coverage, source limitation, relationship endpoints, and OpenAPI path exposure. | Yes. | None found. |
| `mcp/tests/test_mcp_tools.py` | MCP tool registry compatibility, JSON object responses, generated-package coverage, limitation, and relationship tools. | Yes. | None found. |
| `mcp/tests/test_resolver.py` | Legacy citations, `art:246a/par:1`, recital lookup, structural unit lookup, and malformed new-unit references. | Yes. | None found. |
| `scripts/verify_e2e.py` | Real local HTTP and MCP process startup for both legacy and generated-package fixtures. | Yes. | None found. |

### Real-World Testing

Performed for Phase 11's runtime surfaces. The local E2E command starts real HTTP and MCP processes for both fixture families and exercises coverage, source limitation, relationship, norm, search, and error behavior through transport boundaries. External live source probes were intentionally skipped only in the release verifier via `SKIP_LIVE_SOURCE_MATRIX=true`, which is consistent with the supplied verification scope and Phase 11's fixture-backed runtime/API focus.

## Scope Compliance

### Findings

No findings. The implementation stays within Phase 11 runtime/API/testing scope and does not add unrelated import behavior, source-family expansion, or legal-text content.

## Regression Risk

### Test Integrity Check

- [x] No reviewed Phase 11 tests were deleted.
- [x] No reviewed Phase 11 tests were disabled.
- [x] No reviewed Phase 11 assertions were weakened.
- [x] Focused Phase 11 tests, local E2E, and skipped-live release verifier pass.

### Findings

No findings. The remaining regression risk is limited to future generated package variants beyond the representative fixture set; the canonicalization and E2E regressions identified in prior reviews are now covered.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| - | - | - | No findings. | No rework required for Phase 11 acceptance. |

## Recommendations

1. Accept Phase 11 as implemented.
