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

**Verdict**: Needs Rework

The rework closes the main generated law/norm consistency, required hash/readiness, relationship-record, and generated-unit gaps from the first review, and the release gate passes with the expected local HTTP/MCP E2E coverage. However, strict package validation still allows `source-limitations.json` to contradict the manifest and still allows copied/editorial text inside nested manifest relationship-source metadata, so the package contract can still overstate provenance and metadata-only guarantees.

## Prior Findings Recheck

| Prior Finding | Status | Evidence | Remaining Gap |
| ------------- | ------ | -------- | ------------- |
| Major: reverse manifest/package consistency and source/relationship reconciliation | Partial | Extra laws/norms are now rejected by `_validate_manifest_record_references` in `mcp/legal_texts/validation.py:457-484`, with tests at `mcp/tests/test_generated_package.py:94-129`. Relationship source IDs are checked against manifest `relationship_sources` in `mcp/legal_texts/validation.py:559-578`, with a test at `mcp/tests/test_generated_package.py:148-157`. | Package source limitations are reconciled only by `limitation_id` when manifest limitation IDs exist. A package limitation can keep the manifest ID but change `source_id`, `source_url`, or `terminal_state`, update the hash, and `validate_generated_package` returns `[]`. |
| Major: required package hashes and readiness existence | Closed | `_validate_package_hashes` now requires `laws.json`, `norms.json`, declared `manifest_path`, declared `readiness_path`, and present optional files in `mcp/legal_texts/validation.py:328-344`; missing readiness is loaded as an error through `mcp/legal_texts/validation.py:137-159`. Tests cover empty hashes, missing optional-file hash, and missing readiness at `mcp/tests/test_generated_package.py:266-298`. | Separate Minor robustness issue remains for hash entries that point at directories. |
| Major: nested copied/editorial text in relationship records | Closed for `relationships.json` | `_find_forbidden_field_paths` recursively walks dicts/lists in `mcp/legal_texts/validation.py:614-626`, and `_validate_relationships` rejects those paths in `mcp/legal_texts/validation.py:579-581`. Test coverage exists at `mcp/tests/test_generated_package.py:221-230`. | The same recursive protection is not applied to manifest `relationship_sources`, which are also generated-package relationship-source metadata. |
| Minor: generated citation model/container schema mismatch | Closed | `NormUnit` includes generated units in `mcp/legal_texts/models.py:8`; generated container status/text combinations are checked in `mcp/legal_texts/validation.py:219-225`. Tests cover allowed units and malformed container combinations at `mcp/tests/test_generated_package.py:300-370`. | None for Phase 2. Resolver support for new units remains correctly deferred. |
| Minor: missing regression tests for reviewed bypasses | Mostly closed | Tests now cover updated count/hash cases, duplicate relationship IDs, unsupported relationship types, nested relationship text, required hashes, missing readiness, and container malformations. | Missing targeted tests for source-limitation/manifest contradiction, nested manifest relationship-source copied text, and non-file `content_hashes` entries. |

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Existing MCP and HTTP E2E checks pass against the fixture package. | Yes | `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py` exited 0: 89 pytest tests passed, then `HTTP CLI E2E OK` and `MCP streamable HTTP E2E OK`. | None. |
| 2 | Package validation fails when manifest and normalized records disagree. | Yes | Manifest-to-record and record-to-manifest checks for laws/norms are implemented in `mcp/legal_texts/validation.py:457-484`; tests cover missing manifest-declared IDs and extra package IDs in `mcp/tests/test_generated_package.py:82-129`. | None for law/norm records. Source-limitation consistency remains a strictness finding below. |
| 3 | Package validation rejects unsupported or malformed citation units. | Yes | Supported generated units are enumerated at `mcp/legal_texts/validation.py:50`; unsupported units and malformed container unit/status combinations are rejected at `mcp/legal_texts/validation.py:216-225`; tests are at `mcp/tests/test_generated_package.py:300-370`. | None for Phase 2. |
| 4 | Package validation rejects relationship records with missing provenance, unsupported relationship types, duplicate relationship IDs, or targets that resolve to neither official records nor source limitations. | Yes | Relationship validation covers required fields, duplicate IDs, supported types, relationship source IDs, recursive copied-text field paths, provenance, endpoint kinds, and endpoint resolution in `mcp/legal_texts/validation.py:547-653`; tests are at `mcp/tests/test_generated_package.py:148-230`. | Manifest relationship-source metadata still has a copied-text loophole, but `relationships.json` records meet this criterion. |
| 5 | Existing `par` and `art` fixture behavior remains unchanged. | Yes | Existing resolver, MCP, HTTP, and E2E tests passed. `git diff` shows no changes to `mcp/tests/test_resolver.py`, `mcp/tests/test_http_api.py`, or `mcp/tests/test_mcp_tools.py`. | None. |
| 6 | The package format can represent source failures without adding fake law or norm records. | Partial | The generated fixture includes `source-limitations.json` for `lim-state-be-missing`, and relationship targets can resolve to that limitation without a fake law/norm. | The package limitation can contradict the manifest record while preserving the same `limitation_id`, so the representation is not yet strict enough to prevent false source-failure metadata. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Define generated package metadata and optional files. | Implemented package metadata, manifest, readiness, hashes, source limitations, relationships, counts, and fixtures. | Minor | Source-limitation package records are not fully reconciled with manifest records. |
| 2 | Add additive citation-unit validation. | Implemented generated units in model/validation while leaving resolver normalization unchanged. | No | Meets Phase 2 scope. |
| 3 | Validate manifest and normalized-record consistency. | Implemented bidirectional law/norm consistency and count checks. | Minor | Does not fully validate manifest/package consistency for source limitations. |
| 4 | Add relationship record schema validation. | Implemented relationship record schema, target resolution, duplicate/type checks, provenance, source reconciliation, and recursive copied-text checks. | Minor | Manifest relationship-source metadata still uses only shallow copied-text checks. |
| 5 | Preserve runtime and transport behavior. | Achieved; release gate and E2E passed. | No | Meets Phase 2 scope. |
| 6 | Document generated package schemas. | Docs updated for generated package, source provenance, MCP module, and overview. | Partial | Docs still overstate source-limitation and relationship-source copied-text guarantees relative to validation. |

