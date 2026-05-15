---
type: review
entity: implementation-plan-review
plan: "full-privacy-corpus"
phase: 9
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 9 - German state-law machine-readable and HTML adapters

> Reviewing [Phase 9 Implementation Plan](../implementation/phase-9-impl.md)
> Against [Phase 9 Scope](../phases/phase-9.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The plan is directionally aligned with Phase 9's machine-readable and stable-HTML state-law scope, and it correctly avoids PDF-only work deferred to Phase 10. It is not executable without important interpretation: it does not require the concrete Phase 8 inventory data as the authoritative input, it does not define the normalization/generated-package integration path that turns adapter results into package records or limitations, and it lacks real-source verification for official adapter outcomes.

Finding counts: Critical 0, Major 3, Minor 0, Note 0.

## Scope Alignment

### Findings

- **Major**: Phase 9 acceptance requires every Phase 8 `machine_readable` or `stable_html` state to produce imported records or a justified source limitation, but the implementation plan never names the concrete Phase 8 inventory data file as an execution input or requires a preflight enumeration of eligible states. The current Phase 8 implementation plan defines `mcp/legal_texts/data/state_law_sources.v1.json` and possibly `mcp/legal_texts/data/state_law_limitations.v1.json` as the source of truth; Phase 9 only references `phase-8-impl.md` and the planned API module.

## Technical Feasibility

### Findings

- **Major**: The plan says adapter results must be convertible to Phase 2 generated-package records and Phase 1 source limitations, and the testing table expects package validation, but no implementation step actually wires adapter outcomes into the generated package/manifest path. Current code has only the legacy `normalize_snapshot` path that dispatches GII vs DSGVO by source kind, and Phase 2 plans a strict generated-package path; Phase 9 needs a concrete step for writing or merging state-law `laws.json`, `norms.json`, manifest terminal states, and `source-limitations.json` records before validation.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Add state-law adapter interfaces | Yes | Mostly | The result contract is concrete, but later steps do not specify the package/manifest conversion path that consumes it. |
| 2 | Implement machine-readable adapters from inventory | Partial | Partial | It does not name the Phase 8 inventory data file, require an eligible-state preflight, or define how source-specific parsers are selected from inventory fields. |
| 3 | Implement stable HTML adapters from inventory | Partial | Partial | It requires stable selectors or structure but does not require those selectors to be read from, added to, or validated against the Phase 8 inventory artifact. |
| 4 | Add fixtures and validation tests | Partial | Partial | Fixture tests are named, but the plan omits an explicit generated-package integration step and a real-source adapter verification command. |

## Required Context Assessment

### Missing Context

- `mcp/legal_texts/data/state_law_sources.v1.json` - Planned Phase 8 inventory data file and the direct authority for which states are in Phase 9 scope.
- `mcp/legal_texts/data/state_law_limitations.v1.json` or the actual Phase 8 limitation artifact path - Needed if Phase 9 downgrades an eligible state to a justified limitation and must preserve existing limitation references.
- `mcp/tests/test_generated_package.py` - Planned Phase 2 generated-package contract tests that should be exercised when Phase 9 claims imported or limited outcomes validate as package records.

### Unnecessary Context

- None.

## Testing Plan Assessment

### Test Integrity Check

The plan protects `test_state_law_inventory.py` from being weakened and prevents PDF parser tests/manual transcription fixtures from entering Phase 9. It does not propose disabling existing tests, but it also does not explicitly include the generated-package contract tests that should guard the package records this phase emits.

### Test Gaps

- **Major**: Real-source verification is not planned. The testing plan is fixture-backed only, while Phase 9 depends on official state portals, source stability, provenance fields, content hashes, and explicit source limitations when an eligible state proves infeasible. Fixtures can validate parser behavior, but they do not prove that the Phase 8 eligible official URLs still fetch, still match the adapter assumptions, or produce current imported-or-limited evidence.

### Real-World Testing

No real-world or opt-in integration testing path is defined for Phase 9. The plan should add a command such as `PYTHONPATH=mcp uv run --group dev python scripts/verify_state_law_adapters.py --inventory mcp/legal_texts/data/state_law_sources.v1.json --package-dir .artifacts/state-law/package --output .artifacts/state-law/adapter-gate.json` that processes only `machine_readable` and `stable_html` records, validates imported-or-limited outcomes, and writes persisted evidence outside default PR CI.

## Reality Check Validation

### Findings

- The Reality Check correctly identifies that current `mcp/legal_texts/normalizer.py` only dispatches GII or DSGVO by source kind, `mcp/legal_texts/validation.py::_validate_source` has no state-law provenance support, and registry loading from `laws.v1.json` will not cover generated state-law IDs. The missing implementation step for this integration is counted as Finding 2.
- The current repository does not yet contain `mcp/legal_texts/manifest.py`, `mcp/legal_texts/state_law_inventory.py`, or `mcp/tests/test_state_law_inventory.py`; those are acceptable Phase 1/8 prerequisites rather than independent Phase 9 defects, but Phase 9 still needs to name the concrete Phase 8 inventory artifact it will consume once those prerequisites exist.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Scope / Required Context | The plan does not require the concrete Phase 8 inventory data file or a preflight enumeration of `machine_readable`/`stable_html` states. | Add `mcp/legal_texts/data/state_law_sources.v1.json` and the limitation artifact path to Required Context, then add a first implementation step that validates Phase 8 completion and derives the exact eligible state set before parser work starts. |
| 2 | Major | Technical Feasibility | Adapter outcomes are not wired into a concrete generated-package/manifest output path. | Add an implementation step that converts adapter results into state-law law/norm records, source limitations, manifest terminal states, and generated-package files, then validates them through Phase 1/2 helpers. |
| 3 | Major | Testing | The testing plan lacks opt-in real-source verification for official machine-readable and stable HTML adapter outcomes. | Add a state-law adapter gate script that reads the Phase 8 inventory, fetches/processes eligible official sources, validates imported-or-limited outcomes, and writes a persisted evidence artifact outside default PR CI. |

## Recommendations

1. Revise Phase 9 so execution starts from the actual Phase 8 inventory artifact and fails fast if the eligible state set is missing, incomplete, or inconsistent with adapter classes.
2. Add a dedicated package/manifest integration step instead of leaving adapter result conversion implicit.
3. Add an opt-in real-source adapter verification command and include generated-package contract tests in the primary verification path.
