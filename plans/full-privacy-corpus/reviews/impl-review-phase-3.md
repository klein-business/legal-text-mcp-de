---
type: review
entity: implementation-review
plan: "full-privacy-corpus"
phase: 3
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Review: Phase 3 - Complete GII discovery coverage

> Reviewing implementation of [Phase 3](../phases/phase-3.md)
> Against [Implementation Plan](../implementation/phase-3-impl.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Rework

The implementation adds the expected discovery-only module, fixture tests, opt-in script, and docs, and it does not import `xml.zip` payloads or claim terminal import coverage. However, the live artifact path can still pass with malformed TOC items, the artifact/count shape does not fully match the Phase 3 contract, and TOC failure records omit required limitation fields. These are Phase 3 discovery-gate issues, not deferred Phase 4 import-state requirements.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Every TOC item in the fixture TOC has exactly one manifest record. | Partial | Valid fixture coverage builds three discovered records and puts the same list into `manifest["discovered_sources"]` in `mcp/tests/test_gii_toc_discovery.py:29-63`; records are created in `mcp/legal_texts/gii_toc.py:197-223`. | The artifact does not expose a numeric `discovered_gii_items` count, and malformed item artifacts can omit an item while still returning no validation errors. |
| 2 | Discovery does not rely on the old hand-maintained `GERMAN_SOURCES` list. | Yes | `parse_gii_toc` iterates TOC XML items in `mcp/legal_texts/gii_toc.py:41-86`; `SOURCE_SPECS` is used only for alias candidates in `mcp/legal_texts/gii_toc.py:378-388`. | None. |
| 3 | Live discovery can report the current TOC item count without importing all payloads. | Partial | `scripts/verify_gii_discovery.py:18-27` fetches only the TOC and prints `len(artifact["discovered_gii_items"])`; no `xml.zip` fetch loop exists in `mcp/legal_texts/gii_toc.py`. | The persisted artifact stores `discovered_gii_items` as a list, not a count field, and malformed items do not fail the script because it checks only `toc_limitation` and `validation_errors`. |
| 4 | A live or recorded live-gate artifact proves the fetched TOC count used by the import run. | Partial | `write_gii_discovery_artifact` writes an explicit JSON output path in `mcp/legal_texts/gii_toc.py:182-184`; the script requires `--output` in `scripts/verify_gii_discovery.py:11-15`. | No reviewed artifact contains a first-class fetched count, normalized source-path count, duplicate count, or validated limitation shape. No live artifact was supplied in the implementation digest. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Add namespace-tolerant GII TOC parser with deterministic source paths, URLs, metadata, aliases, and duplicate errors. | Implemented parser, URL normalization, aliases, duplicate diagnostics, and namespace-tolerant local-name checks in `mcp/legal_texts/gii_toc.py`. | Partial | Original link and unknown TOC metadata are not preserved as planned. |
| 2 | Add discovery manifest generation and TOC-level limitation artifacts. | Implemented discovery-mode manifest and fetch failure artifacts. | Partial | Malformed item diagnostics do not fail artifact validation, and TOC limitations omit required fields. |
| 3 | Write discovery metadata compatible with generated packages. | Artifact includes schema version, TOC hash/timestamp, parser version, embedded manifest, paths, malformed items, and validation errors. | Partial | Count metadata and generated-package-style validation are incomplete. |
| 4 | Add fixture tests and opt-in live discovery gate. | Added fixture tests, `scripts/verify_gii_discovery.py`, and release-gate fixture test inclusion. | Partial | Tests miss malformed-item artifact failure, successful mocked fetch path, and failure-artifact writing shape. |
| 5 | Document complete GII coverage measurement. | Docs describe GII TOC discovery, fixture-vs-live behavior, opt-in gate, and discovery-only coverage. | No | Docs correctly avoid Phase 4 terminal import claims. |

## Code Quality Assessment

### Findings

- Major: Non-empty `malformed_items` is not treated as artifact validation failure. `build_gii_discovery_artifact` copies parser validation errors and manifest errors only in `mcp/legal_texts/gii_toc.py:107-129`; `scripts/verify_gii_discovery.py:22-25` fails only on `toc_limitation` or `validation_errors`. A probe against `malformed_item_toc.xml` produced one malformed item, `validation_errors=[]`, and `toc_limitation=None`, so a malformed TOC item would be silently accepted by the live gate.
- Major: TOC-level limitation records do not satisfy the planned failure shape. `_toc_limitation` emits only `source_family`, `source_id`, `terminal_state`, `source_url`, `retrieved_at`, `reason`, plus optional status/error/parser fields in `mcp/legal_texts/gii_toc.py:310-334`, but the implementation plan requires `limitation_id` and `details` at `plans/full-privacy-corpus/implementation/phase-3-impl.md:56`, and docs describe the same source-limitation fields at `docs/features/source-provenance.md:88-93`.
- Major: The discovery artifact does not expose the planned count metadata. The phase requires discovery count reporting and tests proving `discovered_gii_items` equals the fixture TOC item count in `plans/full-privacy-corpus/phases/phase-3.md:25-30` and `plans/full-privacy-corpus/phases/phase-3.md:45-48`; the implementation stores `discovered_gii_items` as a list in `mcp/legal_texts/gii_toc.py:272-284` and omits a manifest summary count, normalized source-path count, and duplicate count.
- Minor: `source_metadata.original_link` does not preserve the original TOC URL. `_discovered_source_record` overwrites `xml_zip_url` with the normalized HTTPS URL before assigning `source_metadata["original_link"]` in `mcp/legal_texts/gii_toc.py:204-220`, contrary to `plans/full-privacy-corpus/implementation/phase-3-impl.md:48`.

## Testing Assessment

### Verify Command Result

- **Command**: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_gii_toc_discovery.py mcp/tests/test_corpus_manifest.py mcp/tests/test_generated_package.py`
- **Exit Code**: 0
- **Result**: Passed: 55 tests.

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: Passed: 107 pytest tests, `HTTP CLI E2E OK`, and `MCP streamable HTTP E2E OK`.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `test_parse_valid_gii_toc_builds_discovery_manifest_records` | Happy-path fixture parsing, URL normalization, aliases, embedded manifest validation. | Yes | Does not assert a numeric `discovered_gii_items` count or mocked fetch success. |
| `test_parse_gii_toc_reports_duplicate_source_paths_as_validation_errors` | Duplicate normalized path produces validation errors. | Yes | Good coverage for duplicate detection. |
| `test_parse_gii_toc_reports_malformed_xml_as_toc_limitation` | Malformed XML creates a parse-failed TOC limitation. | Partial | Does not assert required limitation fields such as `limitation_id` and `details`. |
| `test_parse_gii_toc_reports_malformed_items_without_silently_dropping` | Parser reports malformed items. | Partial | It exercises `parse_gii_toc` only; it does not prove `build_gii_discovery_artifact` or the live script fail when malformed items exist. |
| Non-200 and exception tests | Fetch failures produce `source_unavailable` artifacts. | Partial | They check status/error code but not full failure schema or artifact writing. |
| `test_write_gii_discovery_artifact_writes_stable_json` | Success artifact writes stable JSON. | Yes | Does not cover failure artifact writing. |

### Real-World Testing

Not performed in this review. The release gate performs real local HTTP and MCP streamable-HTTP E2E checks, but external live GII discovery was not run because the user requested that the review write only `plans/full-privacy-corpus/reviews/impl-review-phase-3.md`. No persisted live discovery artifact was supplied in the implementation digest.

## Scope Compliance

### Findings

No out-of-scope bulk import behavior found. The implementation fetches and parses the TOC only, does not download every `xml.zip`, does not assign Phase 4 terminal import states to every discovered source, and the reviewed docs state that discovery metadata measures catalog coverage only in `docs/features/law-loading-and-indexing.md:78-82`.

## Regression Risk

### Test Integrity Check

- [x] No existing tests were deleted in the reviewed status output.
- [x] No existing tests were disabled; `rg` found no `pytest.mark.skip`, `pytest.mark.xfail`, `skip()`, or `xfail()` usage under `mcp/tests`, `scripts`, or `mcp`.
- [x] No existing assertions were identified as weakened in the reviewed files.
- [x] All pre-existing release-gate tests still pass in the reviewed command.

### Findings

Regression risk to existing runtime behavior is low because the new code path is opt-in and fixture-backed release verification passes. The main risk is downstream corpus-gate reliability: a malformed TOC item or under-specified failure artifact can be accepted as successful discovery evidence.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Artifact validation | Malformed TOC items are recorded but do not make the artifact or live script fail. | Add a validation error or explicit failure condition for non-empty `malformed_items`, and cover it through `build_gii_discovery_artifact` and script-level tests. |
| 2 | Major | Failure artifact shape | `toc_limitation` records omit required limitation fields and are not validated against the planned source-limitation shape. | Add `limitation_id`, `details`, and terminal-state-specific fields such as `retryable` or diagnostic text, then validate and test both non-200 and parse-failed artifacts. |
| 3 | Major | Count metadata | The artifact stores `discovered_gii_items` as a record list and omits first-class count metadata required for live count evidence. | Add explicit count fields, at minimum `discovered_gii_items` as the count or a clearly named `discovered_gii_item_count`, plus normalized source-path and duplicate counts; keep records under a separate key or document the compatibility choice. |
| 4 | Minor | Provenance metadata | `source_metadata.original_link` is normalized instead of preserving the original TOC link. | Preserve the raw TOC link before normalization and add tests for HTTP and relative links. |

## Recommendations

1. Block acceptance until the three Major artifact/validation issues are fixed.
2. Keep the Phase 3 scope discovery-only; do not add Phase 4 bulk normalization or terminal import-state work while addressing these findings.
3. After rework, rerun the focused discovery/package tests and the release gate, then produce or supply an opt-in live discovery artifact as external evidence if Phase 3 acceptance is being closed.