## Code Quality Assessment

### Findings

- **Major**: `source-limitations.json` is reconciled with manifest `source_limitations` only by `limitation_id`, so a package can contradict manifest source-failure metadata and still validate. Evidence: `_validate_source_limitations_match_manifest` accepts any package limitation whose ID appears in the manifest at `mcp/legal_texts/validation.py:493-517`, without comparing `source_family`, `source_id`, `terminal_state`, `source_url`, or timestamp fields. A manual mutation changed the fixture package limitation `source_id` and URLs from `state-law:be/missing` to `state-law:be/other`, updated `source-limitations.json` in `content_hashes`, and `validate_generated_package` returned `[]`.
- **Major**: recursive copied/editorial text rejection is applied to `relationships.json`, but not to manifest `relationship_sources`, even though those records are relationship-source metadata inside the generated package. Evidence: `_validate_relationships` calls `_find_forbidden_field_paths` at `mcp/legal_texts/validation.py:579-581`; `validate_corpus_manifest` only checks top-level copied-text field names for third-party scope records at `mcp/legal_texts/manifest.py:290-310`. A manual mutation added `source_metadata.editorial_text` to the fixture manifest relationship source, updated the manifest hash, and `validate_generated_package` returned `[]`.
- **Minor**: malformed `content_hashes` entries can raise an unhandled filesystem exception instead of producing a validation error. Evidence: `_validate_package_hashes` calls `file_path.read_bytes()` without first requiring `file_path.is_file()` at `mcp/legal_texts/validation.py:352-360`. A manual mutation adding `"."` to `content_hashes` raised `IsADirectoryError` instead of returning an invalid-readiness error.

## Testing Assessment

