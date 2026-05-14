---
type: planning
entity: source-matrix
plan: "reliable-law-data-mcp"
created: "2026-05-14"
updated: "2026-05-14"
---

# Source Matrix: reliable-law-data-mcp

> Supports [reliable-law-data-mcp](plan.md)

This matrix fixes the Phase 1 source truth table that import, registry, validation, resolver, MCP, and HTTP work must use. Status values below were probe-checked on 2026-05-14 and must be re-validated by the import tests before implementation is considered complete.

## German Laws: gesetze-im-internet.de

| Canonical ID | Display Code | Required Aliases | Source Kind | Source Path | Index URL | XML ZIP URL | Probe Result | Notes |
|--------------|--------------|------------------|-------------|-------------|-----------|-------------|--------------|-------|
| `bgb` | BGB | `BGB`, `bgb`, `Buergerliches Gesetzbuch`, `Bürgerliches Gesetzbuch` | `gesetze-im-internet` | `bgb` | `https://www.gesetze-im-internet.de/bgb/index.html` | `https://www.gesetze-im-internet.de/bgb/xml.zip` | index 200, xml.zip 200 | Primary German-law fixture source. |
| `egbgb` | EGBGB | `EGBGB`, `BGBEG`, `bgbeg`, `Einführungsgesetz zum Bürgerlichen Gesetzbuche` | `gesetze-im-internet` | `bgbeg` | `https://www.gesetze-im-internet.de/bgbeg/index.html` | `https://www.gesetze-im-internet.de/bgbeg/xml.zip` | index 200, xml.zip 200 | Source path differs from display abbreviation. |
| `ddg` | DDG | `DDG`, `ddg`, `Digitale-Dienste-Gesetz` | `gesetze-im-internet` | `ddg` | `https://www.gesetze-im-internet.de/ddg/index.html` | `https://www.gesetze-im-internet.de/ddg/xml.zip` | index 200, xml.zip 200 | Phase 1 imprint/contact fixture source. |
| `uwg_2004` | UWG | `UWG`, `uwg_2004`, `Gesetz gegen den unlauteren Wettbewerb` | `gesetze-im-internet` | `uwg_2004` | `https://www.gesetze-im-internet.de/uwg_2004/index.html` | `https://www.gesetze-im-internet.de/uwg_2004/xml.zip` | index 200, xml.zip 200 | Canonical ID keeps official source-path suffix. |
| `tdddg` | TDDDG | `TDDDG`, `TTDSG`, `ttdsg`, `tddsg`, `Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz` | `gesetze-im-internet` | `ttdsg` | `https://www.gesetze-im-internet.de/ttdsg/index.html` | `https://www.gesetze-im-internet.de/ttdsg/xml.zip` | index 200, xml.zip 200 | Current display law is TDDDG, but official source path remains `ttdsg`. `https://www.gesetze-im-internet.de/tddsg/index.html` probe returned 404 and must stay a regression case. |
| `bdsg_2018` | BDSG | `BDSG`, `bdsg_2018`, `Bundesdatenschutzgesetz` | `gesetze-im-internet` | `bdsg_2018` | `https://www.gesetze-im-internet.de/bdsg_2018/index.html` | `https://www.gesetze-im-internet.de/bdsg_2018/xml.zip` | index 200, xml.zip 200 | Canonical ID keeps official source-path suffix. |
| `bfsg` | BFSG | `BFSG`, `bfsg`, `Barrierefreiheitsstärkungsgesetz`, `Barrierefreiheitsstaerkungsgesetz` | `gesetze-im-internet` | `bfsg` | `https://www.gesetze-im-internet.de/bfsg/index.html` | `https://www.gesetze-im-internet.de/bfsg/xml.zip` | index 200, xml.zip 200 | Accessibility fixture source. |
| `vsbg` | VSBG | `VSBG`, `vsbg`, `Verbraucherstreitbeilegungsgesetz` | `gesetze-im-internet` | `vsbg` | `https://www.gesetze-im-internet.de/vsbg/index.html` | `https://www.gesetze-im-internet.de/vsbg/xml.zip` | index 200, xml.zip 200 | Consumer dispute fixture source. |
| `pangv_2022` | PAngV | `PAngV`, `pangv`, `pangv_2022`, `Preisangabenverordnung` | `gesetze-im-internet` | `pangv_2022` | `https://www.gesetze-im-internet.de/pangv_2022/index.html` | `https://www.gesetze-im-internet.de/pangv_2022/xml.zip` | index 200, xml.zip 200 | `https://www.gesetze-im-internet.de/pangv/index.html` probe returned 404 and must stay a regression case. |

## EU Law: EUR-Lex

| Canonical ID | Display Code | Required Aliases | Source Kind | Source Identifier | Source URL | Probe Result | Notes |
|--------------|--------------|------------------|-------------|-------------------|------------|--------------|-------|
| `dsgvo_eu_2016_679` | DSGVO | `DSGVO`, `GDPR`, `Datenschutz-Grundverordnung`, `Verordnung (EU) 2016/679` | `eur-lex-cellar` | CELEX `32016R0679`, Cellar work `3e485e15-11bd-11e6-ba9a-01aa75ed71a1`, expression `0004.02`, language `DE`, German act XML `DOC_2` | `https://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0004.02/DOC_2` | HTTP 200, `application/xml;type=fmx4;charset=UTF-8`, `<LG.DOC>DE</LG.DOC>`, `<ACT`, and article content on 2026-05-14 probe | Phase 1 treats DSGVO as a separate official Publications Office / Cellar XML source. It must not be stored as a `gesetze-im-internet` law. `DOC_1` at `https://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0004.02/DOC_1` is German metadata/TOC with `REF.PHYS`, not article text; import may store it as auxiliary metadata but must normalize articles from `DOC_2`. The human-facing EUR-Lex page `https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679` is reference-only because it returned an HTTP 202 challenge in this environment. The similarly retrievable expression `0017.02` is Dutch (`NL`) and must not be used for German fixtures. |

## Source Validation Requirements

- Import validation must probe each German law index URL and XML ZIP URL before accepting a new snapshot.
- DSGVO validation must probe the Cellar act XML URL `DOC_2`, require HTTP 200, require XML content type, require `<LG.DOC>DE</LG.DOC>`, require article-bearing `<ACT` content, and record CELEX, Cellar work ID, expression, language, retrieved URL, and content hash. If `DOC_1` is also stored, it must be marked as auxiliary metadata/TOC and not used as article text.
- Registry validation must fail if a registry source path conflicts with this matrix.
- Known invalid paths `tddsg` and `pangv` must be captured as regression tests so aliases never become source paths accidentally.
- Each snapshot manifest entry must include `canonical_id`, `source_kind`, `source_identifier` or `source_path`, `source_url`, `retrieved_at`, `stand_date` or `stand_date_status`, and content hash.
- `stand_date_status` must be one of `present`, `not_exposed`, or `known_issue`; `known_issue` requires a machine-readable issue note.
