---
type: review
entity: implementation-review
plan: "full-privacy-corpus"
phase: 9
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Review: Phase 9 - German state-law machine-readable and HTML adapters

> Reviewing implementation of [Phase 9](../phases/phase-9.md)
> Against [Implementation Plan](../implementation/phase-9-impl.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Rework

The two prior review findings are resolved for their reported failure modes: the BB artifact now uses a legal law title and has zero `Einzelnorm` / `nach oben` text, and the NRW artifact has zero occurrences of `Mehr Paragraph`, `ausdrucken`, `Link kopieren`, `Link kopiert`, or `Pragraph` in top-level norm text and subdivisions. However, the imported NRW package still contains a real portal-navigation label in legal text: `state:nw/datenschutzgesetz/par:72` ends with `Zum Textanfang`. That keeps Phase 9 short of the stable-HTML requirement that imported records not include website chrome.

**Finding count**: Critical 0, Major 1, Minor 0, Note 0.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Every machine-readable or stable HTML state from Phase 8 has imported records or a justified source limitation if implementation proves infeasible. | Partial | `mcp/tests/test_state_law_adapters.py:68` derives 13 eligible stable-HTML records. `.artifacts/state-law/adapter-gate.json` reports 16 inventory states, 13 eligible sources, 2 imported laws, 11 `parse_failed`, 3 `source_unavailable`, 14 source limitations, and `validation_errors: []`. Package and manifest validation also returned `[]`. | One imported NRW record is not clean normalized legal text: `.artifacts/state-law/package/norms.json:9358` ends `state:nw/datenschutzgesetz/par:72` with the portal link label `Zum Textanfang`. |
| 2 | State-law canonical IDs encode jurisdiction clearly. | Yes | Imported laws are `state:bb/brandenburgisches-datenschutzgesetz` and `state:nw/datenschutzgesetz`; all imported norms use those law IDs as prefixes. `test_state_law_ids_do_not_collide_with_non_state_sources` checks `state:` prefixes in `mcp/tests/test_state_law_adapters.py:272`. | None. |
| 3 | State-law records do not collide with GII or EUR-Lex records. | Yes | State-law IDs use the `state:<state-code>/<law-slug>` shape, and the collision test checks no overlap with `bdsg_2018`, `tdddg`, or `dsgvo_eu_2016_679` at `mcp/tests/test_state_law_adapters.py:272`. | None. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 0 | Validate Phase 8 inventory inputs and derive eligible states. | Implemented through `eligible_state_law_records()` and inventory validation. | No. | Good. |
| 1 | Add adapter result interfaces. | Implemented `ParsedStateLaw` and `StateLawAdapterResult` in `mcp/legal_texts/state_law.py:90`. | No. | Good. |
| 2 | Implement machine-readable adapters from inventory. | Current inventory has no eligible `machine_readable` records; all 13 eligible records are `stable_html`. | No. | Acceptable for current inventory. |
| 3 | Implement stable HTML adapters without parsing website chrome. | BB and NRW action chrome sanitization were added in `mcp/legal_texts/state_law.py:770`; fixture coverage checks the prior BB and NRW action strings. | Yes. | Still incomplete because one NRW imported norm retains a portal link label. |
| 4 | Write generated-package and manifest outcomes. | Implemented package, manifest, source limitation, hash, and validation outputs under `.artifacts/state-law/package`. | No. | Mechanically good. |
| 5 | Add fixtures and validation tests. | Added 13 state-law adapter tests, including BB portal chrome and NRW action chrome regressions. | No. | Useful coverage, but it does not catch the remaining `Zum Textanfang` footer/link case. |
| 6 | Add opt-in real-source adapter verification. | `scripts/verify_state_law_adapters.py` writes the adapter gate and generated package; fixture mode also runs without network. | No. | Good separation from default release checks. |

## Code Quality Assessment

### Findings

- **Major - Imported NRW legal text still contains portal chrome.** The fallback parser extracts norm segments from page-wide visible text in `_fallback_norm_items()` (`mcp/legal_texts/state_law.py:692`) and then applies a denylist sanitizer in `_sanitize_portal_chrome_text()` (`mcp/legal_texts/state_law.py:770`). The current denylist covers the r2 NRW action strings, but not the portal navigation label `Zum Textanfang`; the persisted live package shows that label in `state:nw/datenschutzgesetz/par:72` at `.artifacts/state-law/package/norms.json:9358` and `.artifacts/state-law/adapter-gate.json:10348`. This violates the Phase 9 instruction to avoid parsing unstable website chrome as legal text.

## Testing Assessment

### Verify Command Result

- **Command**: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_state_law_adapters.py`
- **Exit Code**: 0
- **Result**: 13 passed.

- **Command**: `PYTHONPATH=mcp uv run --group dev python - <<'PY' ... validate_generated_package(...) ... validate_corpus_manifest(...)`
- **Exit Code**: 0
- **Result**: `package_errors []`, `manifest_errors []`.

- **Command**: `PYTHONPATH=mcp uv run --group dev python scripts/verify_state_law_adapters.py --inventory mcp/legal_texts/data/state_law_sources.v1.json --limitations mcp/legal_texts/data/state_law_limitations.v1.json --package-dir /tmp/legal-text-mcp-de-state-law-review-package --output /tmp/legal-text-mcp-de-state-law-review-gate.json --fixture-mode`
- **Exit Code**: 0
- **Result**: fixture-mode adapter gate completed successfully.

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: 190 passed, HTTP CLI E2E OK, MCP streamable HTTP E2E OK.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `test_eligible_state_law_records_are_derived_from_current_inventory` | Inventory-derived eligible state set. | Yes. | None. |
| `test_official_html_fallback_sanitizes_portal_chrome_and_uses_legal_title` | BB title selection and removal of `Einzelnorm` / `nach oben`. | Yes for the r1 failure. | Does not cover other portal link/footer labels. |
| `test_official_html_fallback_sanitizes_nrw_action_chrome_from_text_and_subdivisions` | Removal of `Mehr Paragraph`, print/copy controls, and `Pragraph` typo before subdivision generation. | Yes for the r2 failure. | Does not cover `Zum Textanfang`, which appears in the live NRW artifact. |
| Package and validation tests | Generated package shape, manifest references, source limitations, and ID policy. | Yes for schema/provenance. | They do not enforce semantic text cleanliness beyond the specific fixture strings. |

### Real-World Testing

Performed through the persisted live adapter artifact. `.artifacts/state-law/adapter-gate.json` records 16 inventory states, 13 eligible stable-HTML states, 2 imported laws, 11 parse failures, 3 source-unavailable limitations, and no validation errors. Direct artifact spot checks confirmed the prior BB and NRW action-string findings are fixed, while also exposing the remaining NRW `Zum Textanfang` contamination.

## Scope Compliance

### Findings

- No out-of-scope code expansion was found in the reviewed Phase 9 files. The implementation stays within state-law adapters, fixtures, validation, generated-package evidence, and release-gate wiring.

## Regression Risk

### Test Integrity Check

- [x] No existing Phase 9 adapter tests were deleted in the reviewed paths.
- [x] No existing Phase 9 adapter tests were disabled.
- [x] No existing Phase 9 adapter assertions were weakened in the reviewed paths.
- [x] Targeted adapter tests and the full skipped-live release gate pass.

### Findings

- The remaining risk is the same class as the prior two reviews: schema validation passes even when imported norm text contains portal chrome. Without a broader artifact-level or fixture-level cleanliness check, future portal labels can be imported while all current tests remain green.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | HTML adapter / generated text quality | `state:nw/datenschutzgesetz/par:72` still includes the real portal link label `Zum Textanfang` in imported norm text. | Strip or structurally exclude this NRW portal link/footer text before accepting imported records; add regression coverage that fails when `Zum Textanfang` or similar portal navigation labels appear in imported norm text. |

## Recommendations

1. Blocking for acceptance: remove the remaining NRW `Zum Textanfang` portal label from stable-HTML output, regenerate `.artifacts/state-law/package`, and add a regression assertion that covers this footer/link case in imported text.
2. Follow-up after the blocker: consider extending generated-package validation or the adapter gate with a small state-law portal-chrome denylist so this class of issue is caught on live artifacts rather than only by manual review.
