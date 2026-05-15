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

The implementation preserves legacy MCP/HTTP behavior and adds a useful generated-package validation path, but strict validation is incomplete for the package contract that Phase 2 is meant to establish. In particular, manifest consistency is only checked one way, required package hashes/readiness can be omitted, and relationship metadata can still carry copied/editorial text in nested fields.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Existing MCP and HTTP E2E checks pass against the fixture package. | Yes | `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py` passed with 77 tests plus HTTP and MCP streamable-HTTP E2E. `scripts/verify_release.py` includes generated-package tests at lines 22-23 and E2E at lines 120-122. | None. |
| 2 | Package validation fails when manifest and normalized records disagree. | Partial | `_validate_manifest_record_references` checks imported manifest IDs resolve into `laws.json`/`norms.json` in `mcp/legal_texts/validation.py:436-455`; the test at `mcp/tests/test_generated_package.py:76-85` covers a manifest ID missing from `norms.json`. | Reverse disagreement is not checked. A generated package can add extra law/norm records absent from the manifest, update counts/hashes, and `validate_generated_package` returns `[]`. |
| 3 | Package validation rejects unsupported or malformed citation units. | Partial | `GENERATED_NORM_UNITS` and unit rejection are implemented in `mcp/legal_texts/validation.py:50` and `mcp/legal_texts/validation.py:215-217`; tests cover allowed units and an unsupported `clause` unit at `mcp/tests/test_generated_package.py:157-195`. | Malformed unit/status combinations still pass, for example `unit="container"` with `status="active"` and text. `NormUnit` remains `Literal["par", "art"]` in `mcp/legal_texts/models.py:8`, despite the Phase 2 plan naming `models.py` as part of the schema change. |
| 4 | Package validation rejects relationship records with missing provenance, unsupported relationship types, duplicate relationship IDs, or targets resolving to neither official records nor source limitations. | Partial | Relationship type, duplicate ID, provenance, and endpoint checks are present in `mcp/legal_texts/validation.py:484-557`; tests cover missing provenance, unresolved target, and unsupported `external_source` target at `mcp/tests/test_generated_package.py:88-121`. | Tests do not cover duplicate IDs or unsupported relationship types, and the schema does not tie relationship `source_id` or source-limitation targets back to manifest relationship/source-limitation records. Nested copied text in `metadata` also passes. |
| 5 | Existing `par` and `art` fixture behavior remains unchanged. | Yes | Existing resolver, HTTP, and MCP tests were retained and passed; `mcp/tests/test_resolver.py`, `mcp/tests/test_http_api.py`, and `mcp/tests/test_mcp_tools.py` all passed in the release gate. | None. |
| 6 | The package format can represent source failures without adding fake law or norm records. | Yes | Fixture `source-limitations.json` represents `lim-state-be-missing` without matching law/norm records, and relationships can target that limitation. Validation accepts the fixture and `NormalizedDataset.load` can load it in `mcp/tests/test_generated_package.py:50-56`. | Source limitations should be tightened so limitation records cannot claim `terminal_state="imported"`. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Define generated package metadata and optional files. | Implemented `package.json`, manifest, readiness, source limitations, relationships, counts, and declared hash checks. | Yes | The hash/readiness contract is weaker than planned because required file hashes are not required and declared readiness can be absent. |
| 2 | Add additive citation-unit validation. | Added generated units to validation and tests. | Yes | `models.py` `NormUnit` was not updated, and malformed unit/status combinations are not rejected. |
| 3 | Validate manifest and normalized-record consistency. | Implemented manifest-to-record ID resolution and count checks. | Yes | Reverse record-to-manifest consistency is missing. |
| 4 | Add relationship record schema validation. | Implemented supported types, duplicate ID detection, provenance, endpoint kinds, and target resolution. | Yes | Source IDs are not reconciled with manifest relationship sources, and copied text checks are shallow. |
| 5 | Preserve runtime and transport behavior. | Achieved. Legacy fixtures still load and E2E passes. | No | Good. |
| 6 | Document generated package schemas. | Docs were updated in law loading, source provenance, MCP module, and overview docs. | Partial | Documentation is directionally correct but overstates strictness for hashes/readiness and copied-text rejection. |

## Code Quality Assessment

### Findings

- **Major**: Manifest/package consistency is incomplete. `mcp/legal_texts/validation.py:436-455` only ensures manifest-imported IDs exist in normalized records. It does not ensure every normalized law/norm is represented by an imported manifest source, nor that package source limitations/relationship sources are backed by the manifest. Manual probe: adding an extra law/norm absent from `manifest.json`, while updating counts and hashes, returned `[]` from `validate_generated_package`.
- **Major**: Hash and readiness validation are opt-in despite being part of the strict generated-package contract. `_validate_package_hashes` in `mcp/legal_texts/validation.py:320-342` only validates entries present in `content_hashes`; `readiness_path` is only loaded if the file exists at `mcp/legal_texts/validation.py:155-159`. Manual probes showed `content_hashes={}` passes, and a missing `readiness.json` passes when its hash entry is removed.
- **Major**: Relationship copied/editorial text rejection is shallow. `mcp/legal_texts/validation.py:511-513` checks only top-level relationship keys, so `metadata.third_party_text` or similar nested payloads pass. This conflicts with the plan requirement at `plans/full-privacy-corpus/implementation/phase-2-impl.md:79-80` and the docs at `docs/features/source-provenance.md:79-86`.
- **Minor**: Citation-unit schema support is split between validation and stale model typing. `NormUnit` remains `Literal["par", "art"]` in `mcp/legal_texts/models.py:8`, and `unit="container"` with `status="active"` still validates if text is present. This does not break current JSON loading, but it leaves the internal schema contract inconsistent for future generated writers.

