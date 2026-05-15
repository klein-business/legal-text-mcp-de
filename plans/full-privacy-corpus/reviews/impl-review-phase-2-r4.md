---
type: review
entity: implementation-review
plan: "full-privacy-corpus"
phase: 2
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Review: Phase 2 - Generated package format and runtime compatibility

> Reviewing implementation of [Phase 2](../phases/phase-2.md)
> Against [Implementation Plan](../implementation/phase-2-impl.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Accepted

The final rework closes the single R3 Minor finding: non-file JSON package paths now return structured validation errors instead of raising filesystem exceptions. I rechecked the actual validator, generated-package regression tests, package fixtures, and updated docs, and found no remaining Critical, Major, Minor, or Note findings for Phase 2.

## Prior Findings Recheck

| Prior Finding | Status | Evidence | Remaining Gap |
| ------------- | ------ | -------- | ------------- |
| R3 Minor: non-file JSON package paths can raise `IsADirectoryError` instead of returning structured validation errors. | Closed | `_load_json` now checks `path.is_file()` and returns `"<label> must be a file"` before reading JSON in `mcp/legal_texts/validation.py:278-286`. Regression tests cover directory `package.json`, `laws.json`, `norms.json`, declared `manifest_path="."`, declared `readiness_path="."`, `relationships.json`, and `source-limitations.json` in `mcp/tests/test_generated_package.py:82-89`, `142-159`, `295-302`, `374-416`. | None. |

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Existing MCP and HTTP E2E checks pass against the fixture package. | Yes | `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py` exited 0 with 100 pytest tests passed, `HTTP CLI E2E OK`, and `MCP streamable HTTP E2E OK`. | None. |
| 2 | Package validation fails when manifest and normalized records disagree. | Yes | Bidirectional law/norm checks are implemented in `mcp/legal_texts/validation.py:462-488`; tests cover missing manifest-declared IDs and extra package IDs in `mcp/tests/test_generated_package.py:92-139`. | None. |
| 3 | Package validation rejects unsupported or malformed citation units. | Yes | `NormUnit` includes generated units in `mcp/legal_texts/models.py:8`; validation rejects unsupported units and malformed container combinations in `mcp/legal_texts/validation.py:216-225`; tests are in `mcp/tests/test_generated_package.py:419-489`. | None. Resolver support for new units remains correctly deferred. |
| 4 | Package validation rejects relationship records with missing provenance, unsupported relationship types, duplicate relationship IDs, or targets that resolve to neither official records nor source limitations. | Yes | Relationship validation covers source reconciliation, duplicate IDs, supported types, recursive copied-text rejection, provenance, endpoint kinds, and target resolution in `mcp/legal_texts/validation.py:574-680`; tests are in `mcp/tests/test_generated_package.py:210-292`. Manifest relationship-source copied-text validation remains covered by `mcp/legal_texts/manifest.py:357-384`. | None. |
| 5 | Existing `par` and `art` fixture behavior remains unchanged. | Yes | Existing resolver, HTTP, MCP, search, and E2E tests passed. The MCP registry test still asserts only the supported tool set in `mcp/tests/test_mcp_tools.py:20-22`. | None. |
| 6 | The package format can represent source failures without adding fake law or norm records. | Yes | Source limitations are validated and reconciled with manifest records in `mcp/legal_texts/validation.py:492-571`; tests cover undeclared, contradictory, and `imported` limitation records in `mcp/tests/test_generated_package.py:162-207`. The fixture represents `lim-state-be-missing` without adding a fake law or norm record. | None. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Define generated package metadata and optional files. | Implemented package metadata, manifest, readiness, hashes, source limitations, relationships, counts, and fixtures. | No | Meets Phase 2 scope. |
| 2 | Add additive citation-unit validation. | Implemented generated-unit typing and validation while keeping resolver behavior unchanged. | No | Meets scope; resolver support remains deferred. |
| 3 | Validate manifest and normalized-record consistency. | Implemented bidirectional law/norm checks and source-limitation reconciliation. | No | Meets scope. |
| 4 | Add relationship record schema validation. | Implemented relationship schema checks, target resolution, source reconciliation, and recursive copied-text checks in package records and manifest relationship sources. | No | Meets scope. |
| 5 | Preserve runtime and transport behavior. | Achieved; release gate and local HTTP/MCP E2E passed. | No | Meets scope. |
| 6 | Document generated package schemas. | Docs cover generated package layout, citation units, source limitations, relationships, strict validation, and deferred runtime surfaces. | No | Meets scope. |

## Code Quality Assessment

### Findings

No findings. The R3 JSON loading issue is fixed at the shared `_load_json` boundary, so all generated-package JSON entry points use the same missing-file, non-file, invalid-JSON, object/list-shape error path.

## Testing Assessment

### Verify Command Result

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: Passed: 100 pytest tests, `HTTP CLI E2E OK`, and `MCP streamable HTTP E2E OK`.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| Directory JSON-path regressions in `mcp/tests/test_generated_package.py` | Every R3 JSON package path returns structured `must be a file` errors without raising. | Yes | None. |
| Manifest/package mismatch tests | Missing and extra generated law/norm IDs are rejected with counts and hashes adjusted. | Yes | None. |
| Source-limitation tests | Undeclared limitations, same-ID contradictions, and impossible `imported` source limitations are rejected. | Yes | None. |
| Relationship tests | Missing provenance, duplicate IDs, unsupported types/kinds, unresolved targets, source mismatch, and copied-text fields are rejected. | Yes | None. |
| Existing resolver/MCP/HTTP/E2E tests | Backwards-compatible `par`/`art` behavior and transport stability. | Yes | None. |

### Real-World Testing

Performed: the release gate ran real local HTTP and MCP streamable-HTTP E2E checks against the fixture package. External live source probes were skipped with `SKIP_LIVE_SOURCE_MATRIX=true`; that is acceptable for Phase 2 because Phase 3+ bulk corpus generation and network-heavy corpus gates are explicitly out of scope.

## Scope Compliance

### Findings

No findings. The implementation does not require Phase 3+ bulk corpus generation, Phase 11 relationship lookup APIs, or resolver support for new units. Generated fixtures remain small and committable.

## Regression Risk

### Test Integrity Check

- [x] No existing tests were deleted.
- [x] No existing tests were disabled.
- [x] No existing assertions were weakened.
- [x] All pre-existing tests still pass in the release gate run.

### Findings

No findings. Regression risk for existing `par`/`art`, HTTP, MCP, resolver, and search behavior is low after the passing release gate.

## Findings Summary

| Severity | Count |
| -------- | ----- |
| Critical | 0 |
| Major | 0 |
| Minor | 0 |
| Note | 0 |

## Recommendations

1. Accept Phase 2 with no follow-up findings from this review.
