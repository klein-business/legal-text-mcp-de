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

The specific prior BB finding is resolved: the regenerated BB law display name is legal-title text, and the artifact contains zero BB norms with `Einzelnorm` or `nach oben`. However, the broader Phase 9 requirement that imported stable-HTML records not contain portal chrome is still not met: every imported NRW norm contains repeated UI labels from the portal, so the generated package would expose non-legal website controls as legal text.

**Finding count**: Critical 0, Major 1, Minor 0, Note 0.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Every machine-readable or stable HTML state from Phase 8 has imported records or a justified source limitation if implementation proves infeasible. | Partial | `mcp/tests/test_state_law_adapters.py:64` derives 13 eligible stable-HTML records; `.artifacts/state-law/adapter-gate.json:2` records 13 eligible sources, 2 imported, 11 parse_failed, and 3 source_unavailable limitation-only states with `validation_errors: []`. Package and manifest validation also returned `[]`. | One imported outcome is not clean normalized legal text: all 71 NRW norms contain portal UI labels such as `Mehr Paragraph ausdrucken Paragraph Link kopieren` and footer copy text. Example: `.artifacts/state-law/package/norms.json:2878`; count check over `norms.json` returned 71 affected NRW norms. |
| 2 | State-law canonical IDs encode jurisdiction clearly. | Yes | Imported laws use `state:bb/brandenburgisches-datenschutzgesetz` and `state:nw/datenschutzgesetz` in `.artifacts/state-law/package/laws.json:3` and `.artifacts/state-law/package/laws.json:39`; tests assert all generated law and norm IDs start with `state:` at `mcp/tests/test_state_law_adapters.py:248`. | None. |
| 3 | State-law records do not collide with GII or EUR-Lex records. | Yes | `derive_state_law_id()` emits `state:<code>/<slug>` in `mcp/legal_texts/state_law_inventory.py:52`; `test_state_law_ids_do_not_collide_with_non_state_sources` checks against `bdsg_2018`, `tdddg`, and `dsgvo_eu_2016_679` at `mcp/tests/test_state_law_adapters.py:248`. | None. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 0 | Validate Phase 8 inventory inputs and derive eligible states. | Implemented with `eligible_state_law_records()` and inventory validation. | No. | Good. |
| 1 | Add adapter result interfaces. | Implemented `ParsedStateLaw` and `StateLawAdapterResult` in `mcp/legal_texts/state_law.py:89`. | No. | Good. |
| 2 | Implement machine-readable adapters from inventory. | Current inventory has no eligible machine-readable records; all eligible records are stable HTML. | No. | Acceptable for current inventory. |
| 3 | Implement stable HTML adapters without parsing website chrome. | Parser now rejects portal titles and sanitizes the BB-specific `Einzelnorm` / `nach oben` terms in `mcp/legal_texts/state_law.py:727` and `mcp/legal_texts/state_law.py:769`. | Yes. | Still incomplete because NRW imported text leaks repeated portal controls. |
| 4 | Write generated-package and manifest outcomes. | Implemented package writing, manifest, source limitations, hashes, and validation in `mcp/legal_texts/state_law.py:245`. | No. | Mechanically good. |
| 5 | Add fixtures and validation tests. | Added 12 state-law adapter tests, including `official_like_portal_chrome.html`. | No. | Useful coverage, but the chrome regression coverage is too narrow and misses NRW control/footer text. |
| 6 | Add opt-in real-source adapter verification. | `scripts/verify_state_law_adapters.py` writes the state-law gate and generated package. | No. | Good separation from default release checks. |

## Code Quality Assessment

### Findings

