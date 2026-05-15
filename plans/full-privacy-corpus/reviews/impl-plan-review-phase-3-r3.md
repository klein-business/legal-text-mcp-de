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

**Verdict**: Ready

The r2 blocker has been addressed: the implementation plan now includes an explicit documentation step for complete GII coverage measurement and a docs-oriented verification expectation. The plan is concrete enough to execute after Phase 1 and Phase 2 prerequisites land, and its discovery-only boundary avoids claiming terminal import coverage before Phase 4.

## Scope Alignment

### Findings

- No scope-alignment findings. The plan covers GII TOC fetch/parse, one discovery manifest source record per TOC item, discovery count metadata, TOC and malformed-payload failure handling, representative fixture tests, an opt-in live discovery gate with persisted output, and documentation of coverage measurement. It does not expand into XML ZIP normalization, runtime corpus exposure, or relationship graph work.

## Technical Feasibility

### Findings

- No technical-feasibility findings. Current baseline anchors support the approach: `mcp/legal_texts/importer.py` provides `default_fetch`, `utc_now`, and `sha256_bytes`; `mcp/legal_texts/sources.py` contains the curated `GERMAN_SOURCES`/`SOURCE_SPECS` aliases to preserve as metadata; `scripts/verify_release.py` exposes the release-gate test selection that should not include the network-heavy live script by default; and the docs targets exist. The plan correctly labels `mcp/legal_texts/manifest.py`, generated-package helpers, and `mcp/tests/test_generated_package.py` as Phase 1/2 prerequisite outputs rather than current baseline files.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Add a GII TOC parser | Yes | Yes | None. URL normalization, stable `source_path`/`source_id`, original-link preservation, alias metadata, duplicate handling, and namespace tolerance are specified. |
| 2 | Add discovery manifest generation | Yes | Yes | None. Fetch behavior, TOC-level limitation artifacts, malformed item diagnostics, and discovery-mode validation are specified without downloading every `xml.zip`. |
| 3 | Write discovery metadata compatible with generated packages | Yes | Yes | None. Artifact schema, count/hash/timestamp/parser-version metadata, duplicate/malformed diagnostics, and strict generated-package validation are specified. |
| 4 | Add fixture tests and live discovery gate | Yes | Yes | None. Unit coverage includes success, non-200, exception, malformed XML/item, duplicate paths, artifact writing, and generated-package validation; the live script remains opt-in. |
| 5 | Document complete GII coverage measurement | Yes | Yes | None. The prior missing documentation deliverable is now assigned to concrete docs files with specific fields and boundaries to document. |

## Required Context Assessment

### Missing Context

- None.

### Unnecessary Context

- None.

## Testing Plan Assessment

### Test Integrity Check

The plan identifies affected existing tests, protects `mcp/tests/test_source_import.py` and `mcp/tests/test_source_matrix.py` from being weakened, and states that the live discovery script must not make ordinary PR verification network-heavy. That is adequate for test integrity.

### Test Gaps

- None. The primary verify command covers the new discovery tests, manifest/generated-package prerequisite tests, source-import regression tests, and the release gate. The opt-in live verification command explicitly exercises real GII TOC discovery and writes a persisted artifact.

### Real-World Testing

Real-world testing is planned through `PYTHONPATH=mcp uv run --group dev python scripts/verify_gii_discovery.py --output .artifacts/gii-discovery/latest.json`. Keeping this outside `scripts/verify_release.py` by default matches the plan-level non-functional requirement that network-heavy checks be explicit or scheduled rather than ordinary PR gates.

## Reality Check Validation

### Findings

- No reality-check findings. The implementation plan examined the relevant live baseline anchors and honestly records that Phase 1/2 outputs are prerequisites, not current files. Its observed TOC-shape note is consistent with the parser assumptions while still requiring namespace and extra-field tolerance.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| - | - | - | No findings. | Proceed when Phase 1 and Phase 2 prerequisites are complete. |

## Recommendations

1. Proceed with Phase 3 implementation after confirming Phase 1 manifest validation and Phase 2 generated-package validation are available in the workspace.
