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

**Verdict**: Needs Rework

The implementation preserves existing article behavior, adds additive `recital:*` resolver support, documents the explicit full-count gate, and keeps the default release gate fixture-backed. However, the new recital parser is keyed to a fixture-only `<RECITAL>` shape while the official DSGVO Cellar DOC_2 Formex XML currently represents recitals as `<CONSID>` records under `<GR.CONSID>`. A direct parser smoke check against the official DOC_2 URL produced 99 articles and 0 recitals, so the core Phase 5 recital acceptance criterion is not met.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | DSGVO articles 1-99 resolve in generated corpus checks. | Partial | `parse_dsgvo_xml()` still parses official `<ARTICLE>` records; live parser smoke check against the official DOC_2 URL returned `articles 99`. Fixture release tests passed. | No committed full package is required by scope, but the checked generated artifact under `.artifacts/dsgvo/full-counts.json` is reduced fixture evidence with 2 articles, not a 99-article generated proof. |
| 2 | DSGVO recitals 1-173 resolve as citation units. | No | `mcp/legal_texts/eurlex_xml.py:41` only iterates tags whose local name is `RECITAL`; `mcp/tests/fixtures/eurlex_dsgvo/dsgvo_articles_recitals.xml:5` uses synthetic `<RECITAL>` elements. The official DOC_2 smoke check returned `recitals 0`. | Parser must support official Formex `<CONSID><NP><NO.P>...</NO.P>...` recitals and tests must use that shape. |
| 3 | DSGVO source metadata records CELEX, Cellar expression, document, language, version/consolidation policy, and content hash. | Yes | `mcp/tests/fixtures/eurlex_dsgvo/source_policy.json:3` pins CELEX, language, Cellar work/expression/document, version/consolidation policy, content hash, and expected counts. `scripts/verify_dsgvo_full_counts.py:52` validates those fields. | No blocking gap found. |
| 4 | Existing selected DSGVO article behavior remains backwards compatible. | Yes | `mcp/tests/test_normalizer_eurlex.py` passed; `mcp/legal_texts/eurlex_xml.py:17` keeps the existing article path; release verification passed with 126 tests plus HTTP and MCP E2E. | No blocking gap found. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Record DSGVO Cellar version policy. | Added `source_policy.json` and full-count script metadata checks. | No | Satisfies the policy-record portion. |
| 2 | Extend parser for full articles. | Parser handles official `<ARTICLE>` records; live smoke check returned 99 articles. | No | Adequate for articles. |
| 3 | Add recital extraction as first-class norms. | Adds `recital:*` norm emission only for `<RECITAL>` tags. | Yes | Problematic: official DOC_2 recitals are `<CONSID>`, so generated official packages will omit all recitals. |
| 4 | Add resolver and search fixtures. | `resolver.py` accepts exact and structured `recital`; tests exercise resolver and search over fixture recitals. | Partial | Runtime behavior works when recital records exist, but the parser will not produce official recital records. |
| 5 | Add DSGVO full-count gate evidence. | `verify_dsgvo_full_counts.py` validates generated package counts, boundary IDs, metadata, and content hash; local artifact is reduced fixture evidence. | Partial | Gate is opt-in as intended, but the implementation has no passing proof from an official-parser-produced full recital package. |
| 6 | Document DSGVO article and recital citation units. | Docs describe `recital:*`, Cellar policy, and explicit full-count gate. | Partial | Documentation is structurally in place, but currently overstates implementation because official recitals are not parsed. |

## Code Quality Assessment

### Findings

- **Critical**: `mcp/legal_texts/eurlex_xml.py:41` only recognizes `<RECITAL>` elements, while the official DSGVO Cellar DOC_2 source uses Formex `<CONSID>` records for recitals. This is a root-cause parsing error, not a missing fixture edge case.

The rest of the Phase 5 changes are narrow and preserve existing patterns. `models.py` adds `recital` unit normalization additively, `resolver.py:11` and `resolver.py:188` add exact parsing and labels without altering `par`/`art` paths, and the release script includes only fast fixture tests rather than the opt-in full-count package gate.

## Testing Assessment

