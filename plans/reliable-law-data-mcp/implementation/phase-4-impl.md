---
type: planning
entity: implementation-plan
plan: "reliable-law-data-mcp"
phase: 4
status: draft
created: "2026-05-14"
updated: "2026-05-14"
---

# Implementation Plan: Phase 4 - Structured Normalization and Validation

> Implements [Phase 4](../phases/phase-4.md) of [reliable-law-data-mcp](../plan.md)

## Approach

Phase 4 converts Phase 2 raw snapshots into a normalized dataset package that later resolver, search, MCP, and HTTP layers can consume. The implementation adds source-kind-specific normalizers for `gesetze-im-internet` XML ZIPs and DSGVO Formex act XML, produces `LawRecord`, `NormRecord`, `SubdivisionRecord`, and normalized-dataset readiness records matching `contracts.md`, validates duplicates/required fields/URLs, and writes fixture-backed normalized JSON for the complete Phase 1 citation inventory. Runtime MCP tools still remain on the legacy Markdown parser until Phase 7.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| `mcp/legal_texts/normalizer.py` | create | Coordinates raw snapshot normalization into `data/normalized/{dataset_id}/`. |
| `mcp/legal_texts/gii_xml.py` | create | Parses `gesetze-im-internet.de` XML ZIP artifacts into structured laws, subdivisions, and norms. |
| `mcp/legal_texts/eurlex_xml.py` | create | Parses DSGVO German Formex act XML expression `0004.02` document `DOC_2` into article records with EU provenance. |
| `mcp/legal_texts/validation.py` | create | Required-field, duplicate-ID, URL, source metadata, known-issue, and readiness validation. |
| `mcp/legal_texts/models.py` | modify | Add or finalize normalized law/norm/subdivision/readiness records. |
| `mcp/tests/test_normalizer_gii.py` | create | German XML fixture normalization tests for `§`, `Art.`, subdivisions, URLs, and EGBGB container/child semantics. |
| `mcp/tests/test_normalizer_eurlex.py` | create | DSGVO Formex XML tests for German language, articles, source metadata, and URLs. |
| `mcp/tests/test_dataset_validation.py` | create | Validation tests for duplicates, missing fields, bad URLs, known issues, and readiness states. |
| `mcp/tests/fixtures/normalized/` | create/modify | Minimal normalized records for required Phase 1 fixtures. |
| `mcp/tests/fixtures/raw/` | modify | Add minimal XML fixture extracts if Phase 2 did not already cover all required citations. |
| `docs/features/law-loading-and-indexing.md` | modify | Document normalized dataset output and current runtime boundary. |

## Required Context

| File | Why |
|------|-----|
| `plans/reliable-law-data-mcp/plan.md` | Global normalization, validation, readiness, and fixture requirements. |
| `plans/reliable-law-data-mcp/phases/phase-4.md` | Gated Phase 4 scope and acceptance criteria. |
| `plans/reliable-law-data-mcp/contracts.md` | Norm, subdivision, source metadata, manifest, readiness stage, and error contracts. |
| `plans/reliable-law-data-mcp/fixture-inventory.md` | Required citations and golden-normalized coverage expectations. |
| `plans/reliable-law-data-mcp/source-matrix.md` | Source paths, DSGVO expression `0004.02`, URL/provenance, and invalid-path context. |
| `plans/reliable-law-data-mcp/implementation/phase-2-impl.md` | Raw snapshot, manifest, source metadata, and live probe decisions. |
| `plans/reliable-law-data-mcp/implementation/phase-3-impl.md` | Registry source identity and canonical law ID decisions. |
| `plans/reliable-law-data-mcp/phases/phase-5.md` | Boundary check: resolver consumes normalized records after Phase 4. |
| `plans/reliable-law-data-mcp/phases/phase-6.md` | Boundary check: search index is not present during Phase 4 readiness. |
| `plans/reliable-law-data-mcp/phases/phase-7.md` | Boundary check: MCP runtime migration remains deferred. |
| `docs/overview.md` | Project structure and test command context. |
| `docs/features/law-loading-and-indexing.md` | Current legacy Markdown parser/runtime boundary. |
| `mcp/parser.py` | Current parser limitations and absatz parsing regression anchor. |
| `mcp/server.py` | Current MCP runtime boundary that Phase 4 must not migrate. |
| `mcp/tests/conftest.py` | Existing pytest style and sample fixture approach. |

