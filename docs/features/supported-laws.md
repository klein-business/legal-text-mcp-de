---
type: documentation
entity: feature
feature: "supported-laws"
version: 1.1
---

# Feature: supported-laws

> Part of [legal-text-mcp-de](../overview.md)

## Summary

Phase 1 supports the legal-audit fixture set defined in [fixture-inventory.md](../../plans/reliable-law-data-mcp/fixture-inventory.md). It is not a claim of complete German-law coverage.

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

The committed fixture dataset covers the required Phase 1 legal-audit citations, including BGB `§ 312`, `§ 355`, `§ 309`; EGBGB `Art. 246a` and `Art. 246a § 1`; DDG `§ 5`; UWG `§ 3`, `§ 5`, `§ 5a`, `§ 5b`, `§ 7`; TDDDG `§ 25`, `§ 26`; selected BDSG provisions; BFSG `§ 1`; VSBG `§ 36`; PAngV `§ 1`, `§ 4`, `§ 5`; and DSGVO Articles 5, 6, 12, 13, 14, 15, 17, 21, 25, 32, and 82.