## Testing Assessment

### Verify Command Result

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: Passed. Pytest reported 77 passed, followed by `HTTP CLI E2E OK` and `MCP streamable HTTP E2E OK`.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `test_valid_generated_package_passes_strict_validation_and_loads` | Positive fixture validation plus `NormalizedDataset` load. | Yes | Good runtime compatibility check. |
| `test_generated_package_rejects_manifest_record_mismatch` | Manifest references a norm missing from `norms.json`. | Yes | Only covers one direction of manifest disagreement. |
| Relationship negative tests | Missing provenance, unresolved source-limitation target, unsupported `external_source`. | Yes | Missing duplicate relationship ID, unsupported relationship type, invalid relationship source ID, nested copied text, and arbitrary source limitation target coverage. |
| Hash/readiness tests | Hash mismatch, self-hash exclusion, malformed readiness when file exists. | Partial | Missing tests for required content hash entries, empty `content_hashes`, and missing declared readiness file. |
| Citation-unit tests | Allowed additive units and unsupported unit. | Partial | Missing malformed unit/status combinations and model type alias coverage. |

### Real-World Testing

Performed fixture-backed real local HTTP and MCP E2E through `scripts/verify_release.py`. Live external source probes were intentionally skipped with `SKIP_LIVE_SOURCE_MATRIX=true`; that is acceptable for Phase 2 because bulk corpus generation and network-heavy gates are out of scope. No full generated production package was tested, and the current strictness gaps mean a production-like package could pass validation while omitting provenance/hash evidence.

## Scope Compliance

### Findings

- The implementation stayed within Phase 2 runtime scope: no Phase 11 relationship lookup APIs were added, and existing MCP tool registry assertions remain authoritative.
- The generated fixture is small and committable, which fits Phase 2.
- The validation additions are closely scoped to `validation.py`; however, the contract is stricter in documentation than in code for hashes, readiness, manifest reverse consistency, and nested relationship text.

## Regression Risk

### Test Integrity Check

- [x] No existing tests were deleted.
- [x] No existing tests were disabled.
- [x] No existing assertions were weakened.
- [x] All pre-existing tests still pass in the release gate run.

### Findings

- Low regression risk for current `par`/`art` fixtures and transports; those paths passed unchanged.
- Higher future-risk for generated packages because weak validation can let incomplete provenance, missing hash evidence, and unmanifested normalized records reach runtime as "ready."

## Documentation & Cleanup

### Findings

- **Minor**: Documentation says generated packages keep `readiness.json` and `search-index.json` and fail when hashes/source limitations/relationship targets are malformed (`docs/features/law-loading-and-indexing.md:53-83`). The current validator does not require readiness existence and does not require hashes for package files, so docs overstate actual strictness.
- **Minor**: Documentation says relationship records must not copy third-party editorial text (`docs/features/source-provenance.md:79-86`), but the implementation only checks top-level fields.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Manifest consistency | Extra normalized laws/norms can be added outside `manifest.json` and still validate when counts/hashes are updated. | Add reverse checks from normalized records to imported manifest generated IDs, and reconcile package source limitations/relationship sources with manifest records. |
| 2 | Major | Package hashes/readiness | `content_hashes={}` and missing declared `readiness.json` can pass strict generated-package validation. | Require hashes for all required package files and all present optional package files; require `readiness_path` to exist and validate when declared. |
| 3 | Major | Relationship schema | Copied/editorial text can be nested under `metadata` and pass validation. | Recursively reject forbidden copied-text field names in relationship records, or constrain `metadata` to an explicit metadata-only schema. |
| 4 | Minor | Citation schema | `NormUnit` remains `par`/`art` only, and malformed `container` unit/status combinations pass. | Update the model/type alias and add validation/tests for unit/status combinations that are expected to be invalid. |
| 5 | Minor | Test coverage | Negative tests miss the validation bypasses above plus duplicate IDs and unsupported relationship types. | Add regression tests that mutate fixture packages while updating hashes/counts so failures prove the intended validation rule. |

## Recommendations

1. Block acceptance until the three Major validation gaps are closed and covered by negative tests.
2. Add focused tests for reverse manifest consistency, required hash entries, missing declared readiness, nested copied text, duplicate relationship IDs, unsupported relationship types, invalid relationship source IDs, and imported source limitations.
3. Align `models.py` and documentation with the final generated citation-unit/readiness/hash contract before re-review.