## XML Structure Anchors

Implementation should verify these source-shape anchors against fixtures or live sample artifacts before coding parser assumptions:

- German `gesetze-im-internet` ZIPs contain at least one XML file with a `<dokumente>` root and repeated `<norm>` elements.
- Law-level metadata appears in the first `<norm>` with `<metadaten>`, `<jurabk>`, `<langue>`, and one or more `<standangabe>` elements.
- Text-bearing German norms may use `<metadaten><enbez>§ 312</enbez><titel ...>...</titel></metadaten>` or article-like `<gliederungseinheit><gliederungsbez>Art 3</gliederungsbez><gliederungstitel>...</gliederungstitel></gliederungseinheit>`.
- Structural subdivisions are also represented as `<gliederungseinheit>` records with empty `<P/>`; these should become structural metadata/containers, not text-bearing norms.
- Norm text is under `<textdaten><text format="XML"><Content>...`.
- Absatz-level text is commonly represented by `<P>(1) ...</P>`; list numbers and letters appear as `<DL Type="arabic"><DT>1.</DT><DD>...` and `<DL Type="alpha"><DT>a)</DT><DD>...`.
- EGBGB uses source path `bgbeg` and source abbreviation `BGBEG`; canonical law ID remains `egbgb`.
- EGBGB `Art. 246a` appears as a separate `<norm>` with `<gliederungseinheit><gliederungsbez>Art 246a</gliederungsbez>` and empty content; child sections appear as later `<norm>` records with the same `gliederungseinheit` plus `<enbez>§ 1</enbez>` and text.
- The public EGBGB container URL `https://www.gesetze-im-internet.de/bgbeg/art_246a.html` returned 404 in source checks; the child URL `https://www.gesetze-im-internet.de/bgbeg/art_246a__1.html` returned 200. Container fixtures must therefore carry explicit known-issue URL metadata unless a stable container URL is verified during execution.
- DSGVO Cellar German expression `0004.02` has metadata/TOC XML in `DOC_1`; article-bearing Formex act XML is `DOC_2`. `DOC_2` must include `<LG.DOC>DE</LG.DOC>`, `<ACT`, and `<ARTICLE IDENTIFIER="005">` style article content. The Dutch `0017.02` expression and German metadata-only `DOC_1` must not be used as article fixtures.

## Normalized Readiness Scope

Phase 4 may emit `stage="normalized_dataset", state="ready"` when raw manifest, registry, normalized laws, normalized norms, source metadata, and validation summary are valid. It must not emit serving readiness for MCP/HTTP. Any `stage="serving_dataset"` check before Phase 6 must report a pending or missing search index through `details.search_index_status="pending"` and must not be treated as serving-ready.

## Implementation Steps

### Step 1: Finalize Normalized Models and Readiness Types

- **What**: Implement or finalize `LawRecord`, `NormRecord`, `SubdivisionRecord`, normalized dataset manifest, validation result, and stage-aware readiness records according to `contracts.md`.
- **Where**: `mcp/legal_texts/models.py`.
- **Why**: Resolver/search/transports need stable normalized records with provenance and readiness state.
- **Considerations**: `text` is required for text-bearing norms; `status="container"` records may omit text but must include children. Preserve `source` metadata and hashes from Phase 2 raw snapshot entries. Readiness records must distinguish normalized-dataset readiness from serving-dataset readiness.

