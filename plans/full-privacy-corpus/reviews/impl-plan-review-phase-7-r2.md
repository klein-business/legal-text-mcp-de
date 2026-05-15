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

**Verdict**: Ready

The revised plan is executable against the Phase 7 scope after accounting for its explicit prerequisites from Phases 1, 2, 5, and 6. It now names the Phase 6 seed graph as the authority for AI Act/Data Act CELEX and canonical IDs, adds imported-or-limited real-source evidence, includes relationship-target validation, and covers the CELEX/language/version documentation deliverable. Under the requested readiness rule, this review has zero Critical, Major, Minor, or Note findings.

## Scope Alignment

### Findings

No findings.

The implementation plan stays within the bounded EU neighbor-act scope. It covers AI Act and Data Act seed records, German EUR-Lex/Cellar language and version policy, representative fixtures, imported-or-limited manifest outcomes, and explicit avoidance of an unbounded EU importer or Phase 11 runtime APIs.

## Technical Feasibility

### Findings

No findings.

The plan's approach matches the current codebase and prior phase contracts. Current code anchors confirm that `mcp/legal_texts/eurlex_xml.py::parse_dsgvo_xml` is article-oriented, `mcp/legal_texts/sources.py::SOURCE_SPECS["dsgvo_eu_2016_679"]` is the existing Cellar metadata pattern, and `mcp/legal_texts/importer.py::validate_dsgvo_doc2` is DSGVO DOC_2-specific. The proposed work correctly builds on Phase 1 manifest terminal states, Phase 2 source limitation and relationship package validation, Phase 5 DSGVO parser generalization, and Phase 6 `privacy_scope_seed.v1.json`.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Add bounded EU neighbor source records | Yes | Yes | None. Requires seed-file consumption or fail-fast validation for missing/divergent AI Act/Data Act CELEX and canonical IDs. |
| 2 | Generalize EUR-Lex parsing | Yes | Yes | None. Identifies the real parser, compatibility wrapper, target citation units, and unsupported-structure behavior. |
| 3 | Add fixtures and source limitation records | Yes | Yes | None. Defines fixture location, first-class limitation behavior, and an opt-in real-source evidence artifact. |
| 4 | Validate relationship target readiness | Yes | Yes | None. Keeps the work limited to target validity and avoids Phase 11 runtime API exposure. |
| 5 | Document EU CELEX/language/version policy | Yes | Yes | None. Adds the previously missing documentation deliverable with bounded seed-policy wording. |

## Required Context Assessment

### Missing Context

None.

### Unnecessary Context

None.

## Testing Plan Assessment

### Test Integrity Check

The plan has exactly one primary verify command and one opt-in real-source command. It explicitly protects existing DSGVO parser/count/version tests, keeps source limitations as first-class tested outcomes, and does not propose disabling, weakening, skipping, or xfail-ing existing tests.

### Test Gaps

No findings.

### Real-World Testing

Real-world testing is planned through `scripts/verify_eu_neighbor_sources.py`, which probes or fetches selected official German EUR-Lex/Cellar URLs, validates imported-or-limited terminal states, and persists CELEX/language/version/hash evidence. Keeping this command opt-in is consistent with the plan's broader testing strategy for network-heavy checks.

## Reality Check Validation

### Findings

No findings.

The Reality Check section is consistent with the current repository. The current code still has a DSGVO-specific EUR-Lex parser, static `SourceSpec` entries with a DSGVO Cellar example, and DOC_2-specific DSGVO source validation. The plan also correctly acknowledges that broader manifest, relationship, and seed-graph support comes from earlier phase implementation plans rather than current baseline files.

## Findings Summary

| Severity | Count |
| -------- | ----- |
| Critical | 0 |
| Major | 0 |
| Minor | 0 |
| Note | 0 |

No findings.

## Recommendations

1. Proceed with Phase 7 only after the prerequisite Phase 1, Phase 2, Phase 5, and Phase 6 implementation contracts have landed or been re-verified against their final symbol names and schemas.
