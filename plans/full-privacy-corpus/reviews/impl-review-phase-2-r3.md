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

The R2 rework closes the two Major strictness gaps and the Minor hash-validation robustness issue from the previous review. Phase 2 acceptance is met: generated-package validation is strict for manifest/record agreement, citation units, source limitations, relationships, hashes/readiness, and current MCP/HTTP behavior remains unchanged. I found one new Minor robustness issue where non-file JSON package paths can still raise instead of returning structured validation errors; it should be tracked, but it does not block Phase 2 acceptance.

## Prior Findings Recheck

| Prior Finding | Status | Evidence | Remaining Gap |
| ------------- | ------ | -------- | ------------- |
| Major: package source limitations can contradict manifest `source_limitations`. | Closed | `mcp/legal_texts/validation.py:490-541` now reconciles package limitations to manifest limitations by `limitation_id` and compares `source_family`, `source_id`, `terminal_state`, `source_url`, `retrieved_at`, and `decided_at`. `mcp/tests/test_generated_package.py:148-177` covers same-ID contradictions and `terminal_state="imported"`. | None blocking. |
| Major: nested copied/editorial text can appear in manifest `relationship_sources`. | Closed | `mcp/legal_texts/manifest.py:357-384` now calls recursive `_find_forbidden_field_paths`, defined at `mcp/legal_texts/manifest.py:446-458`. `mcp/tests/test_corpus_manifest.py:101-110` covers nested `metadata.nested.editorial_text`. | None. |
| Minor: non-file `content_hashes` targets raise filesystem exceptions. | Closed | `mcp/legal_texts/validation.py:352-360` now checks safe package-relative paths, existence, and `is_file()` before reading bytes. `mcp/tests/test_generated_package.py:323-330` covers a directory hash target. | None for `content_hashes`. |

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Existing MCP and HTTP E2E checks pass against the fixture package. | Yes | `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py` exited 0 with 93 pytest tests passed, `HTTP CLI E2E OK`, and `MCP streamable HTTP E2E OK`. | None. |
| 2 | Package validation fails when manifest and normalized records disagree. | Yes | Bidirectional law/norm manifest consistency is in `mcp/legal_texts/validation.py:460-487`; tests at `mcp/tests/test_generated_package.py:76-129` cover missing and extra generated IDs. | None. |
| 3 | Package validation rejects unsupported or malformed citation units. | Yes | `NormUnit` includes generated units at `mcp/legal_texts/models.py:8`; validation rejects unsupported units and malformed container status/text at `mcp/legal_texts/validation.py:216-225`; tests at `mcp/tests/test_generated_package.py:332-397` cover allowed and malformed units. | None. Resolver support for new units remains correctly deferred. |
| 4 | Package validation rejects relationship records with missing provenance, unsupported relationship types, duplicate relationship IDs, or targets that resolve to neither official records nor source limitations. | Yes | `mcp/legal_texts/validation.py:572-673` validates relationship fields, duplicate IDs, types, source reconciliation, recursive copied-text rejection, provenance, endpoint kinds, and target resolution. Tests at `mcp/tests/test_generated_package.py:180-262` cover these cases. | None. |
| 5 | Existing `par` and `art` fixture behavior remains unchanged. | Yes | Existing resolver, MCP, HTTP, search, and E2E tests all pass in the release gate. No Phase 11 relationship APIs or resolver support for new units were added. | None. |
| 6 | The package format can represent source failures without adding fake law or norm records. | Yes | The generated fixture uses `source-limitations.json` for `lim-state-be-missing`; relationship targets resolve to that limitation; source limitations are reconciled with manifest records in `mcp/legal_texts/validation.py:490-541`. | None. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Define generated package metadata and optional files. | Implemented package metadata, manifest, readiness, hashes, source limitations, relationships, counts, and fixtures. | No | Meets Phase 2 scope. |
| 2 | Add additive citation-unit validation. | Implemented generated-unit typing and validation while keeping resolver behavior unchanged. | No | Meets scope; runtime resolver support remains deferred. |
| 3 | Validate manifest and normalized-record consistency. | Implemented bidirectional law/norm checks and source-limitation reconciliation. | No | R2 source-limitation contradiction gap is closed. |
| 4 | Add relationship record schema validation. | Implemented relationship schema checks, target resolution, source reconciliation, and recursive copied-text checks in package records and manifest relationship sources. | No | Meets Phase 2 relationship package scope. |
| 5 | Preserve runtime and transport behavior. | Achieved; release gate and local HTTP/MCP E2E passed. | No | Meets scope. |
| 6 | Document generated package schemas. | Docs cover package layout, generated units, source limitations, relationships, strict validation, and fixture-vs-generated behavior. | No | Docs no longer overstate the R2-fixed behavior. |