### Step 2: Parse German GII XML ZIP Snapshots

- **What**: Implement a parser that opens XML files from raw GII ZIP artifacts and emits law metadata, structural hierarchy records, `par`/`art` norms, headings, full text, URLs, and initial subdivisions.
- **Where**: `mcp/legal_texts/gii_xml.py` and `mcp/legal_texts/normalizer.py`.
- **Why**: Phase 1 requires structured norms rather than Markdown paragraphs.
- **Considerations**: Use `xml.etree.ElementTree` or `lxml` if already available from dependencies. Text extraction should preserve legal text order and normalize whitespace conservatively. Do not parse assets like GIF/JPG files in EGBGB ZIPs as law text.

### Step 3: Parse DSGVO Formex Act XML Separately

- **What**: Implement a separate DSGVO normalizer that validates German Formex act metadata, extracts required `Art.` fixtures from `DOC_2`, and emits article `NormRecord`s with `eur-lex-cellar` source metadata.
- **Where**: `mcp/legal_texts/eurlex_xml.py` and `mcp/legal_texts/normalizer.py`.
- **Why**: DSGVO provenance and structure differ from German laws and must not be mixed into the GII parser.
- **Considerations**: Require expression `0004.02`, document `DOC_2`, language `DE`, CELEX `32016R0679`, Cellar work ID, XML content type metadata from the raw manifest, `<LG.DOC>DE</LG.DOC>`, `<ACT`, and article nodes such as `<ARTICLE IDENTIFIER="005">`. Reject metadata-only `DOC_1` as an article source. If Formex article extraction is too broad, support at least required fixture articles with deterministic tests and mark unsupported structure as known issue.

### Step 4: Implement EGBGB Article Container and Child Normalization

- **What**: Represent `Art. 246a` as `egbgb/art:246a` with `status="container"` and child references, and represent `Art. 246a § 1` as `egbgb/art:246a/par:1` with text.
- **Where**: `mcp/legal_texts/gii_xml.py`, `mcp/tests/test_normalizer_gii.py`, and `mcp/tests/fixtures/normalized/`.
- **Why**: This is a core resolver/search fixture and prevents fabricated aggregate text.
- **Considerations**: Group child records by shared `gliederungseinheit` under the article container. The source URL for the child should follow verified GII child pages such as `/bgbeg/art_246a__1.html`; the container URL must be represented as a documented known issue if `/bgbeg/art_246a.html` remains 404.

### Step 5: Parse Subdivisions Conservatively

- **What**: Extract Absatz, Satz, Nummer, and Buchstabe records where deterministic, while preserving full norm text even when fine-grained parsing is incomplete.
- **Where**: `mcp/legal_texts/gii_xml.py`, `mcp/legal_texts/eurlex_xml.py`, and tests.
- **Why**: Phase 4 must support structured subdivision lookup without guessing.
- **Considerations**: Absatz detection starts from `<P>(n)` or Formex `<PARAG><NO.PARAG>(n)</NO.PARAG>` boundaries. Satz extraction must be limited to fixture-backed sentences within a selected Absatz and must preserve full Absatz text. Nummer extraction maps GII `<DL Type="arabic"><DT>1.</DT><DD>...` and Formex list item numbers to `nr:{value}`. Buchstabe extraction maps `<DL Type="alpha"><DT>a)</DT><DD>...` and equivalent Formex list items to `lit:{value}`. If nested list or sentence boundaries are unsafe, output the full parent text with `status="known_issue"` and `known_issues=[{"code":"SUBDIVISION_UNPARSED","path":...}]`.

### Step 6: Validate Normalized Dataset Packages

