---
type: planning
entity: fixture-inventory
plan: "reliable-law-data-mcp"
created: "2026-05-14"
updated: "2026-05-14"
---

# Fixture Inventory: reliable-law-data-mcp

> Supports [reliable-law-data-mcp](plan.md)

These fixtures are the minimum Phase 1 conformance set. Each listed citation must eventually have raw-source coverage, normalized JSON, resolver golden JSON, search coverage where text search is relevant, MCP response coverage, and HTTP coverage where the endpoint exists.

## Required Citation Fixtures

| Canonical ID | Display Code | Citation Fixtures | Required Coverage Notes |
|--------------|--------------|-------------------|-------------------------|
| `bgb` | BGB | `§ 312`, `§ 355`, `§ 309` | Consumer contract and cancellation examples; include Absatz and Nummer parsing where present. |
| `egbgb` | EGBGB | `Art. 246a` container, `Art. 246a § 1` text-bearing child fixture | `Art. 246a` is a structural article container in the official source; resolver must not invent text for it. `Art. 246a § 1` is the required text-bearing golden fixture and must exercise article-plus-section grammar and URL encoding. |
| `ddg` | DDG | `§ 5` | Provider/imprint fixture; must include stable source URL. |
| `uwg_2004` | UWG | `§ 3`, `§ 5`, `§ 5a`, `§ 5b`, `§ 7` | Must exercise suffix norms and advertising/unfair-practice search terms. |
| `tdddg` | TDDDG | `§ 25`, `§ 26` | Must resolve through aliases `TDDDG`, `TTDSG`, `ttdsg`, and `tddsg`, while source path remains `ttdsg`. |
| `bdsg_2018` | BDSG | `§ 1`, `§ 22`, `§ 26`, `§ 34`, `§ 35` | Concrete DSGVO supplement fixtures for scope, special categories, employment data, and data-subject-right restrictions. |
| `bfsg` | BFSG | `§ 1` | Accessibility-scope fixture. |
| `vsbg` | VSBG | `§ 36` | Consumer dispute information-duty fixture. |
| `pangv_2022` | PAngV | `§ 1`, `§ 4`, `§ 5` | Price indication fixtures; aliases `PAngV` and `pangv` must resolve to canonical `pangv_2022`. |
| `dsgvo_eu_2016_679` | DSGVO | `Art. 5`, `Art. 6`, `Art. 12`, `Art. 13`, `Art. 14`, `Art. 15`, `Art. 17`, `Art. 21`, `Art. 25`, `Art. 32`, `Art. 82` | Separate EUR-Lex fixtures for principles, lawful basis, transparency, data-subject rights, privacy by design, security, and damages. |

## Golden JSON Requirements

- Every fixture must have a golden JSON response for service-level citation resolution.
- Transport-level MCP and HTTP tests must compare response shape and key metadata against the same fixture inventory.
- Golden JSON must include canonical law ID, display code, source kind, source URL, norm ID, citation label, title when available, text, subdivision fields when requested, and content/source hash when available.
- If a subdivision cannot be extracted deterministically, the golden JSON must preserve the full norm text and include a structured limitation flag instead of guessing.
- Structural container fixtures such as EGBGB `Art. 246a` must return container metadata and child references, not aggregated child text, unless a later registry version explicitly changes that behavior.
- EGBGB child fixture tests must cover structured resolver fields `unit="art"`, `paragraph_or_article="246a"`, `child_unit="par"`, `child_value="1"`, MCP parameters with the same names, and HTTP norm path `art%3A246a%2Fpar%3A1`.

## Regression Fixtures

- `tddsg` alias resolves to canonical `tdddg`, but source path `tddsg` is invalid and must never be used for import.
- `pangv` alias resolves to canonical `pangv_2022`, but source path `pangv` is invalid and must never be used for import.
- MCP tool responses must not double-serialize JSON.
- URLs for EGBGB article norms must use the verified source path `bgbeg`.
