---
type: review
entity: implementation-plan-review
plan: "full-privacy-corpus"
phase: 10
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 10 - German state-law PDF adapters and source limitations

> Reviewing [Phase 10 Implementation Plan](../implementation/phase-10-impl.md)
> Against [Phase 10 Scope](../phases/phase-10.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The plan is directionally aligned with Phase 10: it avoids manual transcription, treats unsupported state-law sources as explicit limitations, and keeps runtime exposure deferred to Phase 11. It is not yet executable without interpretation because it does not identify the concrete Phase 8/9 outcome artifacts to merge, does not materialize Phase 10 limitations into the Phase 2 generated-package contract, and lacks real-world evidence requirements for PDF extraction or limitation decisions. Under the requested gate, this is not Ready because the review found nonzero findings.

## Scope Alignment

### Findings

- **Major**: Phase 10 must leave every German state imported or explicitly limited after Phases 9 and 10, and Phase 11 depends on final state-law coverage. The implementation plan defines an in-memory/helper contract for `state_law_coverage.v1`, but it does not specify the persisted package or manifest location where this coverage and the new limitation records are written.

## Technical Feasibility

### Findings

- **Major**: The plan says Step 1 merges "Phase 9 imported/limited outcomes" with the Phase 8 inventory, but the Phase 9 implementation plan does not define a concrete persisted outcome artifact or API that enumerates imported and limited machine-readable/HTML states. Without a named source of truth, an implementer has to infer Phase 9 outcomes from tests, adapter return values, generated package records, or limitation records.
- **Major**: The plan depends on generated-package validation in the testing table, but Required Context omits the Phase 2 generated-package contract that defines `source-limitations.json`, record counts, manifest consistency, and runtime-loadable optional files. This leaves Step 3 free to emit limitation records only in a coverage helper rather than in the package structures that Phase 11 will load.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Identify remaining Phase 8 states | Partial | Partial | Defines the desired 16-state coverage shape, but does not name the Phase 8 inventory data file or Phase 9 persisted outcome source to merge. |
| 2 | Implement PDF extraction only for approved cases | Yes | Mostly | The quality gate is concrete for fixture behavior, but the plan does not require real official-source evidence before approving import versus limitation. |
| 3 | Add source limitation records for unsupported states | Partial | Partial | Does not specify whether records are written to `source-limitations.json`, `manifest.json`/`source_limitations`, Phase 8 limitation data, or all required generated-package locations. |
| 4 | Add coverage summary and negative tests | Yes | Mostly | The test targets are appropriate, but the tests are not tied to a persisted coverage artifact that Phase 11 can consume. |

## Required Context Assessment

### Missing Context

- `plans/full-privacy-corpus/implementation/phase-2-impl.md` - Defines the generated-package files and `source-limitations.json` schema that Phase 10 must update for final imported-or-limited state outcomes.
- Planned Phase 8 inventory data, such as `mcp/legal_texts/data/state_law_sources.v1.json` and `mcp/legal_texts/data/state_law_limitations.v1.json` from Phase 8 - Needed as the concrete inventory input, not just the validation API.
- A concrete Phase 9 outcomes artifact or API - Needed as the source of truth for machine-readable/HTML states that Phase 10 must preserve while closing the remaining PDF/limitation states.

### Unnecessary Context

- None.

## Testing Plan Assessment

### Test Integrity Check

The plan includes one primary verify command and protects important behaviors: no manual transcription, no weakening of Phase 9 adapter tests, and explicit limitations for unsupported sources. It does not fully identify which package or manifest consistency tests prove that new Phase 10 limitations are loadable by Phase 11, because the concrete generated-package artifact is under-specified.

### Test Gaps

- **Major**: The testing plan is fixture-only and lacks an explicit real-world verification step for official PDF source stability, content hash capture, extraction method/version capture, and limitation decisions. Fixture tests can prove deterministic parser behavior, but they cannot prove that the selected official PDF or unstable source currently supports an imported state-law outcome or must be limited.
- **Major**: The primary verify command does not include generated-package or manifest validation tests by name, even though the testing table claims final state-law coverage validates against manifest/generated-package rules.

### Real-World Testing

Real-world testing is not planned. For Phase 10, that is a material gap because the import-versus-limitation decision depends on official source stability, fetchability, content hashing, and PDF extraction quality rather than only local representative fixtures.

## Reference Consistency

### Findings

- **Major**: Current repository anchors `mcp/legal_texts/manifest.py`, `mcp/legal_texts/state_law_inventory.py`, `mcp/legal_texts/state_law.py`, and `mcp/tests/test_state_law_adapters.py` do not exist in the workspace. This is acceptable only if Phase 10 is executed strictly after Phases 1, 8, and 9 land those files, but the Phase 10 plan should state the concrete prerequisite artifacts and update if prior implementation names differ.

## Reality Check Validation

### Findings

- **Minor**: The Reality Check correctly notes that there is no current PDF extraction code or dependency and that the phase may choose limitations instead of a PDF adapter. It does not acknowledge the current absence of the prerequisite state-law and manifest modules named in Required Context, so it understates the degree to which this plan depends on prior phases landing exact file and symbol names.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Scope / Persistence | Phase 10 defines `state_law_coverage.v1` but not the persisted manifest/package location for final 16-state coverage and new limitation records. | Specify the exact generated-package and/or manifest files that Phase 10 writes, including how `source-limitations.json`, `manifest.json`, package counts, and coverage summary stay consistent. |
| 2 | Major | Technical Feasibility | Step 1 relies on Phase 9 imported/limited outcomes without a named persisted artifact or API. | Require a concrete Phase 9 outcome source, such as validated generated-package records, a state-law adapter outcome summary, or a named helper that enumerates terminal states. |
| 3 | Major | Required Context | The plan omits the Phase 2 generated-package contract despite claiming generated-package validation and Phase 11 runtime loadability. | Add `plans/full-privacy-corpus/implementation/phase-2-impl.md` and the concrete package schema files/helpers to Required Context and Step 3. |
| 4 | Major | Testing / Evidence | No real-world verification step proves official PDF source stability, hash capture, extraction quality, or limitation decisions. | Add an opt-in command or explicit artifact requirement that fetches/probes remaining official state sources, records hashes and parser versions where fetchable, and persists import-or-limitation evidence outside default PR CI. |
| 5 | Major | Testing | The primary verify command does not run manifest/generated-package validation tests even though package validation is a stated expected outcome. | Include the generated-package/manifest validation test module or a focused validation command in the primary verify path. |
| 6 | Major | Reference Consistency | The current repo lacks several named Phase 10 prerequisite anchors (`manifest.py`, `state_law_inventory.py`, `state_law.py`, adapter tests). | State that Phase 10 must start with a prerequisite check against the actual symbols/files produced by Phases 1, 8, and 9, and revise the plan if names or contracts changed. |
| 7 | Minor | Reality Check | The Reality Check omits the current absence of the prerequisite state-law and manifest modules named in the plan. | Add this dependency reality to the Reality Check so execution does not silently rely on non-existent current anchors. |

## Recommendations

1. Revise Phase 10 to name the exact Phase 8 inventory data file and Phase 9 terminal-outcome source that determine the remaining states.
2. Define where Phase 10 writes final coverage and source limitations in the Phase 2 generated-package/manifest contract, and test package consistency directly.
3. Add a real-world verification command or persisted evidence artifact for remaining official state-law sources, especially any PDF import decision.
4. Add a prerequisite check that verifies the actual Phase 1/8/9 file and symbol names before implementation begins.
