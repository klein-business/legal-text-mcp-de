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

The revised implementation plan resolves the prior substantive gaps around GII TOC link normalization, duplicate handling, TOC failure artifacts, script artifact schema, and prerequisite-created Phase 1/2 anchors. The remaining issue is narrower but still phase-relevant: Phase 3 explicitly requires documentation of complete GII coverage measurement, yet the implementation steps do not assign or verify the docs update.

## Scope Alignment

### Findings

- **Major**: Phase 3 includes "Documentation of complete GII coverage measurement" as a deliverable, and the implementation plan lists `docs/features/source-provenance.md` and `docs/features/law-loading-and-indexing.md` as context to extend. However, no implementation step actually updates those docs or defines the expected documentation content for `discovered_gii_items`, the live artifact, fixture-vs-live discovery, or the opt-in nature of the live gate.

## Technical Feasibility

### Findings

- The revised parser, discovery artifact, validation, and opt-in live-gate approach is technically feasible against the current code anchors and planned Phase 1/2 prerequisites. Current baseline helpers `default_fetch`, `utc_now`, and `sha256_bytes` exist in `mcp/legal_texts/importer.py`; `GERMAN_SOURCES` and `SOURCE_SPECS` exist in `mcp/legal_texts/sources.py`; `scripts/verify_release.py` has `selected_tests()` and can keep `verify_gii_discovery.py` out of the default release gate.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Add a GII TOC parser | Yes | Yes | Normalization, URL preservation, alias candidates, namespace tolerance, and duplicate failure behavior are specified. |
| 2 | Add discovery manifest generation | Yes | Yes | Fetch, TOC-level limitation shape, malformed item diagnostics, and discovery-mode manifest validation are specified. |
| 3 | Write discovery metadata compatible with generated packages | Yes | Yes | Artifact schema and generated-package validation expectation are specified, assuming Phase 2 prerequisite helpers exist. |
| 4 | Add fixture tests and live discovery gate | Yes | Yes | Fixture tests, mocked script artifact coverage, failure branches, and opt-in live command are specified. |
| Missing | Documentation update | No | No | Phase 3 documentation deliverable is implied by context and rollback, but no step assigns it. |

## Required Context Assessment

### Missing Context

- No additional code context is required for the implementation mechanics. The docs files already listed are the right targets, but the plan needs an explicit implementation step for updating them.

### Unnecessary Context

- None.

## Testing Plan Assessment

### Test Integrity Check

The plan identifies affected existing tests, protects `mcp/tests/test_source_import.py` and `mcp/tests/test_source_matrix.py` from weakening, and keeps the live discovery script opt-in. That is adequate for test integrity.

### Test Gaps

- **Major**: The primary verify command exercises parser, manifest, generated-package, and source-import tests, but the plan has no test or verification step for the required documentation update. At minimum, the documentation step should be included and verified by the repo's existing active workflow/docs checks or another explicit docs validation command.

### Real-World Testing

Real-world testing is planned through `PYTHONPATH=mcp uv run --group dev python scripts/verify_gii_discovery.py --output .artifacts/gii-discovery/latest.json`, and ordinary PR verification remains fixture-backed. This satisfies the phase's explicit-or-scheduled live discovery gate requirement.

## Reality Check Validation

### Findings

- The Reality Check now correctly separates Phase 1/2 prerequisite outputs from current baseline files and records the observed live TOC shape. A live sample fetched on 2026-05-15 confirms `<item>` entries with `<title>` and direct `<link>` values ending in `/xml.zip`, matching the parser assumptions.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Scope Alignment | The required documentation deliverable is not represented in any implementation step or verification path. | Add a docs step covering `docs/features/source-provenance.md` and `docs/features/law-loading-and-indexing.md`, and verify it through the existing docs/release checks or another explicit command. |

## Recommendations

1. Add a documentation step that updates the coverage-measurement and package-metadata docs with `discovered_gii_items`, TOC hash/timestamp, live artifact location/schema, fixture-vs-live behavior, and the fact that the live gate is opt-in.
2. Include a verification path for the docs update, preferably by running the existing release/docs checks in addition to the focused pytest command or documenting why the focused command is sufficient for Phase 3.
