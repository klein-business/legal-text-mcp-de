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

**Verdict**: Needs Revision

The implementation plan is technically grounded and mostly executable: it identifies the current EUR-Lex parser, source metadata, importer validation, resolver, search, package validation, and fixture surfaces that Phase 5 must change. It also includes an explicit generated/full-count gate for 99 articles and 173 recitals. However, Phase 5 lists a documentation update for article and recital citation units as a deliverable, while the implementation plan omits a documentation step and instead notes that final docs are deferred to Phase 13. Under the requested rule that Ready requires zero Critical/Major/Minor/Note findings, this prevents a Ready verdict.

## Scope Alignment

### Findings

- Phase 5 requires a documentation update describing article and recital citation units, but the implementation plan does not include a documentation implementation step or verification target for that deliverable.

## Technical Feasibility

### Findings

- None.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Record the DSGVO Cellar version policy | Yes | Yes | None. |
| 2 | Extend the EUR-Lex parser for full articles | Yes | Yes | None. |
| 3 | Add recital extraction as first-class norms | Yes | Yes | None. |
| 4 | Add resolver and search fixtures | Yes | Yes | None. |
| 5 | Add DSGVO full-count gate evidence | Yes | Yes | None. |

## Required Context Assessment

### Missing Context

- None.

### Unnecessary Context

- None.

## Testing Plan Assessment

### Test Integrity Check

The test integrity constraints are adequate for the parser, resolver, search, source-policy, generated-package, and full-count evidence work. The plan preserves the existing selected DSGVO article behavior, keeps the existing DOC_2 parser test authoritative, avoids fake full counts in fast fixtures, and explicitly prohibits weakening Phase 2 generated-package validation for malformed recital records.

### Test Gaps

- None for the planned code and generated-artifact behavior. The documentation deliverable gap is tracked under Scope Alignment.

### Real-World Testing

Real-world / integration testing is planned through the opt-in full-count command:

`PYTHONPATH=mcp uv run --group dev python scripts/verify_dsgvo_full_counts.py --package-dir .artifacts/dsgvo/package --output .artifacts/dsgvo/full-counts.json`

That gate is scoped to generated/live corpus evidence rather than fast fixtures and verifies the official DSGVO article and recital counts, selected CELEX/Cellar metadata, source hash, version/consolidation policy, and boundary resolver samples.

## Reality Check Validation

### Findings

- None.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Minor | Scope Alignment | Phase 5 includes a documentation update deliverable for article and recital citation units, but the implementation plan has no documentation step or doc verification target and instead defers final docs to Phase 13. | Add a narrow Phase 5 documentation step, likely updating `docs/features/supported-laws.md` and the citation-unit/API contract docs only as needed to describe DSGVO `art:*` and `recital:*` support. |

| Severity | Count |
| -------- | ----- |
| Critical | 0 |
| Major | 0 |
| Minor | 1 |
| Note | 0 |

## Recommendations

1. Add a scoped documentation step to the Phase 5 implementation plan and include the relevant docs in the primary or focused verification path.
