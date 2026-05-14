---
type: review
entity: plan-review
plan: "reliable-law-data-mcp"
status: final
reviewer: "general"
created: "2026-05-14"
---

# Plan Review: reliable-law-data-mcp

> Reviewing [reliable-law-data-mcp](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The plan has a sensible high-level phase sequence and covers the major product surfaces for a Phase 1 legal-text MCP. It is not yet reliable enough to execute without drift because source-path validation, concrete fixture inventory, dataset readiness semantics, and canonical norm identifier grammar are either deferred too late or left as implementation decisions.

## Requirement Coverage

| Requirement | Covered By | Gap? | Notes |
| ----------- | ---------- | ---- | ----- |
| Replace productive `bundestag/gesetze` dependence with `gesetze-im-internet.de` | Phases 2, 9 | Partial | Covered directionally, but no phase requires validating every required official source path before implementation. |
| Reproducible import with download, snapshots, hashing, manifest, URL, retrieval timestamp, stand date, content hash | Phases 1, 2, 4 | Partial | Manifest fields are covered, but exact source URL matrix and stand-date extraction rules are not required acceptance artifacts. |
| Keep raw source data separate from normalized data | Phases 1, 2, 4 | No | Clearly covered. |
| Document supported law set, including DSGVO as EUR-Lex or separate | Phases 1, 2, 3, 9 | Partial | Law list is present, but exact real source path/URL validation is missing and TDDDG path handling appears inconsistent with the current official path. |
| Versioned alias registry | Phase 3 | Partial | Registry exists in scope, but ambiguous/current-vs-historical TDDDG/TTDSG path semantics need a concrete source-path truth table. |
| Include canonical ID, display name, source metadata, stable URL in responses | Phases 1, 4, 5, 7, 8 | Partial | Response inclusion is stated; canonical norm URL/ID grammar is not pinned down. |
| Normalize laws, containers, sections/articles, subdivisions, headings, full text, URL, source metadata, stand date, hash | Phases 1, 4 | Partial | Structure levels are listed, but acceptance does not define required parser behavior for EGBGB article-plus-section patterns, repealed ranges, or unavailable subdivisions. |
| Implement `resolve_citation(...)` with structured JSON, suggestions, machine-readable errors | Phase 5 | Partial | Resolver behavior is covered, but canonical input/output grammar for mixed `§`/`Art.` cases is incomplete. |
| Search loaded laws or selected subset with norm ID, title, snippet, URL, score, optional non-HTML highlighting | Phase 6 | Partial | Contract is covered, but scoring/snippet determinism criteria are weak. |
| Stable MCP tools and real JSON objects | Phase 7 | Partial | Tool names and JSON-object requirement are covered; legacy tool migration choice remains open. |
| HTTP API and OpenAPI | Phase 8 | No | Covered. |
| Import validation for required fields, duplicates, alias collisions, URLs, readiness, hash changes | Phases 2, 3, 4, 8, 9 | Partial | Validation categories are present, but readiness ownership is late and source-path validation is not concrete enough. |
| Structured error codes | Phases 1, 5, 6, 7, 8, 9 | Partial | Codes are listed, but transport mappings and required payload fields are not fully owned before implementation. |
| Startup fail-fast for missing/invalid dataset | Phases 8, 9 | Gap | Top-level NFR is not clearly owned by the data-loading/MCP phases before HTTP arrives. |
| Reproducible/auditable imports from manifests | Phase 2 | Partial | Covered, but real-source verification inputs need to be explicit. |
| Deterministic parser/resolver independent of LLM behavior | Phases 4, 5 | No | Covered. |
| Stable API contracts for MCP, HTTP tests, future integrations | Phases 1, 7, 8 | Partial | Intended, but identifier/error details are too open. |
| Passing, deployable state after each phase | All phases | Partial | Phase boundaries are mostly sequential, but several phases defer validation to Phase 9. |
| No SaaS/billing/user/tenant scope | Plan, Phases 1, 6, 8, 9 | No | Covered. |

## Scope Clarity

### Findings

- The plan clearly excludes SaaS/productization and legal reasoning, but source support is not concrete enough: the law inventory does not require a verified table of official source URLs, source paths, downloadable formats, expected HTTP status, and source-kind handling for every Phase 1 law.
- DSGVO separation is in scope, but the plan does not specify the exact EUR-Lex representation to import or normalize, such as CELEX/ELI URL, language, consolidated-vs-OJ choice, or how GDPR article fixtures enter the same resolver contract as German laws.
- The old MCP tool migration is left as "removal or compatibility handling", which is too open for a phase intended to deliver a stable Phase 1 MCP surface.

## Definition of Done Assessment

### Findings

- The DoD says required norms resolve from a fixture list, but the fixture list is not fully concrete. `BDSG relevant DSGVO supplements` and DSGVO itself do not name exact norms/articles, expected URLs, or subdivision cases.
- The DoD requires startup from a validated dataset, but no earlier phase acceptance criterion creates a single dataset readiness contract that both MCP startup and HTTP `/ready` must use.
- The DoD requires imports and manifests to include source metadata, but it does not require a pre-implementation source validation pass against the current official source URLs.

## Phase Structure Assessment

| Phase | Title | Verdict | Issue |
| ----- | ----- | ------- | ----- |
| 1 | Domain Contracts and Dataset Layout | Revise | Should also produce a verified source matrix and exact norm/citation identifier grammar; otherwise later phases invent contracts. |
| 2 | Reproducible Source Import | Revise | Import acceptance should require live-source/path validation for every Phase 1 law, not just fixtures or "real source snapshots". |
| 3 | Canonical Registry and Alias Resolution | Revise | Registry depends on source paths, but the plan contains a likely incorrect `tddsg` path; source-path validation should block registry completion. |
| 4 | Structured Normalization and Validation | Revise | Should own dataset-package validation/readiness before resolver, search, MCP, and HTTP phases consume data. |
| 5 | Citation Resolver | Revise | Needs a shared canonical citation grammar for `§`, `Art.`, article-plus-section patterns, suffixes, and ranges. |
| 6 | Search Index and Result Contract | Minor revise | Snippet and score determinism are stated but not objectively bounded. |
| 7 | MCP Tool API Migration | Revise | MCP readiness/error behavior and legacy-tool migration choice need to be fixed before implementation. |
| 8 | HTTP API and OpenAPI | OK with dependency fix | Thin HTTP layer is appropriate, but readiness semantics should not originate here. |
| 9 | Fixture Coverage, Docs, and Release Gate | Revise | Too much first-time fixture completeness and source verification risk is deferred to the final gate. |

## Testing Strategy Assessment

### Test Coverage Gaps

- No explicit source-probe test matrix requires current official URLs to return expected status and downloadable XML/HTML for each German law, or an expected EUR-Lex source for DSGVO.
- Golden citation fixtures are incomplete for DSGVO and underspecified for BDSG. The current wording can pass while leaving major source/law coverage untested.
- There is no shared conformance suite that runs the same required citations through normalized data, resolver service, MCP tools, and HTTP endpoints before the release gate.
- Readiness and startup-fail-fast behavior are not tied to concrete tests in the early data phases or MCP phase.
- Search score and snippet determinism are not defined tightly enough for stable regression tests across local environments.

### Real-World Testing

Real-world/source validation is partially planned but insufficient. The plan mentions real imports and source documentation, but it does not require a phase-gated live validation of the official source surface. Spot checks on 2026-05-14 show official `gesetze-im-internet.de` index pages expose XML downloads for required laws such as [BGB](https://www.gesetze-im-internet.de/bgb/index.html) and [TDDDG](https://www.gesetze-im-internet.de/ttdsg/index.html), while `https://www.gesetze-im-internet.de/tddsg/index.html` returns 404. The plan also needs a fixed EUR-Lex source decision for [Regulation (EU) 2016/679](https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679), including language and consolidated/OJ handling.

## Reference Consistency

### Findings

- The plan and Phase 3 refer to TDDDG / TTDSG / `tddsg`, but the current official `gesetze-im-internet.de` path observed for TDDDG is `/ttdsg/`; `/tddsg/` does not resolve. This is a source-reference inconsistency with direct implementation impact.
- PAngV is listed as `PAngV`, but the official source path observed in search results is `/pangv_2022/`; the plan should require path-level source validation for all laws instead of relying on display abbreviations.
- EGBGB source paths use `/bgbeg/`, which is not obvious from the display abbreviation and should be explicitly captured in the registry/source matrix.

## Completeness Check

### Findings

- A developer can start implementing from the phase docs, but several decisions that affect persisted data contracts are left implicit: norm ID grammar, URL canonicalization, source path truth table, dataset readiness state model, and exact fixture inventory.
- The plan does not define how known upstream issues are represented in machine-readable data beyond saying they are "known-issue-capable"; without a schema, this can drift between import, validation, and API responses.
- Phase 9 is overloaded as a final catch-all for fixtures, docs, and release gating; it should verify completeness, not discover source support and fixture gaps for the first time.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Source validation | The plan lacks a required verified source matrix, and current spot checks already show a likely bad TDDDG path: `/tddsg/` returns 404 while `/ttdsg/` resolves. | Add a Phase 1/2 acceptance artifact listing each law's canonical ID, display code, official source path, index URL, XML URL, expected status, source kind, stand-date extraction rule, and source validation result. Make registry/import validation fail on mismatches. |
| 2 | Major | Fixture coverage | The required fixture inventory is incomplete for DSGVO and underspecified for BDSG, so Phase 1 can pass without proving all required laws resolve. | In Phase 1, enumerate exact citations for every required law, including DSGVO articles and concrete BDSG sections, with expected source URLs, source kind, subdivisions, and golden JSON ownership. |
| 3 | Major | Phase boundaries | Dataset readiness and startup fail-fast are top-level requirements but not owned before the transport phases, risking MCP behavior that serves invalid or missing data. | Add a Phase 4 readiness/dataset package contract and Phase 7 MCP acceptance tests for missing/invalid dataset, `DATASET_NOT_READY`, and `SOURCE_UNAVAILABLE`. |
| 4 | Major | Identifier contracts | Canonical norm IDs and citation grammar are not specified enough for `§`, `Art.`, suffixes, EGBGB article-plus-section references, repealed ranges, and HTTP `{norm}` encoding. | Define a shared grammar and examples in Phase 1, then require Phases 4, 5, 7, and 8 to use the same conformance fixtures. |
| 5 | Major | Error contracts | Error codes are listed, but payload fields and transport mappings are not fixed early enough for consistent resolver, search, MCP, and HTTP behavior. | Add a structured error schema with required fields, HTTP status mapping, MCP return shape, suggestion limits, and examples for every error code. |
| 6 | Minor | MCP migration | Phase 7 leaves legacy tool behavior open as either removal or compatibility handling. | Decide in the contract phase whether old tool names are removed, aliased, or deprecated, and test that only the chosen surface is exposed. |
| 7 | Minor | Search determinism | Search snippets and scores are only "deterministic enough", which is weak for regression tests. | Specify tokenizer/query normalization, snippet length, score ordering/tie-breaking, and fixture expectations for stable environments. |

## Recommendations

1. Revise Phase 1 to add two contract artifacts before implementation: a verified source matrix and a canonical citation/norm identifier grammar.
2. Move source probing and complete fixture inventory from the final gate into early phase acceptance, with Phase 9 only re-verifying them.
3. Assign dataset readiness and startup fail-fast behavior to the data layer before MCP/HTTP transports consume it.
4. Tighten structured error and MCP migration contracts so clients see one stable Phase 1 API surface.
