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

The revised implementation plan resolves the prior documentation-scope gap by adding a dedicated DSGVO article/recital documentation step and docs verification target. The remaining issue is narrow but actionable: the resolver work is described as a `resolver.py` change, while current structured citation resolution depends on unit normalization and canonical norm ID construction in `mcp/legal_texts/models.py`. Because the user requested Ready only when Critical/Major/Minor/Note counts are all zero, this single Minor finding prevents a Ready verdict.

## Scope Alignment

### Findings

- None. The plan now covers Phase 5's required parser, recital, source-policy, resolver/search, full-count evidence, and documentation deliverables without adding AI Act, Data Act, relationship graph, or state-law scope.

## Technical Feasibility

### Findings

- Minor: Step 4 requires structured `unit="recital"` resolver calls, but the current resolver delegates unit acceptance and canonical ID construction to `mcp/legal_texts/models.py` via `normalize_unit()` and `canonical_norm_id()`. Phase 2 adds generated-record unit validation, but its implementation plan explicitly defers runtime resolver support; Phase 5 should therefore name `mcp/legal_texts/models.py` as an implementation target for `recital` runtime normalization and, likely, citation labeling.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Record the DSGVO Cellar version policy | Yes | Yes | None. |
| 2 | Extend the EUR-Lex parser for full articles | Yes | Yes | None. |
| 3 | Add recital extraction as first-class norms | Yes | Yes | None. |
| 4 | Add resolver and search fixtures | Partial | Partial | It names `resolver.py` but not `models.py`, even though `resolve_citation()` calls `normalize_unit()` and `canonical_norm_id()` from `models.py` before resolving records. |
| 5 | Add DSGVO full-count gate evidence | Yes | Yes | None. |
| 6 | Document DSGVO article and recital citation units | Yes | Yes | None. |

## Required Context Assessment

### Missing Context

- `mcp/legal_texts/models.py` - required for Phase 5 runtime support because `NormUnit`, `normalize_unit()`, and `canonical_norm_id()` control whether structured `unit="recital"` calls can produce `recital:<n>` canonical norm IDs.

### Unnecessary Context

- None.

## Testing Plan Assessment

### Test Integrity Check

The test integrity constraints are adequate for the parser, resolver, search, source-policy, generated-package, and full-count evidence work. The plan preserves existing selected DSGVO article behavior, keeps the existing DOC_2 parser test authoritative, avoids fake full counts in fast fixtures, and explicitly prohibits weakening Phase 2 generated-package validation for malformed recital records.

### Test Gaps

- The resolver/search test row should explicitly include a structured `resolve_citation(..., unit="recital", paragraph_or_article="1")` case, not only exact `get_norm(..., "recital:1")`, so the `models.py` normalization path is exercised.

### Real-World Testing

Real-world / integration testing is planned through the opt-in full-count command:

`PYTHONPATH=mcp uv run --group dev python scripts/verify_dsgvo_full_counts.py --package-dir .artifacts/dsgvo/package --output .artifacts/dsgvo/full-counts.json`

That gate is scoped to generated/live corpus evidence rather than fast fixtures and verifies the official DSGVO article and recital counts, selected CELEX/Cellar metadata, source hash, version/consolidation policy, and boundary resolver samples.

## Reference Consistency

### Findings

- Minor: The Reality Check table lists `normalize_unit` under `mcp/legal_texts/resolver.py`, but the symbol is imported from `mcp/legal_texts/models.py`. This matters because `resolver.py` cannot fully support structured recital calls without changing the model-level normalization helper.

## Reality Check Validation

### Findings

- Minor: The Reality Check correctly identifies that current exact parsing only accepts `par` and `art`, but it does not fully capture that the runtime unit-normalization owner is `mcp/legal_texts/models.py`, not just `mcp/legal_texts/resolver.py`.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Minor | Resolver Support | Structured `unit="recital"` calls require updates to `mcp/legal_texts/models.py` (`normalize_unit()`, `canonical_norm_id()` behavior, and possibly citation labels), but Step 4 and Required Context only name `resolver.py` for runtime resolver support. | Add `mcp/legal_texts/models.py` to Required Context and Step 4, and require tests for both exact `recital:<n>` parsing and structured `unit="recital"` resolution. |

| Severity | Count |
| -------- | ----- |
| Critical | 0 |
| Major | 0 |
| Minor | 1 |
| Note | 0 |

## Recommendations

1. Revise Step 4 to include `mcp/legal_texts/models.py` alongside `resolver.py`, with explicit work for `normalize_unit("recital")`, `canonical_norm_id("recital", value)`, and user-facing citation labels for recital records.
2. Add a focused resolver test for structured `resolve_citation(dataset, "DSGVO", "recital", "1")` in addition to exact `get_norm(dataset, "DSGVO", "recital:1")`.
