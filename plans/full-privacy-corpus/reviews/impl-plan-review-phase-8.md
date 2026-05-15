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

The implementation plan is aligned with the intended inventory-only scope and avoids premature parser/runtime exposure, but it does not yet provide enough executable detail to prove the phase's external-source obligations. In particular, the plan leaves live reachability evidence and manifest source-limitation materialization under-specified, so an implementer could finish the unit tests while still failing Phase 8 acceptance.

## Scope Alignment

### Findings

- Phase 8 scope includes reachability/stability checks for machine-readable, stable HTML, and PDF sources, plus manifest limitation records for states without stable official sources. The implementation plan includes schema fields and fake-fetch tests, but it does not require a real reachability run or persisted manifest limitation records as completion evidence.

## Technical Feasibility

### Findings

- The proposed data-first inventory model fits the current repository shape: existing `mcp/legal_texts/sources.py` only models static GII/EUR-Lex serving sources, and current `mcp/legal_texts/validation.py` validates normalized record source metadata rather than inventory outcomes.
- The plan correctly treats `mcp/legal_texts/manifest.py` as a Phase 1 prerequisite. That file is not present in the current codebase, so Phase 8 must only execute after the Phase 1 manifest contract exists.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Add state-law inventory schema | Yes | Mostly | Conditional hash/provenance requirements and canonical state-law ID derivation need tightening. |
| 2 | Add committed inventory data | Yes | Partly | Does not specify where actual limitation records live or how `source_limitation_id` references are validated. |
| 3 | Add reachability and stability check hooks | Yes | Partly | Adds a hook, but not a required real-world execution/artifact for the phase gate. |
| 4 | Add validation tests and docs note | Yes | Mostly | Unit tests are appropriate, but cannot prove live source availability evidence by themselves. |

## Required Context Assessment

### Missing Context

- None requiring revision. The plan lists the relevant current anchors and the Phase 1 prerequisite implementation plan.

### Unnecessary Context

- None.

## Testing Plan Assessment

### Test Integrity Check

The plan has useful integrity constraints: it keeps state-law records out of normalized serving fixtures, preserves source limitation validation, and keeps live checks outside the default release gate. It does not explicitly say that existing tests will not be disabled or weakened, but the listed constraints are specific enough for this phase.

### Test Gaps

- The primary verify command only runs unit/manifest tests. It does not prove that the committed inventory was produced from current official source reachability checks.
- The tests are planned to validate source limitation records, but the implementation steps do not define the concrete manifest/data artifact that stores those records.

### Real-World Testing

Real-world testing is only mentioned as "explicit or scheduled" and outside `scripts/verify_release.py`; there is no required command, artifact path, or acceptance condition for a Phase 8 live reachability run. This is a material gap because the phase is specifically about official source availability and stability.

## Reference Consistency

### Findings

- `mcp/legal_texts/manifest.py` and `mcp/tests/test_corpus_manifest.py` are not present in the current repository, but the Phase 8 phase document explicitly depends on Phase 1 and the Phase 1 implementation plan creates those anchors. This is acceptable only if Phase 8 is executed after Phase 1.

## Reality Check Validation

### Findings

- The Reality Check accurately identifies that current runtime/docs have no state-law source family, and that Phase 8 must not create parser claims. It omits the planned Phase 1 manifest anchor from current-code anchors, which is reasonable because it is a prerequisite rather than current code.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Testing / Evidence | Phase 8 requires reachability and stability checks, but the implementation plan only creates an opt-in helper and fake-fetch tests. The primary verify command can pass without any real official source check or persisted evidence. | Add an explicit real-world verification step, for example `PYTHONPATH=mcp uv run --group dev python scripts/verify_state_law_inventory.py --inventory mcp/legal_texts/data/state_law_sources.v1.json --write-artifact ...`, and require the artifact to prove `checked_at`, status/content type, and hash when fetchable for all non-`limitation_only` records. |
| 2 | Major | Source Limitations | The phase scope requires manifest limitation records for states without stable usable official sources, but the implementation steps only require `source_limitation_id` on inventory records and do not specify the concrete manifest/data artifact or cross-reference validation for those limitation records. | Define where Phase 8 source limitation records are stored, require every `limitation_only` inventory item to reference a real Phase 1-compatible limitation record, and add tests that fail dangling or incomplete limitation references. |
| 3 | Minor | ID / Provenance Schema | The schema has `law_slug` and tests "malformed state-law IDs", but it does not explicitly define a `law_id` field or helper that enforces the global `state:<state-code>/<stable-law-slug>` rule before Phase 9 consumes the inventory. | Add a derived or stored `law_id` contract with validation that the state prefix matches `state_code`, or make the helper that derives it from `state_code` and `law_slug` part of Step 1 and test it directly. |

## Recommendations

1. Make live reachability evidence a required Phase 8 gate with a concrete command and persisted artifact, while keeping it outside default PR CI.
2. Specify and test the actual Phase 1-compatible source limitation records used by `limitation_only` states.
3. Tighten the inventory ID contract so Phase 9 can consume state-law IDs without inventing or reinterpreting them.
