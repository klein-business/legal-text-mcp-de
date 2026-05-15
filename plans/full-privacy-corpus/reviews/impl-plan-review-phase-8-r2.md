---
type: review
entity: implementation-plan-review
plan: "full-privacy-corpus"
phase: 8
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 8 - German state-law source family inventory

> Reviewing [Phase 8 Implementation Plan](../implementation/phase-8-impl.md)
> Against [Phase 8 Scope](../phases/phase-8.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The revised plan resolves the prior source-limitation and state-law ID-contract gaps, and it is technically aligned with the current codebase plus the Phase 1 prerequisite. It is not Ready under the requested zero-finding rule because the reachability evidence gate still permits Phase 8 completion without a current persisted or externally archived reachability artifact.

Finding counts: Critical 0, Major 1, Minor 0, Note 0.

## Scope Alignment

### Findings

- Phase 8 scope explicitly includes reachability and stability checks for machine-readable, stable HTML, and PDF sources. The implementation plan now defines a concrete reachability command and artifact schema, but its acceptance evidence clause still allows "an explicit decision that the run is scheduled" as an alternative to a current persisted or externally archived artifact. A scheduled future run does not satisfy the phase's inventory/evidence purpose before Phase 9/10 parser work depends on the classifications.

## Technical Feasibility

### Findings

- The proposed `mcp/legal_texts/state_law_inventory.py` module and JSON inventory fit the current repository structure. Current `mcp/legal_texts/sources.py` only contains static GII/EUR-Lex source specs, and current `mcp/legal_texts/validation.py` validates normalized law/norm source metadata rather than inventory outcomes.
- The plan correctly depends on Phase 1 for `mcp/legal_texts/manifest.py` and Phase 1-compatible source limitation validation. That file is not present in the current codebase, but Phase 8 is explicitly blocked by Phase 1, so this is a valid prerequisite rather than an implementation-plan defect.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Add state-law inventory schema | Yes | Yes | None. The fixed 16-state set, adapter classes, limitation references, and `derive_state_law_id` contract are concrete. |
| 2 | Add committed inventory data | Yes | Yes | None. The plan now defines a limitation artifact or embedded section and requires dangling/incomplete limitation references to fail validation. |
| 3 | Add reachability and stability check hooks | Yes | Partly | The command and artifact schema are concrete, but the completion evidence permits a scheduled future run instead of requiring current persisted or externally archived evidence. |
| 4 | Add validation tests and docs note | Yes | Yes | None. The tests cover 16 outcomes, ID validation, adapter classes, provenance, and limitation references without implementing parsers. |

## Required Context Assessment

### Missing Context

- None requiring revision. The plan lists the Phase 8 scope, Phase 1 manifest plan, current source/validation anchors, and provenance docs needed for an implementer.

### Unnecessary Context

- None.

## Testing Plan Assessment

### Test Integrity Check

The plan identifies the affected tests, keeps state-law records out of `mcp/tests/fixtures/normalized/`, preserves source limitation validation, and keeps live reachability outside the default release gate. It does not propose disabling or weakening existing tests.

### Test Gaps

- The testing plan includes a Gate row for the reachability artifact, but the implementation steps still allow completion via a scheduled future run rather than requiring the artifact or an externally archived equivalent to exist before Phase 8 is closed.

### Real-World Testing

Real-world testing is planned through an opt-in `scripts/verify_state_law_inventory.py` command that records status/content type/hash for non-`limitation_only` sources. The remaining gap is not the command itself; it is the acceptance rule that allows no current artifact when the run is merely scheduled.

## Reality Check Validation

### Findings

- The Reality Check is accurate: current runtime/docs have no state-law source family, `mcp/legal_texts/sources.py` covers only existing GII and DSGVO sources, and Phase 8 should not claim parser/runtime support.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Testing / Evidence | The plan's Phase 8 completion evidence allows a scheduled future reachability run. Because Phase 8 includes reachability/stability checks and later state-law adapter phases depend on the resulting classifications, a future scheduled run can let the phase close without current official-source availability evidence. | Require Phase 8 completion to include either a current `.artifacts/state-law/inventory-reachability.json` produced by the documented command or a current externally archived equivalent with path/hash recorded in the handover. Do not allow "scheduled" alone to satisfy completion. |

## Recommendations

1. Tighten Step 3's acceptance evidence clause so scheduled future reachability is tracked as incomplete work, not a completion substitute.
2. Keep the opt-in command outside default PR CI, but make its current artifact or externally archived equivalent mandatory before Phase 8 is marked complete.