### Verify Command Result

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_dsgvo_full_counts.py mcp/tests/test_normalizer_eurlex.py mcp/tests/test_resolver.py mcp/tests/test_search.py mcp/tests/test_generated_package.py`
- **Exit Code**: 0
- **Result**: 55 passed

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: 126 passed, HTTP CLI E2E OK, MCP streamable HTTP E2E OK

- **Command**: direct parser smoke check against `https://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0004.02/DOC_2`
- **Exit Code**: 0
- **Result**: `articles 99`, `recitals 0`

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `mcp/tests/test_dsgvo_full_counts.py::test_eurlex_parser_extracts_articles_and_recitals_as_first_class_norms` | Parser emits `art:1`, `art:99`, `recital:1`, `recital:173` from reduced XML. | Partially | Fixture uses `<RECITAL>` tags that do not match the official DOC_2 Formex recital structure. |
| `mcp/tests/test_dsgvo_full_counts.py::test_recital_resolver_and_search_are_additive` | Exact and structured recital resolution plus search over generated fixture records. | Yes | Validates runtime behavior only after recitals already exist. |
| `mcp/tests/test_dsgvo_full_counts.py::test_verify_dsgvo_full_counts_script_writes_artifact` | Full-count gate writes artifact and validates metadata/counts. | Partially | Test mutates expected counts to 2/2 for fixture evidence, so it does not prove the parser can generate 173 official recitals. |
| `mcp/tests/test_normalizer_eurlex.py` | Existing DSGVO article parser compatibility. | Yes | No issue for article compatibility. |
| `scripts/verify_release.py` | Default release gate includes fixture tests and E2E, not explicit full-count generation. | Yes | This is the intended CI behavior. |

### Real-World Testing

Performed during review: I fetched the official DSGVO DOC_2 Cellar XML and ran the repository parser against it in a temporary directory. The parser returned all 99 articles but 0 recitals. This confirms the recital gap against the real source and is not just a theoretical fixture concern.

## Scope Compliance

### Findings

- No out-of-scope `dsgvo-gesetz.de` legal text use was found in Phase 5 implementation paths. Repository hits for `dsgvo-gesetz.de` are metadata/policy fixtures and manifest tests from the broader plan, including tests that reject copied/editorial text fields.
- The default release gate remains fixture-backed: `scripts/verify_release.py:11` lists test modules, including `mcp/tests/test_dsgvo_full_counts.py`, but does not invoke `scripts/verify_dsgvo_full_counts.py` against a full package path.
- Full generated corpus artifacts remain outside Git; `.gitignore` excludes `.artifacts/`.

## Regression Risk

### Test Integrity Check

- [x] No existing tests were deleted in the inspected Phase 5 scope.
- [x] No existing tests were disabled.
- [x] No existing assertions were weakened in the inspected Phase 5 scope.
- [x] All pre-existing release-gate tests still pass under `SKIP_LIVE_SOURCE_MATRIX=true`.

### Findings

- The main regression risk is false confidence: fixture and release tests pass while official generated packages would omit every DSGVO recital. Existing `par` and `art` behavior did not show a regression in the commands above.

## Documentation & Cleanup

### Findings

- The docs updates are in the right files and correctly state the intended official-source and opt-in-gate model. They should not be considered complete until the parser and tests match official Formex recitals; otherwise the documentation claims working `recital:*` generated support that the implementation cannot produce from the selected source.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Critical | EUR-Lex Parser | Official DSGVO recitals are not parsed. `parse_dsgvo_xml()` recognizes only `<RECITAL>`, but the selected official Cellar DOC_2 XML uses `<CONSID>` records, and a live parser check returned 0 recitals. | Parse Formex `<GR.CONSID>/<CONSID>` recital records, derive values from `<NO.P>`, emit `recital:<n>` norms, and replace or augment the fixture with official-shaped `<CONSID>` samples covering boundaries 1 and 173. |

## Recommendations

1. Block Phase 5 acceptance until official Formex `<CONSID>` recital parsing is implemented and covered by fixture tests that fail against the current parser.
2. Add a generated-package or temporary official-source smoke test that demonstrates `art:1`, `art:99`, `recital:1`, and `recital:173` are produced from the selected DOC_2 source shape before the opt-in full-count gate is considered meaningful.
3. Re-run `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py` and the explicit DSGVO full-count gate after the parser fix.
