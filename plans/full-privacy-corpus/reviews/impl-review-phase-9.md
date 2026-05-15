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

The implementation has the core Phase 9 mechanics in place: the eligible state set is inventory-derived, state-law IDs are jurisdiction-prefixed, generated-package validation runs, and the live adapter artifact records terminal outcomes for all 16 states. However, one imported live record still contains portal chrome in law and norm output, so the stable HTML adapter cannot yet be accepted as producing clean normalized legal text.

**Finding count**: Critical 0, Major 1, Minor 0, Note 0.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Every machine-readable or stable HTML state from Phase 8 has imported records or a justified source limitation if implementation proves infeasible. | Partial | `mcp/tests/test_state_law_adapters.py` derives 13 eligible stable-HTML states; `.artifacts/state-law/adapter-gate.json` records 13 eligible, 2 imported, 11 `parse_failed`, 3 existing limitation-only states, and `validation_errors: []`; `.artifacts/state-law/package/source-limitations.json` records Phase 9 parse-failed limitations with content hashes and diagnostics. | Imported BB records are not clean normalized legal text: `.artifacts/state-law/package/laws.json:5` uses the portal title `Brandenburgisches Vorschriftensystem`, and 34 BB norms include `Einzelnorm` chrome, including `par:35` at `.artifacts/state-law/package/norms.json:2474`. |
| 2 | State-law canonical IDs encode jurisdiction clearly. | Yes | Imported laws use IDs such as `state:bb/brandenburgisches-datenschutzgesetz` and `state:nw/datenschutzgesetz`; validation builds state-law canonical IDs with `state_code`; `test_state_law_ids_do_not_collide_with_non_state_sources` asserts the `state:` prefix. | None. |
| 3 | State-law records do not collide with GII or EUR-Lex records. | Yes | `mcp/legal_texts/state_law_inventory.py` derives `state:<code>/<slug>` IDs; `mcp/legal_texts/manifest.py` validates state-law canonical IDs with state prefixes; tests assert no overlap with `bdsg_2018`, `tdddg`, or `dsgvo_eu_2016_679`. | None. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 0 | Validate Phase 8 inventory inputs and derive eligible states. | Implemented via `eligible_state_law_records()` and inventory validation. | No. | Good. |
| 1 | Add adapter result interfaces. | Implemented `ParsedStateLaw` and `StateLawAdapterResult` in `mcp/legal_texts/state_law.py`. | No. | Good. |
| 2 | Implement machine-readable adapters from inventory. | No machine-readable records are currently eligible; all 13 eligible records are `stable_html`. | No. | Acceptable for current inventory. |
| 3 | Implement stable HTML adapters without parsing website chrome. | Generic HTML parser, fallback heading extraction, duplicate-candidate scoring, and meta-refresh handling were added. | Yes. | Partially successful, but live BB output still includes portal chrome. |
| 4 | Write generated-package and manifest outcomes. | Implemented package writer, manifest, source limitations, package hashes, and validation. | No. | Good mechanically. |
| 5 | Add fixtures and validation tests. | Added 11 fixture-backed tests covering parser output, meta refresh, parse failures, package validation, and ID collision. | Yes. | Coverage is useful but misses remaining chrome contamination and display-name correctness. |
| 6 | Add opt-in real-source adapter verification. | Implemented `scripts/verify_state_law_adapters.py`; live artifact was generated under `.artifacts/state-law/`. | No. | Good separation from default release gate. |

## Code Quality Assessment

### Findings

- **Major - Live imported HTML still leaks portal chrome into generated records.** The fallback parser builds candidate norm text from page-wide visible text (`mcp/legal_texts/state_law.py:691`) and only scores against a limited chrome-term list (`mcp/legal_texts/state_law.py:734`). The generated live package shows the result: the BB law display name is the portal title at `.artifacts/state-law/package/laws.json:5`, and `par:35` ends with `Einzelnorm nach oben` at `.artifacts/state-law/package/norms.json:2474`. `jq '[.[] | select((.text // "") | contains("Einzelnorm"))] | length' .artifacts/state-law/package/norms.json` reports 34 affected top-level norms. This violates the Phase 9 implementation constraint to avoid parsing unstable website chrome as legal text and would pollute resolver/search output once state-law records are exposed.

## Testing Assessment

### Verify Command Result

- **Command**: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_state_law_adapters.py`
- **Exit Code**: 0
- **Result**: 11 passed.

- **Command**: `PYTHONPATH=mcp uv run --group dev python -m pytest mcp/tests/test_generated_package.py mcp/tests/test_dataset_validation.py`
- **Exit Code**: 0
- **Result**: 38 passed.

The execution digest also reports the live adapter gate passed, the full release gate passed with 188 tests, HTTP CLI E2E passed, and MCP streamable HTTP E2E passed. I did not rerun the live adapter gate or full release gate during review; I inspected the generated live artifacts directly.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `test_eligible_state_law_records_are_derived_from_current_inventory` | Inventory-derived eligible state set. | Yes. | None. |
| Parser fixture tests | Synthetic marker parsing, official-like fallback parsing, duplicate portal-help candidate scoring. | Partial. | The duplicate-help regression checks only selected terms (`Hilfe`, `Inhaltsübersicht`, `Reiter`) and does not cover common official portal labels such as `Einzelnorm`, `nach oben`, or portal-title display-name contamination. |
| `test_meta_refresh_is_followed_and_preserved_in_import_metadata` | NRW meta refresh and provenance preservation. | Yes. | None. |
| Package/source-limitation tests | Importable fixture package, parse failure limitations, fetch exceptions, generated-package validation. | Yes. | They verify schema and terminal-state behavior, not semantic text cleanliness. |
| ID collision test | State-law IDs remain `state:`-prefixed and do not overlap existing GII/EUR-Lex IDs. | Yes. | None. |

### Real-World Testing

Performed. The live adapter gate artifact at `.artifacts/state-law/adapter-gate.json` records 16 inventory states, 13 eligible stable-HTML states, 2 imported laws, 11 parse failures, 3 source-unavailable limitation-only states, and no validation errors. That real-world evidence is useful and is what exposed the remaining BB text contamination.

## Scope Compliance

### Findings

- Scope is otherwise appropriate: Phase 9 stays within state-law adapters, fixtures, validation, generated-package evidence, and release-gate wiring. The generated `.artifacts/state-law/` package is ignored by `.gitignore`, preserving the generated-data-outside-Git requirement.

## Regression Risk

### Test Integrity Check

- [x] No existing tests were deleted in the reviewed Phase 9 paths.
- [x] No existing tests were disabled.
- [x] No existing assertions were weakened in the reviewed Phase 9 paths.
- [x] Pre-existing release coverage is still included by `scripts/verify_release.py`; the execution digest reports the release gate passed.

### Findings

- The main regression risk is semantic, not schema-level: current validation can pass packages whose text contains portal chrome. Without a regression fixture based on the live BB failure mode, future parser changes could reintroduce similar contamination while all tests and package validation still pass.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | HTML adapter / generated text quality | Live BB imported records still include portal chrome in the law display name and norm text. | Rework stable HTML extraction so imported records contain only legal text and law titles; add regression coverage for `Einzelnorm`, `nach oben`, portal title contamination, and the live BB `par:35` artifact shape. |

## Recommendations

1. Blocking for acceptance: sanitize or structurally exclude remaining portal chrome from stable HTML output, regenerate the live state-law package, and add fixture coverage that would fail on the current `Einzelnorm` / portal-title contamination.
