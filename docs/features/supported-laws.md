---
type: documentation
entity: feature
feature: "supported-laws"
version: 1.5
---

# Feature: supported-laws

> Part of [legal-text-mcp-de](../overview.md)

## Summary

The committed fixture scope is represented by the legal-audit fixture set under
`mcp/tests/fixtures/`. Generated production corpus scope is broader and is
proved by explicit artifacts, not by committing generated data to Git.

## Canonical IDs

| Canonical ID | Display Code | Source Kind | Source Identifier |
| ------------ | ------------ | ----------- | ----------------- |
| `bgb` | BGB | `gesetze-im-internet` | `bgb` |
| `egbgb` | EGBGB | `gesetze-im-internet` | `bgbeg` |
| `ddg` | DDG | `gesetze-im-internet` | `ddg` |
| `uwg_2004` | UWG | `gesetze-im-internet` | `uwg_2004` |
| `tdddg` | TDDDG | `gesetze-im-internet` | `ttdsg` |
| `bdsg_2018` | BDSG | `gesetze-im-internet` | `bdsg_2018` |
| `bfsg` | BFSG | `gesetze-im-internet` | `bfsg` |
| `vsbg` | VSBG | `gesetze-im-internet` | `vsbg` |
| `pangv_2022` | PAngV | `gesetze-im-internet` | `pangv_2022` |
| `dsgvo_eu_2016_679` | DSGVO | `eur-lex-cellar` | `CELEX:32016R0679` |

## Alias Rules

- `UWG`, `uwg_2004`, and `Gesetz gegen den unlauteren Wettbewerb` resolve to `uwg_2004`.
- `TDDDG`, `TTDSG`, `ttdsg`, and `tddsg` resolve to `tdddg`; only `ttdsg` is the upstream source path.
- `BDSG` and `bdsg_2018` resolve to `bdsg_2018`.
- `PAngV`, `pangv`, and `pangv_2022` resolve to `pangv_2022`; only `pangv_2022` is the upstream source path.
- DSGVO aliases resolve to `dsgvo_eu_2016_679` and keep EUR-Lex/Cellar provenance.

## Fixture Coverage

The committed fixture dataset covers the required legal-audit citations, including BGB `§ 312`, `§ 355`, `§ 309`; EGBGB `Art. 246a` and `Art. 246a § 1`; DDG `§ 5`; UWG `§ 3`, `§ 5`, `§ 5a`, `§ 5b`, `§ 7`; TDDDG `§ 25`, `§ 26`; selected BDSG provisions; BFSG `§ 1`; VSBG `§ 36`; PAngV `§ 1`, `§ 4`, `§ 5`; and DSGVO Articles 5, 6, 12, 13, 14, 15, 17, 21, 25, 32, and 82.

Generated DSGVO packages can represent official EUR-Lex/Cellar articles and
recitals. The source policy fixture pins CELEX `32016R0679`, German expression
`0004.02`, document `DOC_2`, selected version/consolidation policy, expected
`article_count=99`, and expected `recital_count=173`. Fast tests use reduced
fixtures; full generated packages are checked with the explicit DSGVO
full-count gate.

## Generated Full Corpus Scope

Generated full-corpus packages expand beyond the fixture set:

- GII discovery starts from every reachable official `gii-toc.xml` item and
  records one terminal state per discovered source.
- Imported GII laws and norms remain source-backed by official
  `gesetze-im-internet.de` provenance.
- DSGVO generated packages represent Articles 1-99 and Recitals 1-173 as
  first-class citation units from official EUR-Lex/Cellar provenance.
- EU neighbor acts start from approved CELEX seeds. AI Act `32024R1689` and
  Data Act `32023R2854` are the required minimum seed set.
- German state privacy-law coverage requires all 16 state outcomes as imported
  records or accepted source limitations.
- Relationship metadata links official records and source limitations; it is
  not a separate legal-text source family.

## Critical GII Gate

Generated GII fixture gates treat BDSG and TDDDG as critical privacy laws.
Passing evidence requires imported, resolvable GII records with canonical IDs
`bdsg_2018` and `tdddg`, runtime/MCP/HTTP resolution evidence from the
generated GII package, and preserved upstream source paths such as `ttdsg` in
provenance. A release-blocking upstream `source_unavailable` limitation can
satisfy the gate; reachable `parse_failed` or `unsupported_format` outcomes do
not.