- **What**: Validate required fields, duplicate canonical IDs/norm IDs, URL shape, source metadata, registry alignment, raw-manifest linkage, known-issue documentation, and readiness states.
- **Where**: `mcp/legal_texts/validation.py`.
- **Why**: Later transports must never silently serve invalid or missing data.
- **Considerations**: Produce readiness states `ready`, `missing`, `invalid`, and `source_unavailable` for `stage="normalized_dataset"` as defined in `contracts.md`. Do not report `stage="serving_dataset", state="ready"` until Phase 6 search index validation exists. Validation should fail on duplicate IDs and missing text for active text-bearing norms.

### Step 7: Write Normalized Fixtures and Dataset Package Layout

- **What**: Write normalized JSON fixture records for every required Phase 1 citation and a minimal dataset package under `mcp/tests/fixtures/normalized/`.
- **Where**: `mcp/tests/fixtures/normalized/` and `mcp/tests/fixtures/raw/`.
- **Why**: Phase 5 resolver and Phase 6 search need stable normalized data to build on.
- **Considerations**: Include BGB `§ 312`, `§ 355`, `§ 309`; EGBGB `Art. 246a` and `Art. 246a § 1`; DDG `§ 5`; UWG `§ 3`, `§ 5`, `§ 5a`, `§ 5b`, `§ 7`; TDDDG `§ 25`, `§ 26`; BDSG `§ 1`, `§ 22`, `§ 26`, `§ 34`, `§ 35`; BFSG `§ 1`; VSBG `§ 36`; PAngV `§ 1`, `§ 4`, `§ 5`; and DSGVO `Art. 5`, `Art. 6`, `Art. 12`, `Art. 13`, `Art. 14`, `Art. 15`, `Art. 17`, `Art. 21`, `Art. 25`, `Art. 32`, `Art. 82`. Tests must assert coverage against `fixture-inventory.md`.

### Step 8: Document Normalization Coverage and Known Limits

- **What**: Document parser coverage, known structural limitations, normalized dataset paths, and readiness behavior.
- **Where**: `docs/features/law-loading-and-indexing.md` and `docs/modules/mcp-server.md` if module inventory needs updating.
- **Why**: Users and later implementers need to know which legal structures are safe in Phase 1.
- **Considerations**: Do not claim MCP tools consume normalized data until Phase 7. Document that legacy Markdown parsing remains runtime-only until migration.

## Testing Plan

Primary verify command:

```bash
PYTHONPATH=mcp python3 -m pytest mcp/tests/test_normalizer_gii.py mcp/tests/test_normalizer_eurlex.py mcp/tests/test_dataset_validation.py mcp/tests/test_registry.py mcp/tests/test_source_import.py mcp/tests/test_source_matrix.py mcp/tests/test_parser.py mcp/tests/test_library.py
```

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| German XML normalization | Required GII fixture norms normalize to canonical law IDs, norm IDs, titles, text, URLs, source metadata, stand status, and hashes. | Normalized JSON matches contracts and fixture expectations. |
| EGBGB container/child | `Art. 246a` is a container and `Art. 246a § 1` is text-bearing child `egbgb/art:246a/par:1`. | No fabricated aggregate text; child URL and canonical IDs are stable. |
| End-to-end package generation | Run normalizer coordinator against raw manifest fixtures, write a normalized package, then validate written files and readiness output. | Package contains laws, norms, manifest, validation summary, and `stage="normalized_dataset"` readiness. |
| DSGVO Formex normalization | German expression `0004.02` document `DOC_2` with `<LG.DOC>DE</LG.DOC>`, `<ACT`, and required `<ARTICLE>` nodes emits required article records; metadata-only `DOC_1` and Dutch `0017.02` are rejected as article fixtures. | DSGVO provenance remains `eur-lex-cellar`; required articles normalize. |
| Complete fixture coverage | Every citation row from `fixture-inventory.md`, including all BDSG and DSGVO fixtures, has normalized JSON coverage. | Tests fail on missing fixture IDs. |
| Subdivision parsing | Named fixtures cover `abs`, `satz`, `nr`, `lit`, plus an unsafe nested fixture that must produce a known-issue limitation. | Subdivision paths and text match expected records or known-issue flags. |
| Dataset validation | Missing required fields, duplicate IDs, bad URLs, missing source metadata, and undocumented known issues fail validation. | Validation returns `invalid` with machine-readable details. |
| Readiness states | Missing, invalid, source-unavailable, and normalized-ready dataset packages produce stage-aware readiness states. | No silent empty dataset success; no serving-ready state before Phase 6 search index. |
| Regression coverage | Wrong URL construction and legacy absatz parsing regressions are covered by new normalized tests. | Tests fail on display-code-as-source-path URLs and broken Absatz extraction. |
| Existing prior-phase tests | Source import and registry behavior remain passing. | Earlier tests still pass. |