## Code Quality Assessment

### Findings

- **Minor**: Non-file JSON package paths can still raise `IsADirectoryError` instead of returning structured validation errors. Evidence: `_load_json` only handles missing files and `JSONDecodeError`, while `validate_generated_package` calls `_load_json_object` / `_load_json_list` for `package.json`, `laws.json`, `norms.json`, `manifest_path`, `readiness_path`, `source-limitations.json`, and `relationships.json` without a file-type guard at `mcp/legal_texts/validation.py:122-172`. Manual probes that set `manifest_path="."`, `readiness_path="."`, or replaced package JSON files with directories raised `IsADirectoryError`. This is adjacent to, but separate from, the now-fixed `content_hashes` directory target case.

## Testing Assessment

### Verify Command Result

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: Passed: 93 pytest tests, `HTTP CLI E2E OK`, and `MCP streamable HTTP E2E OK`.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `test_generated_package_rejects_source_limitation_same_id_contradiction` | Same-ID package limitation changes to source family, source ID, terminal state, source URL, and retrieval timestamp. | Yes | None. |
| `test_generated_package_rejects_imported_source_limitation_terminal_state` | Source limitations cannot claim `terminal_state="imported"`. | Yes | None. |
| `test_relationship_sources_reject_nested_copied_editorial_text_fields` | Manifest relationship sources reject nested copied/editorial text paths. | Yes | None. |
| `test_generated_package_rejects_directory_content_hash_target_without_raising` | Directory entries in `content_hashes` return validation errors. | Yes | Does not cover non-file JSON package paths, which is the Minor finding above. |
| Existing resolver/MCP/HTTP/E2E tests | Backwards-compatible `par`/`art` behavior and transport stability. | Yes | None. |

### Real-World Testing

Performed: the release gate ran real local HTTP and MCP streamable-HTTP E2E checks against the fixture package. External live source probes were skipped with `SKIP_LIVE_SOURCE_MATRIX=true`, which is acceptable for Phase 2 because bulk corpus generation and network-heavy corpus gates are explicitly deferred.

## Scope Compliance

### Findings

- No out-of-scope Phase 3+ bulk corpus generation was required or introduced.
- No Phase 11 relationship lookup APIs were added.
- No resolver support for `recital`, `chapter`, `section`, `annex`, or generated `container` units was required or added.
- Generated fixtures remain small and committable.

## Regression Risk

### Test Integrity Check

- [x] No existing tests were deleted.
- [x] No existing tests were disabled.
- [x] No existing assertions were weakened.
- [x] All pre-existing tests still pass in the release gate run.

### Findings

- Regression risk for existing `par`/`art`, HTTP, MCP, resolver, and search behavior is low after the passing release gate.
- Generated-package strictness risk is materially reduced from R2. The remaining JSON non-file path handling issue is a malformed-package robustness edge case.

## Documentation Check

The reviewed docs in `docs/features/law-loading-and-indexing.md`, `docs/features/source-provenance.md`, `docs/modules/mcp-server.md`, and `docs/overview.md` match Phase 2 behavior for generated package layout, strict validation, source limitations, relationship metadata, and deferred runtime surfaces. The only caveat is the Minor code finding above: docs say malformed generated packages fail readiness, but some non-file JSON package paths currently raise before readiness can be returned.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Minor | Validation robustness | Non-file JSON package paths can raise `IsADirectoryError` instead of returning structured validation errors. | Add an `is_file()` check or catch `OSError` in `_load_json`, and add regressions for directory `package.json`, `laws.json`, `norms.json`, declared `manifest_path`, declared `readiness_path`, `relationships.json`, and `source-limitations.json`. |

## Recommendations

1. Accept Phase 2; the R2 blocking findings are closed and acceptance criteria are met.
2. Track the Minor malformed-package robustness issue as follow-up before relying on generated-package validation for broader producer inputs.
