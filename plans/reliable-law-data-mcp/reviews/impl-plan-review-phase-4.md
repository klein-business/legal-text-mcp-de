---
type: review
entity: implementation-plan-review
plan: "reliable-law-data-mcp"
phase: 4
status: final
reviewer: "general"
created: "2026-05-14"
---

# Implementation Plan Review: Phase 4 - Structured Normalization and Validation

> Reviewing [Phase 4 Implementation Plan](../implementation/phase-4-impl.md)
> Against [Phase 4 Scope](../phases/phase-4.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The implementation plan is directionally aligned with Phase 4, especially the separation of GII and EUR-Lex normalizers and the EGBGB container/child model. It is not yet executable without guessing because the DSGVO raw-source handoff points at a non-article Formex document, the readiness semantics conflict with the shared contract, and required fixture/subdivision coverage is underspecified.

## Scope Alignment

### Findings

- Phase 4 scope requires normalized fixture artifacts for the Phase 1 citation list, but Step 7 only says "selected BDSG fixtures" instead of the required BDSG par:1, par:22, par:26, par:34, and par:35 from `fixture-inventory.md`.
- Phase 4 scope requires dataset readiness state production, but the plan does not reconcile that with `contracts.md`, where `ready` requires a valid search index that Phase 6 owns.

## Technical Feasibility

### Findings

- DSGVO extraction is currently not feasible from the source artifact named by the source matrix and Phase 2 handoff. A live check on 2026-05-14 showed `...0004.02/DOC_1` is a German Formex metadata/TOC document with `<LG.DOC>DE</LG.DOC>` and a physical reference, while the actual `<ACT>` with `<ARTICLE IDENTIFIER="005">`, `<TI.ART>`, `<STI.ART>`, and `<PARAG>` content is in `...0004.02/DOC_2`. Phase 4 Step 3 says to extract required articles from the German Cellar XML but does not require following `DOC_1` to the act XML or requiring Phase 2 to import `DOC_2`.
- The EGBGB `Art 246a` model is correct, but the plan should be more explicit about the source pattern. A live GII ZIP check showed the container appears as a `<norm>` with `<gliederungsbez>Art 246a</gliederungsbez>` and empty `<Content/>`, while child sections are later `<norm>` records with the same `gliederungseinheit` plus `<enbez>§ 1</enbez>`. The child URL `https://www.gesetze-im-internet.de/bgbeg/art_246a__1.html` returns 200, while `art_246a.html` returns 404 and must be a known issue for the container if no canonical public URL exists.
- Subdivision normalization is technically plausible from GII XML (`<P>(n)</P>` and nested `<DL Type="arabic|alpha"><DT>...` structures), but the plan does not define enough deterministic mapping rules for nested `DL` content, sentence splitting, or limitation flags to prevent over-parsing.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Finalize Normalized Models and Readiness Types | Yes | Partial | Needs an explicit phase-scoped readiness rule because contract-level `ready` currently depends on Phase 6 search index output. |
| 2 | Parse German GII XML ZIP Snapshots | Partial | Partial | Identifies XML anchors, but does not specify canonical URL construction for `par`, `art`, repealed/empty records, and article-plus-section child pages across required laws. |
| 3 | Parse DSGVO Formex XML Separately | No | No | Points at expression `0004.02` but not the actual act XML document (`DOC_2`) that contains articles; `DOC_1` alone cannot satisfy DSGVO article fixtures. |
| 4 | Implement EGBGB Article Container and Child Normalization | Yes | Partial | Correct target IDs and child URL, but must require the parser to group same-`gliederungseinheit` child records under the container and mark missing container URL explicitly. |
| 5 | Parse Subdivisions Conservatively | Partial | Partial | Does not name fixture cases that must exercise Absatz, Satz, Nummer, and Buchstabe, nor the exact known-issue shape when parsing is incomplete. |
| 6 | Validate Normalized Dataset Packages | Partial | Partial | Required validation categories are good, but readiness validation is ambiguous because search index validation is impossible in Phase 4. |
| 7 | Write Normalized Fixtures and Dataset Package Layout | Partial | Partial | Required fixture list is incomplete for BDSG and does not explicitly require every `fixture-inventory.md` row to be present in normalized JSON. |
| 8 | Document Normalization Coverage and Known Limits | Yes | Yes | Appropriate, provided it documents the runtime boundary and parser limitations discovered during implementation. |

## Required Context Assessment

### Missing Context

- `plans/reliable-law-data-mcp/phases/phase-5.md`, `phase-6.md`, and `phase-7.md` should be listed for boundary checks only. Phase 4 must produce data that later resolver/search/MCP layers consume, and the implementer needs to know which runtime behavior remains deferred.
- `mcp/server.py` should be listed as a boundary anchor. The plan says runtime MCP tools remain legacy until Phase 7, and this is the current tool surface that must not be accidentally migrated in Phase 4.

## Testing Plan Assessment

### Test Integrity Check

The plan includes useful constraints not to weaken Phase 2 source tests, Phase 3 registry tests, or legacy parser/library tests. However, it does not explicitly say existing tests must not be disabled or loosened, and it does not distinguish which existing tests are expected to remain behaviorally unchanged versus which new tests supersede legacy parser behavior.

### Test Gaps

- The primary verify command can become meaningful, but only if the new tests run an end-to-end path from raw manifest/snapshot fixtures through normalization, output package writing, validation, and readiness. The current plan's test descriptions allow isolated parser tests that would miss broken dataset package generation.
- DSGVO tests must include a real fixture that proves articles are extracted from the act XML document, not merely that `DOC_1` contains `<LG.DOC>DE</LG.DOC>`.
- GII tests must assert all required normalized fixture IDs from `fixture-inventory.md`, including every BDSG fixture and the known invalid source-path regressions that affect URL/source metadata.
- Subdivision tests should pin at least one deterministic fixture for each required kind: `abs`, `satz`, `nr`, and `lit`, plus one fixture where the expected result is full text with a structured limitation flag.

### Real-World Testing

Real-world source inspection is partially planned through Phase 2 live probes, but Phase 4 does not include its own real-world or fixture-fidelity gate for parsing representative GII and DSGVO artifacts. Because Phase 4 is a parser/normalizer phase, mocked unit tests alone are not enough; the verify path should include committed raw XML extracts copied from the real GII ZIP/Formex act structures, and the implementation notes should record the source URLs and retrieval dates used to create them.

## Reference Consistency

### Findings

- `mcp/legal_texts/*` and Phase 2/3 test files are future phase outputs, so their absence in the current repository is not a Phase 4 review finding.
- Existing code anchors are valid: `mcp/parser.py` is a Markdown-only parser, `LawLibrary.get` builds URLs from `law.short_title.lower()`, and the current runtime still exposes legacy behavior through `mcp/server.py`.
- The DSGVO source reference is internally inconsistent for Phase 4 normalization: `source-matrix.md` names `DOC_1`, but the article-bearing Formex act XML needed by Step 3 is `DOC_2`.

## Reality Check Validation

### Findings

- The Reality Check correctly identifies that the existing repository has no XML normalizer and that Phase 4 is a new data layer, not a refactor of `LawParser`.
- The Reality Check is incomplete on DSGVO: it says sample inspection confirmed the German Cellar expression `0004.02`, but it does not record that `DOC_1` is not the article-bearing act XML.
- The Reality Check should include the EGBGB `Art 246a` source-shape detail that child records are separate `<norm>` entries with the same `gliederungseinheit` and their own `<enbez>` values.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Critical | DSGVO normalization | The plan does not identify the article-bearing DSGVO Formex document. `DOC_1` is metadata/TOC XML; required DSGVO articles are in `DOC_2`. | Update Phase 4 implementation plan to require parsing `DOC_2` or following the `DOC_1` physical reference, and align this with Phase 2 raw manifest expectations before implementation. |
| 2 | Major | Dataset readiness | Phase 4 says it will produce `ready`, but `contracts.md` defines `ready` as including a valid search index owned by Phase 6. | Define Phase 4 readiness as normalized-dataset readiness with search-index status explicitly pending, or revise the shared contract/state model so Phase 4 cannot falsely emit serving-ready packages. |
| 3 | Major | Fixture coverage | Step 7 does not require all fixture inventory records, specifically all BDSG required fixtures. | Replace "selected BDSG fixtures" with the exact required fixture list and require tests to assert complete normalized coverage for every inventory row. |
| 4 | Major | Subdivision coverage | Absatz, Satz, Nummer, and Buchstabe extraction is too underspecified to implement safely and test deterministically. | Add concrete XML-to-subdivision mapping rules, named fixture cases for each kind, and the exact limitation/known-issue output shape when parsing is unsafe. |
| 5 | Major | Verify command | The verify command may pass without proving raw snapshot to normalized package generation, validation, and readiness behavior. | Require end-to-end fixture tests that invoke the normalizer coordinator on raw manifest fixtures and validate written normalized package files plus readiness output. |
| 6 | Minor | Test integrity | The plan does not explicitly forbid disabling or weakening existing tests, although it implies preserving prior-phase behavior. | Add a direct test-integrity statement that existing Phase 2/3 and legacy parser/library tests remain enabled and behaviorally unchanged unless a genuine requirement change is documented. |
| 7 | Minor | EGBGB URL metadata | The EGBGB container has no resolving public page in the checked source, while the child URL resolves; the plan only says the container URL should be present if verified or marked known issue. | Make the expected container known-issue metadata explicit in the fixtures and validation tests if no stable container URL is available. |

## Recommendations

1. Fix the DSGVO source handoff first: specify `DOC_2` article parsing or a deterministic `DOC_1` to act-document resolution rule, and update tests to reject article extraction from metadata-only XML.
2. Resolve Phase 4 readiness semantics before implementation so validators cannot mark a dataset serving-ready before the Phase 6 search index exists.
3. Tighten fixture and subdivision test coverage to enumerate every required citation and every required subdivision kind.
4. Strengthen the primary verify command by requiring an end-to-end normalizer run from raw fixtures to written normalized package and readiness output.