### Test Integrity Constraints

- Do not disable, skip, xfail, delete, or weaken Phase 2 live-source/source-metadata expectations, Phase 3 alias registry tests, or existing legacy parser/library tests to make Phase 4 pass.
- Existing legacy parser/library tests may remain unchanged; new normalization tests should capture the replacement behavior rather than mutating legacy tests prematurely.
- If a subdivision cannot be parsed safely, tests must require a known-issue flag plus full norm text, not accept guessed text.

## Rollback Strategy

Remove `mcp/legal_texts/normalizer.py`, `gii_xml.py`, `eurlex_xml.py`, `validation.py`, normalized fixture outputs, and Phase 4 tests/docs. Phase 2 raw import and Phase 3 registry artifacts should remain intact.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| XML parser | `xml.etree.ElementTree` / `lxml` / BeautifulSoup | `xml.etree.ElementTree` first, `lxml` only if needed | Standard-library first keeps runtime small; `lxml` is available in preparation deps if needed later. |
| Fine-grained Satz parsing | full grammar now / fixture-driven conservative parser / defer entirely | fixture-driven conservative parser | Supports required fixtures without overclaiming ambiguous structure. |
| DSGVO source | German Cellar `0004.02` `DOC_2` / metadata-only `DOC_1` / EUR-Lex `TXT` / Dutch Cellar `0017.02` | German Cellar `0004.02` `DOC_2` | Verified as machine-readable German article XML; avoids WAF challenge, metadata-only TOC, and wrong-language fixture. |
| Runtime consumption | switch MCP now / write normalized package only / dual runtime | write normalized package only | Phase 7 owns runtime and MCP migration. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/parser.py` | `LawParser.PARAGRAPH_RE` and `LawParser.ABSATZ_RE` | Current Markdown parser cannot parse official XML, articles, or reliable subdivisions. |
| `mcp/parser.py` | `LawLibrary.get` and URL construction | Current URLs derive from display code and fail for source-path mismatches such as EGBGB. |
| `plans/reliable-law-data-mcp/source-matrix.md` | GII and DSGVO rows | Normalizers must preserve source-kind-specific provenance and correct source paths. |
| `plans/reliable-law-data-mcp/contracts.md` | `NormRecord`, `SubdivisionRecord`, and readiness contracts | These define required normalized output and validation states. |
| `/tmp` source inspection on 2026-05-14 | GII XML and DSGVO Formex sample structure | Confirmed GII `<norm>`/`<metadaten>`/`<Content>` shape, EGBGB container/child shape, and DSGVO German Cellar expression `0004.02` with article content in `DOC_2`. |

### Mismatches / Notes

- The existing repository has no XML normalizer; Phase 4 is a new data layer, not a refactor of `LawParser`.
- Official GII XML may encode article-like norms in `<gliederungseinheit>` rather than `<enbez>`; implementation must handle both text-bearing and structural records.
- DSGVO Formex parsing is source-kind-specific and should not be forced through the German XML normalizer. `DOC_1` is metadata/TOC; article extraction must use `DOC_2`.
- Runtime startup may still ignore normalized packages until Phase 7; this phase must produce and validate them for later consumers.
