---
type: review
entity: implementation-review
plan: "full-privacy-corpus"
phase: 5
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Review: Phase 5 - Full DSGVO articles and recitals

> Reviewing implementation of [Phase 5](../phases/phase-5.md)
> Against [Implementation Plan](../implementation/phase-5-impl.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Accepted

The Phase 5 rework fixes the prior Critical parser gap: official Formex `<GR.CONSID>/<CONSID>/<NP>/<NO.P>/<TXT>` recitals are now recognized as first-class `recital:*` norms, and a direct live parser smoke against the selected official Cellar DOC_2 source returned 99 articles and 173 recitals with all requested boundary IDs present. The updated fixture and tests now exercise the official `<CONSID>` shape, preserve legacy reduced `<RECITAL>` fixture support, keep existing article parsing behavior intact, and continue to validate generated packages strictly.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | DSGVO articles 1-99 resolve in generated corpus checks. | Yes | `mcp/legal_texts/eurlex_xml.py:17` still extracts `<ARTICLE>` records using the existing article path. Direct live parser smoke against `https://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0004.02/DOC_2` returned `articles 99` with `art:1` and `art:99` present. | None found. |
| 2 | DSGVO recitals 1-173 resolve as citation units. | Yes | `mcp/legal_texts/eurlex_xml.py:41` emits recital norms, `_is_recital_element()` accepts `CONSID` at `mcp/legal_texts/eurlex_xml.py:72`, and `_recital_value()` reads numeric values from `<NO.P>` at `mcp/legal_texts/eurlex_xml.py:94`. Direct live parser smoke returned `recitals 173` with `recital:1` and `recital:173` present. | None found. |
| 3 | DSGVO source metadata records the selected CELEX/Cellar expression, document, language, version/consolidation policy, and content hash. | Yes | `mcp/tests/fixtures/eurlex_dsgvo/source_policy.json` pins CELEX `32016R0679`, Cellar work, expression `0004.02`, language `de`, document `DOC_2`, version/consolidation policy, content hash, counts, and boundary samples. `scripts/verify_dsgvo_full_counts.py:52` validates source metadata fields and `scripts/verify_dsgvo_full_counts.py:63` validates content hash. | None found. |
| 4 | Existing selected DSGVO article behavior remains backwards compatible. | Yes | `mcp/tests/test_normalizer_eurlex.py:4` still verifies the selected article parser behavior for `ARTICLE IDENTIFIER="005"`. Targeted pytest for `mcp/tests/test_dsgvo_full_counts.py` and `mcp/tests/test_normalizer_eurlex.py` passed with 10 tests. User-provided release evidence also shows `verify_release.py` passed with 127 tests plus HTTP and MCP E2E. | None found. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Record DSGVO Cellar version policy. | Source policy fixture records CELEX, Cellar work/expression/document, language, version policy, consolidation policy, content hash, expected counts, and boundary samples. | No | Satisfies the policy/count contract used by the full-count gate. |
| 2 | Extend parser for full articles. | Article parsing remains based on official `<ARTICLE>` records and live parser smoke returned all 99 article IDs. | No | Adequate and backwards compatible. |
| 3 | Add recital extraction as first-class norms. | Parser now treats `CONSID` and `RECITAL` as recital elements and emits `recital:<n>` norms with `unit="recital"`. | No | Addresses the root cause from the previous review. |
| 4 | Add resolver and search fixtures. | `models.py` normalizes `recital`; `resolver.py` accepts canonical `recital:*` references and returns `DSGVO ErwG <n>` labels; `mcp/tests/test_dsgvo_full_counts.py:188` verifies exact lookup, structured lookup, and search. | No | Additive runtime behavior is covered without changing `par`/`art`. |
| 5 | Add DSGVO full-count gate evidence. | `scripts/verify_dsgvo_full_counts.py` validates strict package schema, expected article/recital counts, source metadata, content hash, and boundary IDs. | No | Fixture test uses reduced counts intentionally; live parser smoke provides official-source evidence for 99/173 parser capability. |
| 6 | Document DSGVO article and recital citation units. | Not re-reviewed in depth because this round focused on the Critical parser rework and relevant code/tests. | No blocking deviation found | Documentation was covered in the prior review; no new functional issue found in the rework scope. |

## Code Quality Assessment

### Findings

- No functional or technical findings.

The parser change is small and root-cause oriented: `_is_recital_element()` now accepts official Formex `CONSID` elements while retaining reduced-fixture `RECITAL` support, and `_recital_value()` derives stable values from Formex number elements before falling back to text matching. Existing article extraction is unchanged, and generated-package validation remains strict because `recital` is an explicit supported unit rather than a catch-all relaxation.

## Testing Assessment

### Verify Command Result

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_dsgvo_full_counts.py mcp/tests/test_normalizer_eurlex.py`
- **Exit Code**: 0
- **Result**: 10 passed

- **Command**: direct parser smoke against `https://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0004.02/DOC_2`
- **Exit Code**: 0
- **Result**: `articles 99 recitals 173`, boundaries present: `art:1`, `art:99`, `recital:1`, `recital:173`

- **Command**: simulated old-recital-shape check against `mcp/tests/fixtures/eurlex_dsgvo/dsgvo_articles_recitals.xml`
- **Exit Code**: 0
- **Result**: old `<RECITAL>`-only detection saw `old_recital_tag_count 0`; current parser emitted `['art:1', 'art:99', 'recital:1', 'recital:173']`

- **Command**: `validate_dsgvo_full_counts()` against the reduced generated fixture package with adjusted 2/2 policy counts
- **Exit Code**: 0
- **Result**: `validation_errors []`, counts `{'articles': 2, 'recitals': 2}`

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: User-provided evidence: 127 passed, HTTP CLI E2E OK, MCP streamable HTTP E2E OK

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `mcp/tests/test_dsgvo_full_counts.py::test_eurlex_parser_extracts_articles_and_formex_considerations_as_first_class_norms` | Parses reduced official-shaped `<GR.CONSID>/<CONSID>/<NP>/<NO.P>/<TXT>` fixture and expects `art:1`, `art:99`, `recital:1`, `recital:173`. | Yes | No issue. This would fail against the previous `<RECITAL>`-only implementation because the fixture contains zero `<RECITAL>` recital records. |
| `mcp/tests/test_dsgvo_full_counts.py::test_eurlex_parser_preserves_reduced_recital_fixture_support` | Confirms legacy reduced `<RECITAL>` fixture support remains available. | Yes | No issue; this guards compatibility without replacing the official-shape test. |
| `mcp/tests/test_dsgvo_full_counts.py::test_recital_resolver_and_search_are_additive` | Verifies exact `recital:*` lookup, structured `unit="recital"` resolution, label formatting, and search indexing. | Yes | No issue. |
| `mcp/tests/test_dsgvo_full_counts.py::test_generated_dsgvo_fixture_package_passes_strict_validation` | Runs generated-package validation on the DSGVO fixture package with article and recital units. | Yes | No issue. |
| `mcp/tests/test_dsgvo_full_counts.py` mismatch tests | Confirm the full-count gate rejects wrong Cellar work and expression metadata. | Yes | No issue. |
| `mcp/tests/test_normalizer_eurlex.py` | Confirms old article parser behavior and DOC_2 guard behavior remain intact. | Yes | No issue. |

### Real-World Testing

Performed during review. I fetched the official DSGVO German Cellar DOC_2 XML and ran `parse_dsgvo_xml()` against it in a temporary directory. The parser returned 99 article norms and 173 recital norms, with `art:1`, `art:99`, `recital:1`, and `recital:173` present.

## Scope Compliance

### Findings

- No out-of-scope code, docs, plan, or test modifications were made during this review.
- The rework stays within the Phase 5 EUR-Lex/Cellar DSGVO parser, fixture, resolver/search, and generated-package validation scope.
- The generated full-count gate remains explicit and package-based; fast fixture tests do not fabricate a 99/173 generated package.

## Regression Risk

### Test Integrity Check

- [x] No existing tests were deleted in the inspected Phase 5 scope.
- [x] No existing tests were disabled.
- [x] No existing assertions were weakened in the inspected Phase 5 scope.
- [x] All targeted pre-existing article/parser tests still pass.

### Findings

- No regression findings. Article extraction still uses the same `<ARTICLE>` traversal and identifier/title extraction path, resolver support for `recital` is additive, and strict package validation still rejects unsupported units while accepting the Phase 2 generated unit set.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| - | - | - | No findings. | None. |

## Recommendations

1. Accept the Phase 5 rework.
2. Keep the direct live DOC_2 smoke output or a generated full-count artifact as release evidence when closing Phase 5, since fast CI appropriately remains fixture-backed.
