---
type: review
entity: implementation-plan-review
plan: "full-privacy-corpus"
phase: 3
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 3 - Complete GII discovery coverage

> Reviewing [Phase 3 Implementation Plan](../implementation/phase-3-impl.md)
> Against [Phase 3 Scope](../phases/phase-3.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The implementation plan is directionally aligned with Phase 3 and correctly keeps the work discovery-only, but it leaves important execution details to the implementer. In particular, canonical source ID derivation from TOC links, malformed/unreachable TOC artifact behavior, and live-gate artifact validation are not concrete enough for a phase whose output becomes Phase 4's source of truth.

## Scope Alignment

### Findings

- **Major**: Phase 3 requires "manifest records for every discovered `<item>` and official `xml.zip` link" plus a live or recorded artifact proving the fetched TOC count. The plan adds a script, but does not specify the artifact schema, where it is persisted, or how the generated package/import run ties back to that artifact.
- **Minor**: The approach says the phase must not "claim terminal import coverage," which is correct, but Step 2's "source limitation artifact for the TOC fetch" is not clearly scoped to TOC-level discovery failure rather than item-level terminal source states. That distinction matters because Phase 4 owns per-item terminal states.

## Technical Feasibility

### Findings

- **Major**: The plan does not define deterministic source ID derivation and duplicate handling for TOC items. Current code has curated IDs in `mcp/legal_texts/sources.py` (`GERMAN_SOURCES`, `SOURCE_SPECS`), while the live TOC exposes links like `http://www.gesetze-im-internet.de/1-dm-goldm_nzg/xml.zip`. The implementer needs explicit rules for normalizing the link path to manifest `source_id`/`source_identifier`, canonicalizing `http` source links to the required source URL form if desired, preserving existing alias mappings for current GII laws, and failing on duplicate source paths.
- **Major**: Failure handling is under-specified. Phase 3 includes unreachable TOC and malformed TOC payload handling, but the plan only says to "emit a source limitation artifact" or reject/classify malformed entries. It does not define the record shape, required fields, or whether malformed individual items make the whole discovery invalid versus producing explicit item diagnostics.
- **Minor**: Step 3 points either to a Phase 2 package metadata helper in `mcp/legal_texts/validation.py` or a new writer in `mcp/legal_texts/gii_toc.py`. Because Phase 2 introduces the generated-package contract, this step should name the actual Phase 2 helper or file once Phase 2 exists, rather than leaving metadata placement open.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Add a GII TOC parser | Partial | Partial | File path and parser purpose are clear, but source path/source ID extraction and duplicate/canonicalization rules are not specified. |
| 2 | Add discovery manifest generation | Partial | Partial | Fetch and validation mode are clear; TOC failure and source-limitation artifact shape are not. |
| 3 | Write discovery metadata compatible with generated packages | Partial | Partial | Required fields are named, but the destination and exact package/manifest summary schema are left open. |
| 4 | Add fixture tests and live discovery gate | Yes | Partial | Test/script files are concrete, but the live artifact contract and script test coverage are missing. |

## Required Context Assessment

### Missing Context

- `mcp/legal_texts/validation.py` or the Phase 2 generated-package validator/writer actually produced by Phase 2: Step 3 depends on package metadata compatibility and should direct the implementer to the concrete validation entry point.
- `mcp/tests/test_generated_package.py` or equivalent Phase 2 generated-package tests: needed to avoid writing `discovered_gii_items` metadata in a shape that strict package validation rejects.
- `docs/features/law-loading-and-indexing.md`: useful context for where generated package files and metadata are documented, especially because Phase 3 adds discovery count reporting.

### Unnecessary Context

- `mcp/tests/test_source_matrix.py`: it is useful as regression context, but the plan already protects it through test integrity constraints. It is not necessary to execute the core GII TOC discovery work.

## Testing Plan Assessment

### Test Integrity Check

The plan identifies affected existing tests and explicitly says not to skip or weaken `mcp/tests/test_source_import.py` or redefine `mcp/tests/test_source_matrix.py` semantics. That is adequate for test integrity, assuming Phase 1's `mcp/tests/test_corpus_manifest.py` exists after prerequisites complete.

### Test Gaps

- **Major**: The testing plan does not test `scripts/verify_gii_discovery.py` itself. There should be a fixture or mocked-fetch test proving the script writes the persisted JSON artifact with `discovered_gii_items`, TOC URL, content hash, retrieval timestamp, parser version, and failure details.
- **Major**: No explicit test covers unreachable TOC behavior, even though Phase 3 scope includes failure handling for unreachable TOC payloads. `default_fetch` returns status/body for HTTP errors, so discovery needs a tested branch for non-200 status and source-limitation output.
- **Minor**: The primary verify command omits generated-package validation tests from Phase 2. If discovery metadata is written into package metadata, at least the relevant strict generated-package test should run with the new fixture.

### Real-World Testing

Real-world testing is planned only as an opt-in live script, which matches the phase's "explicit or scheduled" network-heavy requirement. The plan is not yet adequate because it does not define the command invocation, artifact path convention, persisted artifact schema, or a non-network test that verifies the script's artifact-writing behavior.

## Reference Consistency

### Findings

- **Minor**: The Reality Check lists `scripts/verify_release.py` `selected_tests()`, and the current file does have that function. However, `TESTS` currently includes `mcp/tests/test_source_matrix_live.py`, so the statement "network-heavy discovery should not be added to the default release gate" is a plan choice rather than a direct consequence of the current release gate. The implementation plan should be explicit that `verify_gii_discovery.py` remains outside `TESTS`.

## Reality Check Validation

### Findings

- **Minor**: The Reality Check accurately identifies the static `SOURCE_SPECS` limitation and the reusable fetch/hash helpers, but it does not mention the current absence of `mcp/legal_texts/manifest.py` and generated-package metadata helpers in the baseline repo. Since Phase 3 is blocked by Phases 1 and 2, that is not a blocker, but it should be called out as prerequisite-created code rather than current code.
- **Minor**: The Reality Check does not validate the live TOC field shape. A quick check of `https://www.gesetze-im-internet.de/gii-toc.xml` shows each sampled `<item>` currently has `<title>` and a direct `<link>` to an `xml.zip`, which supports Step 1; recording that fact would make the plan's parser assumptions clearer.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Technical Feasibility | Deterministic source ID/link normalization and duplicate handling are not specified. | Define exact rules for deriving source path, source ID, source URL, alias preservation, and duplicate failure from TOC `<link>` values. |
| 2 | Major | Technical Feasibility | TOC failure and malformed item behavior lacks a concrete artifact/schema. | Specify TOC-level source-limitation fields and item-level malformed-entry handling, then test both. |
| 3 | Major | Testing | Live discovery artifact behavior is not tested or specified enough. | Add a mocked-fetch test for `scripts/verify_gii_discovery.py` and document the artifact path/schema. |
| 4 | Minor | Step Quality | Generated metadata destination is left open between validation helpers and a new writer. | Name the Phase 2 helper/file once prerequisites exist and include the relevant generated-package validation test. |
| 5 | Minor | Reality Check | Prerequisite-created files and live TOC shape are not clearly separated from current-code anchors. | Update Reality Check notes to distinguish current repo state from Phase 1/2 outputs and record the observed TOC shape. |

## Recommendations

1. Revise Steps 1-3 to define exact TOC link normalization, manifest source ID fields, duplicate detection, and existing GII alias preservation.
2. Add a concrete live discovery artifact contract covering success and TOC failure cases, including persisted JSON fields and path/CLI conventions.
3. Expand tests to cover the live script with mocked fetch, unreachable TOC status, malformed XML, malformed item records, duplicate TOC links, and generated-package metadata validation.
4. Tighten the Reality Check to separate current code anchors from Phase 1/2 prerequisite outputs and include the observed live TOC structure.
