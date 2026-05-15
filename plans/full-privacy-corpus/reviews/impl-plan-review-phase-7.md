---
type: review
entity: implementation-plan-review
plan: "full-privacy-corpus"
phase: 7
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 7 - EU neighbor acts source family

> Reviewing [Phase 7 Implementation Plan](../implementation/phase-7-impl.md)
> Against [Phase 7 Scope](../phases/phase-7.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The plan is aligned with the intended EU neighbor source-family scope, but it is not yet executable without important interpretation. The main gaps are that the bounded Phase 6 seed artifact is not named as a required input, the testing plan has no real-source verification path for imported-or-limited EU outcomes, and the phase deliverable for CELEX/language/version policy documentation is not covered by an implementation or verification step. Under the requested rule that Ready requires zero Critical/Major/Minor/Note findings, this review is not Ready.

## Scope Alignment

### Findings

- **Minor**: Phase 7 explicitly delivers "CELEX/language/version policy documentation", but the implementation plan only says to add source metadata fields and tests. There is no step to update a policy/doc artifact such as `docs/features/source-provenance.md` or a dedicated EU source-policy note, and no docs check in the testing plan.

## Technical Feasibility

### Findings

- **Major**: The plan says EU neighbor records must come from the approved Phase 6 seed graph, but it does not name the concrete Phase 6 output `mcp/legal_texts/data/privacy_scope_seed.v1.json` as required context or as a required source of truth for Step 1. Step 1 allows either direct edits in `mcp/legal_texts/sources.py` or a builder fed by the seed file, which leaves room to hard-code AI Act/Data Act records without validating that they match the approved seed graph. That weakens the phase's core boundary: "approved scope graph or explicit seed additions only."

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Add bounded EU neighbor source records | Partial | Partial | It names AI Act/Data Act CELEX values, but does not require reading the Phase 6 seed file or define a mismatch/fail-fast check against it. |
| 2 | Generalize EUR-Lex parsing | Yes | Yes | No issue. It references the real current parser and specifies expected output behavior for new unit types and unsupported structures. |
| 3 | Add fixtures and source limitation records | Partial | Partial | Fixture behavior is clear, but source reachability classification is not backed by an explicit real-source verification command or persisted evidence artifact. |
| 4 | Validate relationship target readiness | Partial | Partial | The target behavior is in scope, but the step depends on Phase 6 relationship/seed outputs without naming the concrete seed graph input in required context. |

## Required Context Assessment

### Missing Context

- `mcp/legal_texts/data/privacy_scope_seed.v1.json` - Planned Phase 6 seed graph output and the direct authority for the AI Act/Data Act CELEX records that bound this phase.
- `docs/features/source-provenance.md` or a dedicated source-policy document - Needed if Phase 7 is to satisfy the CELEX/language/version policy documentation deliverable.

### Unnecessary Context

- None.

## Testing Plan Assessment

### Test Integrity Check

The plan includes one primary verify command and protects important regressions: existing DSGVO parser behavior must remain unchanged, relationship targets must resolve, and source limitations must be first-class outcomes. It does not propose disabling or weakening existing tests.

### Test Gaps

- **Major**: The testing plan is fixture-only and does not include an explicit or opt-in real-source check that fetches or probes the selected official German EUR-Lex/Cellar source URLs for AI Act and Data Act, validates their terminal manifest states, and persists imported-or-limited evidence. Fixture tests can prove parser behavior, but they cannot prove that the selected CELEX/language/version policy resolves to reachable official German text or to a correct source limitation.

### Real-World Testing

Real-world testing is not planned. For this phase, that is a material limitation because the acceptance criteria depend on official EUR-Lex/Cellar availability and explicit source limitations when German text is unavailable or unsupported.

## Reality Check Validation

The reality check correctly identifies the current code anchors: `mcp/legal_texts/eurlex_xml.py::parse_dsgvo_xml` is DSGVO-specific, `mcp/legal_texts/sources.py::SOURCE_SPECS["dsgvo_eu_2016_679"]` is the existing Cellar metadata pattern, and `mcp/legal_texts/importer.py::validate_dsgvo_doc2` is currently DOC_2-specific. Planned prerequisite files such as `mcp/legal_texts/manifest.py` and `mcp/legal_texts/relationships.py` are acceptable Phase 1/2/6 dependencies, but the Phase 7 plan should name the concrete Phase 6 seed artifact as an execution input.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Technical Feasibility | Phase 7 does not require the concrete Phase 6 seed graph artifact as the source of truth for AI Act/Data Act source records. | Add `mcp/legal_texts/data/privacy_scope_seed.v1.json` to required context and require source record generation or validation to fail if the seed file is missing or CELEX/canonical IDs diverge. |
| 2 | Major | Testing | The plan lacks real-source verification for official German EUR-Lex/Cellar imported-or-limited outcomes. | Add an opt-in command or script that probes/fetches the selected AI Act/Data Act official sources, validates terminal manifest states, and writes a persisted evidence artifact. |
| 3 | Minor | Scope Alignment | The CELEX/language/version policy documentation deliverable is not implemented or verified. | Add a documentation/policy step and include it in the verification path, even if broader user-facing docs remain deferred to Phase 13. |

## Recommendations

1. Revise Step 1 and Required Context so Phase 7 consumes or validates against `mcp/legal_texts/data/privacy_scope_seed.v1.json` from Phase 6, including explicit AI Act/Data Act canonical IDs and CELEX mismatch failures.
2. Add a secondary real-source verification command for AI Act/Data Act official German EUR-Lex/Cellar reachability and terminal-state evidence.
3. Add a scoped CELEX/language/version policy documentation step and a lightweight docs verification expectation.