### Verify Command Result

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: Passed: 89 pytest tests, `HTTP CLI E2E OK`, and `MCP streamable HTTP E2E OK`.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `test_generated_package_rejects_extra_law_not_declared_by_imported_manifest_source` / `test_generated_package_rejects_extra_norm_not_declared_by_imported_manifest_source` | Reverse law/norm manifest consistency with counts and hashes updated. | Yes | Good regression coverage for the first review's main law/norm bypass. |
| Hash/readiness tests at `mcp/tests/test_generated_package.py:244-298` | Hash mismatch, self-hash exclusion, empty hash coverage, optional-file hashes, and missing readiness. | Yes | Missing non-file hash path coverage. |
| Relationship tests at `mcp/tests/test_generated_package.py:148-230` | Missing provenance, unresolved target, unsupported target kind, duplicate IDs, unsupported type, nested copied text, and relationship-source mismatch. | Yes | Missing manifest `relationship_sources` nested copied-text coverage. |
| Citation-unit tests at `mcp/tests/test_generated_package.py:300-370` | Generated units and container status/text malformations. | Yes | Adequate for Phase 2; resolver support for new units is deferred. |
| Source-limitation tests at `mcp/tests/test_generated_package.py:132-145` | Package limitation with a new ID/source not declared by the manifest is rejected. | Partial | Does not cover same-ID contradictions against the manifest record. |

### Real-World Testing

Performed: the release gate ran real local HTTP and MCP streamable-HTTP E2E checks against the fixture package. External live source probes were skipped with `SKIP_LIVE_SOURCE_MATRIX=true`, which is acceptable for Phase 2 because bulk corpus generation and network-heavy corpus gates are deferred.

## Scope Compliance

### Findings

- The implementation stays within Phase 2 runtime scope. It does not add Phase 11 relationship lookup APIs and does not require resolver support for `recital`, `chapter`, `section`, `annex`, or generated `container` units.
- Generated fixtures remain small and committable; no full production corpus is required or introduced.

## Regression Risk

### Test Integrity Check

- [x] No existing tests were deleted.
- [x] No existing tests were disabled.
- [x] No existing assertions were weakened.
- [x] All pre-existing tests still pass in the release gate run.

### Findings

- Current `par`/`art` resolver, MCP, HTTP, and search behavior has low regression risk after this phase; the release gate exercises those paths.
- Generated-package provenance has higher residual risk until source-limitation records are compared against manifest records and recursive copied-text checks cover manifest relationship sources.

## Documentation & Cleanup

### Findings

- **Major**: `docs/features/source-provenance.md:65-67` says relationship-source metadata must not copy editorial text into the generated package, but manifest `relationship_sources` can still carry nested copied/editorial text.
- **Major**: `docs/features/source-provenance.md:71-77` describes `source-limitations.json` as source-level failure evidence, but validation allows the package file to contradict the manifest source limitation and even claim `terminal_state="imported"` while retaining the manifest limitation ID.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Source limitations | Package source-limitation records can contradict manifest `source_limitations` when they reuse an existing `limitation_id`. | Compare package and manifest limitation records by ID/source key and reject mismatched `source_family`, `source_id`, `terminal_state`, source URL, and key provenance fields; consider rejecting `terminal_state="imported"` in `source-limitations.json`. |
| 2 | Major | Relationship provenance | Manifest `relationship_sources` can include nested copied/editorial text fields even though `relationships.json` now rejects them recursively. | Reuse the recursive forbidden-field check in `validate_corpus_manifest` for third-party scope records, especially `relationship_sources` and nested `source_metadata`. |
| 3 | Minor | Hash validation | `content_hashes` entries that resolve to directories raise `IsADirectoryError` instead of returning structured validation errors. | Require hash targets to be package-relative files before reading bytes and add a regression test. |

## Recommendations

1. Block acceptance until the two Major strictness gaps are closed and covered by negative tests.
2. Add focused tests for same-ID source-limitation contradictions, package source limitations claiming `imported`, nested copied text in manifest `relationship_sources`, and non-file `content_hashes` targets.
3. Re-run `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py` after the fixes.