- **Major - Imported NRW norms still include portal UI chrome.** The fallback extraction still builds norm text from page-wide visible text and only removes `Einzelnorm` / `nach oben` in `_sanitize_portal_chrome_text()` (`mcp/legal_texts/state_law.py:769`). The generated package proves the remaining issue: `.artifacts/state-law/package/norms.json:2878` starts NRW `par:1` with `Mehr Paragraph ausdrucken Paragraph Link kopieren`, includes `Link kopiert Der Link zum Pragraph wurde kopiert` at the end, and the same prefix appears in all 71 NRW norms. This violates the Phase 9 implementation constraint to avoid parsing unstable website chrome as legal text.

## Testing Assessment

### Verify Command Result

- **Command**: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_state_law_adapters.py`
- **Exit Code**: 0
- **Result**: 12 passed.

- **Command**: `PYTHONPATH=mcp uv run --group dev python - <<'PY' ... validate_generated_package(...) ... validate_corpus_manifest(...)`
- **Exit Code**: 0
- **Result**: `package_errors []`, `manifest_errors []`.

The provided rework evidence also reports the live adapter gate passed and the full release gate passed with 189 tests plus HTTP CLI and MCP streamable HTTP E2E. I did not rerun the full release gate during this review; I inspected the persisted live artifacts directly and reran the targeted adapter tests and package/manifest validation.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `test_eligible_state_law_records_are_derived_from_current_inventory` | Inventory-derived eligible state set. | Yes. | None. |
| `test_official_html_fallback_sanitizes_portal_chrome_and_uses_legal_title` | BB-like portal title rejection and removal of `Einzelnorm` / `nach oben`. | Partial. | It catches the previous BB failure mode but not other common portal controls such as `Mehr`, `Paragraph ausdrucken`, `Link kopieren`, or `Link kopiert`. |
| Duplicate-help fallback test | Candidate scoring avoids an earlier duplicate portal-help block. | Partial. | It verifies selection among duplicate candidates, not cleanup of UI chrome embedded inside the selected legal block. |
| Package and limitation tests | Imported-or-limited outcomes, generated-package shape, source limitations, and ID policy. | Yes for schema; partial for content quality. | They do not assert imported norm text is free of portal chrome beyond the BB-specific fixture terms. |

### Real-World Testing

Performed through the persisted live adapter artifact. `.artifacts/state-law/adapter-gate.json` records 16 inventory states, 13 eligible stable-HTML states, 2 imported laws, 11 parse failures, 3 source-unavailable limitations, and no validation errors. That real-world artifact also exposes the remaining NRW portal-chrome contamination.

## Scope Compliance

### Findings

- No out-of-scope code expansion was found in the reviewed Phase 9 files. The implementation stays within state-law adapters, fixtures, validation, generated-package evidence, and release-gate wiring.

## Regression Risk

### Test Integrity Check

- [x] No existing Phase 9 adapter tests were deleted in the reviewed paths.
- [x] No existing Phase 9 adapter tests were disabled.
- [x] No existing Phase 9 adapter assertions were weakened in the reviewed paths.
- [x] Targeted Phase 9 adapter tests pass; provided release evidence reports the broader suite passes.

### Findings

- The main regression risk remains semantic text pollution: schema/package validation accepts records whose `text` fields contain official portal controls. Without a broader fixture or artifact-level assertion for imported text cleanliness, future parser changes can keep passing while generated legal text remains polluted.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | HTML adapter / generated text quality | NRW imported norms still contain repeated portal UI text in every norm, despite the BB-specific portal chrome fix. | Sanitize or structurally exclude NRW control/footer chrome before accepting imported records; add regression coverage for `Mehr Paragraph ausdrucken Paragraph Link kopieren`, `Link kopiert`, and similar portal controls in top-level norm text and subdivisions. |

## Recommendations

1. Blocking for acceptance: rework stable-HTML extraction so imported NRW records contain only legal text, regenerate `.artifacts/state-law/package`, and add a regression fixture or artifact-level assertion that fails on the current NRW chrome strings.
2. Follow-up after the blocker: consider validating imported state-law norm text against a small denylist of known portal-control phrases so package validation catches this class of issue before the artifacts are accepted.
