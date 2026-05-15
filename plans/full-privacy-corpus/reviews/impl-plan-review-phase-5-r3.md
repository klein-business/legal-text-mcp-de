---
type: review
entity: implementation-plan-review
plan: "full-privacy-corpus"
phase: 5
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 5 - Full DSGVO articles and recitals

> Reviewing [Phase 5 Implementation Plan](../implementation/phase-5-impl.md)
> Against [Phase 5 Scope](../phases/phase-5.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Ready

The latest implementation plan is executable against the Phase 5 scope and correctly accounts for the prior Phase 1 and Phase 2 dependencies. It covers full DSGVO article parsing, recital extraction, source/version evidence, resolver/search behavior, generated full-count gates, and the scoped documentation update without expanding into later EU-neighbor, relationship-graph, or state-law phases.

## Scope Alignment

### Findings

None.

## Technical Feasibility

### Findings

None. The plan aligns with the current code anchors: `parse_dsgvo_xml()` owns EUR-Lex article parsing, `SOURCE_SPECS["dsgvo_eu_2016_679"]` already carries the selected CELEX/Cellar metadata, `validate_dsgvo_doc2()` is the current DOC_2 source guard, and structured resolver support for `recital` is now correctly assigned to both `models.py` and `resolver.py`.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Record the DSGVO Cellar version policy | Yes | Yes | None. |
| 2 | Extend the EUR-Lex parser for full articles | Yes | Yes | None. |
| 3 | Add recital extraction as first-class norms | Yes | Yes | None. |
| 4 | Add resolver and search fixtures | Yes | Yes | None. |
| 5 | Add DSGVO full-count gate evidence | Yes | Yes | None. |
| 6 | Document DSGVO article and recital citation units | Yes | Yes | None. |

## Required Context Assessment

### Missing Context

None.

### Unnecessary Context

None.

## Testing Plan Assessment

### Test Integrity Check

The testing plan preserves existing selected DSGVO article behavior, keeps the existing DOC_2 parser test authoritative, exercises exact and structured `recital` resolution through model-level normalization, includes search coverage, and explicitly prohibits fake full counts in fast fixtures or weakened Phase 2 generated-package validation.

### Test Gaps

None.

### Real-World Testing

Real-world / integration testing is planned through the opt-in full-count command:

`PYTHONPATH=mcp uv run --group dev python scripts/verify_dsgvo_full_counts.py --package-dir .artifacts/dsgvo/package --output .artifacts/dsgvo/full-counts.json`

The planned gate verifies articles 1-99, recitals 1-173, selected CELEX/Cellar metadata, source hash, version/consolidation policy, and boundary resolver samples for `art:1`, `art:99`, `recital:1`, and `recital:173`.

## Reality Check Validation

The Reality Check is accurate for the current repository state. It identifies the current article-only parser, existing Cellar metadata pinning, DOC_2 validation limits, model-level unit normalization ownership, and resolver exact-reference restrictions; it also correctly flags that Phase 5 must wait for the Phase 1/2 prerequisites before execution.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| - | - | - | No findings. | No action required. |

| Severity | Count |
| -------- | ----- |
| Critical | 0 |
| Major | 0 |
| Minor | 0 |
| Note | 0 |

## Recommendations

1. Proceed to execution after the Phase 1 and Phase 2 prerequisites have landed.
