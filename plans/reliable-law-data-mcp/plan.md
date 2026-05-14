---
type: planning
entity: plan
plan: "reliable-law-data-mcp"
status: completed
created: "2026-05-14"
updated: "2026-05-14"
---

# Plan: reliable-law-data-mcp

## Objective

Make the MCP server fachlich verlasslich for loading, normalizing, searching, and referencing legal texts in Phase 1. The target is a local/server-side legal text foundation with stable JSON contracts, reproducible source snapshots, canonical identifiers, structured norms, precise citation resolution, MCP tools, and a small HTTP API.

## Motivation

The current repository is a useful demo server, but it depends on `bundestag/gesetze` demo data, parses only paragraph headings from Markdown, returns stringified JSON from MCP tools, and has limited validation/error contracts. Legal-audit workflows need stable citations, traceable source metadata, deterministic imports, and explicit failure modes before any higher-level legal reasoning or SaaS product work is credible.

## Requirements

### Functional

- [x] Use `gesetze-im-internet.de` as the canonical primary source for German Phase 1 laws; remove productive dependence on `bundestag/gesetze`.
- [x] Provide reproducible data import with download, snapshot storage, hashing, manifest generation, source URL, retrieval timestamp, stand date, and content hash.
- [x] Keep raw source data separate from normalized data.
- [x] Document the Phase 1 supported law set: BGB, EGBGB, DDG, UWG / `uwg_2004`, TDDDG with historical TTDSG aliases and official source path `ttdsg`, BDSG / `bdsg_2018`, BFSG, VSBG, PAngV / `pangv_2022`, and DSGVO as EUR-Lex-sourced or explicitly separate from `gesetze-im-internet.de`.
- [x] Maintain a verified source matrix for every Phase 1 law with canonical ID, display code, aliases, source kind, source path or source identifier, index URL, XML/source URL, expected probe status, and known invalid paths.
- [x] Implement a versioned law alias registry mapping user aliases to canonical IDs, source paths, and display codes.
- [x] Return canonical ID, display name, source metadata, and stable URL in every law/norm/citation response.
- [x] Use a shared canonical law ID, norm ID, citation ID, HTTP norm path, and structured error grammar across import, normalization, resolver, search, MCP, and HTTP.
- [x] Normalize law structure into law, structural containers where available, `§`, `Art.`, Absatz, Satz, Nummer, Buchstabe, heading, full text, URL, source metadata, stand date, and hash.
- [x] Implement `resolve_citation(code, unit, paragraph_or_article, child_unit?, child_value?, absatz?, satz?, nummer?, buchstabe?)` with structured JSON output, controlled suggestions for ambiguous aliases, article-plus-section support, and machine-readable errors for missing norms.
- [x] Search all loaded laws or a selected law subset and return norm ID, title, snippet, URL, score, and optional highlighting without HTML fragments in the default API contract.
- [x] Return search `score` as a normalized API score with deterministic ranking semantics, not raw backend-dependent values.
- [x] Expose stable MCP tools: `list_laws`, `get_law`, `get_norm`, `resolve_citation`, `search_laws`, and `get_source_metadata`.
- [x] Return real JSON objects from MCP tools, not double-serialized JSON strings.
- [x] Expose a small HTTP API with `GET /health`, `GET /ready`, `GET /laws`, `GET /laws/{code}`, `GET /laws/{code}/norms/{norm}`, and `GET /search`.
- [x] Publish OpenAPI for the HTTP API and document API contracts.
- [x] Validate imports for required fields, duplicate IDs, alias collisions, canonical URLs, source readiness, and hash-manifest changes between snapshots.
- [x] Use structured error codes: `LAW_NOT_FOUND`, `NORM_NOT_FOUND`, `AMBIGUOUS_LAW_ALIAS`, `SOURCE_UNAVAILABLE`, `DATASET_NOT_READY`, `INVALID_CITATION`, and `INVALID_QUERY`.
- [x] Use one shared dataset readiness contract for startup, MCP tools, HTTP `/ready`, and tests.

### Non-Functional

- [x] Startup must fail fast when no valid dataset is configured or the configured dataset is invalid.
- [x] Imports must be reproducible and auditable from manifest files.
- [x] Parser and resolver behavior must be deterministic and independent of LLM behavior.
- [x] API contracts must be stable enough for MCP clients, HTTP tests, and future integrations.
- [x] Phase boundaries must keep the repository in a passing, deployable state after each phase.
- [x] No SaaS, billing, user accounts, authorization, tenant isolation, or multi-tenant data segregation in this plan.

## Scope

### In Scope

- Data source replacement from `bundestag/gesetze` demo dependency to reproducible `gesetze-im-internet.de` import for German laws.
- Separate handling/marking for DSGVO as an EUR-Lex source, without mixing it into `gesetze-im-internet.de` metadata.
- Raw and normalized data layout, manifest schema, and source metadata model.
- Source matrix and fixture inventory as plan-owned references: [source-matrix.md](source-matrix.md), [fixture-inventory.md](fixture-inventory.md), and [contracts.md](contracts.md).
- Canonical law IDs and versioned alias registry.
- Structured norm parsing for German laws and enough EU-source representation to avoid misleading DSGVO provenance.
- Citation resolver, search contracts, MCP tool contracts, HTTP API, OpenAPI, validation, and tests.
- Documentation updates for supported laws, data provenance, API contracts, and known source issues.

### Out of Scope

- SaaS productization, billing, subscriptions, tenant isolation, user management, or role-based access control.
- Legal advice, legal evaluation, or hallucination-based fallback logic.
- Broad coverage of every German law beyond the Phase 1 legal-audit set.
- Full historical versioning UI or diff viewer beyond manifest-level change detection.
- Production observability platform, distributed cache, or database operations beyond what Phase 1 needs.
- Any claim that `bundestag/gesetze` is a production source.

## Definition of Done

- [x] The server can start from a validated Phase 1 dataset without relying on `bundestag/gesetze`.
- [x] Runtime defaults and Docker packaging no longer clone or load `bundestag/gesetze` as a production dataset path.
- [x] Raw snapshots, normalized records, and manifests include source URL, retrieval timestamp, stand date when discoverable, hash, and canonical law ID.
- [x] The verified source matrix is implemented and tested, including known invalid source paths `tddsg` and `pangv`.
- [x] The Phase 1 law registry resolves all required aliases and rejects collisions deterministically.
- [x] Required norms from the fixture list resolve to stable structured JSON with URLs and provenance.
- [x] Search returns deterministic JSON objects with norm IDs, snippets, URLs, and scores for all or selected laws.
- [x] MCP tools return typed JSON-compatible objects and expose only the Phase 1 tool names.
- [x] HTTP endpoints and OpenAPI exist and are covered by tests.
- [x] Import validation rejects missing required fields, duplicate IDs, alias collisions, invalid source states, and known bad URL conditions.
- [x] Structured errors are returned consistently across resolver, search, MCP, and HTTP boundaries.
- [x] Dataset readiness uses one shared state model across strict startup, MCP serving, HTTP `/ready`, and diagnostics.
- [x] Unit, parser, golden citation, search, import-validation, error-contract, MCP-tool, HTTP-contract, and regression tests pass.
- [x] Documentation states supported Phase 1 laws, source provenance, API contracts, known issues, and explicit non-goals.

## Testing Strategy

- [x] Unit tests for alias registry mapping, canonical ID resolution, and alias collision detection.
- [x] Parser tests for `§`, `Art.`, Absatz, Satz, Nummer, Buchstabe, headings, full text, and URL construction.
- [x] Golden JSON tests for BGB § 312, § 355, § 309; EGBGB Art. 246a container and Art. 246a § 1 child; DDG § 5; UWG § 3, § 5, § 5a, § 5b, § 7; TDDDG/TTDSG § 25, § 26; BDSG § 1, § 22, § 26, § 34, § 35; BFSG § 1; VSBG § 36; and PAngV §§ 1, 4, 5.
- [x] Golden JSON tests for DSGVO/EUR-Lex Art. 5, 6, 12, 13, 14, 15, 17, 21, 25, 32, and 82.
- [x] Source-probe tests for every entry in [source-matrix.md](source-matrix.md), including expected 404 regression checks for invalid source paths.
- [x] Search tests with stable fixture expectations for all-law and code-filtered searches.
- [x] Import-validation tests for missing fields, duplicate IDs, alias collisions, bad source metadata, and manifest hash changes.
- [x] Error-contract tests for `LAW_NOT_FOUND`, `NORM_NOT_FOUND`, `AMBIGUOUS_LAW_ALIAS`, `SOURCE_UNAVAILABLE`, `DATASET_NOT_READY`, `INVALID_CITATION`, and `INVALID_QUERY`.
- [x] MCP tool tests without a real LLM client.
- [x] HTTP API contract tests, including OpenAPI availability and endpoint response shapes.
- [x] Shared conformance tests that run required citations through normalized data, resolver service, MCP tools, and HTTP endpoints where the transport exists.
- [x] Explicit service, MCP, and HTTP conformance tests for `EGBGB Art. 246a` container and `EGBGB Art. 246a § 1` child request grammar, including HTTP path `art%3A246a%2Fpar%3A1`.
- [x] Regression tests for double JSON serialization, wrong URLs, and incorrect absatz parsing.

## Phases

| Phase | Title | Scope | Status |
|-------|-------|-------|--------|
| 1 | Domain Contracts and Dataset Layout | [Detail](phases/phase-1.md) | completed |
| 2 | Reproducible Source Import | [Detail](phases/phase-2.md) | completed |
| 3 | Canonical Registry and Alias Resolution | [Detail](phases/phase-3.md) | completed |
| 4 | Structured Normalization and Validation | [Detail](phases/phase-4.md) | completed |
| 5 | Citation Resolver | [Detail](phases/phase-5.md) | completed |
| 6 | Search Index and Result Contract | [Detail](phases/phase-6.md) | completed |
| 7 | MCP Tool API Migration | [Detail](phases/phase-7.md) | completed |
| 8 | HTTP API and OpenAPI | [Detail](phases/phase-8.md) | completed |
| 9 | Fixture Coverage, Docs, and Release Gate | [Detail](phases/phase-9.md) | completed |

## Risks & Open Questions

| Risk/Question | Impact | Mitigation/Answer |
|---------------|--------|-------------------|
| `gesetze-im-internet.de` source formats may differ by law or include HTML/XML quirks. | Parser and URL normalization can become brittle. | Phase 2 stores raw snapshots first; Phase 4 normalizes through fixtures and explicit known-issue markers. |
| DSGVO source provenance differs from German laws. | Mixing EUR-Lex with `gesetze-im-internet.de` would make citations misleading. | Treat DSGVO as a separate source kind in registry and metadata; do not import it through the German-law pipeline. |
| Existing parser and server have string-based JSON contracts. | Clients may depend on legacy strings, but Phase 1 requires real JSON objects. | Phase 7 makes a deliberate breaking MCP tool migration with regression tests for double serialization. |
| Absatz/Satz/Nummer/Buchstabe parsing can be ambiguous in real legal text. | Citation resolver could return over-precise but wrong slices. | Start with deterministic fixtures, preserve full norm text, and return structured errors rather than guessed subdivisions when parsing is uncertain. |
| `stand` date availability may vary by source artifact. | Manifest completeness can fail for otherwise useful data. | Treat required vs optional metadata explicitly; import fails for required fields and records known issues for documented source limitations. |
| OpenAPI requires clear HTTP response schemas before implementation stabilizes. | Late schema changes can churn tests and docs. | Phase 1 defines contracts before code; Phase 8 tests endpoint shapes against schemas. |
| Source paths can differ from display abbreviations, as with EGBGB `/bgbeg/`, TDDDG `/ttdsg/`, and PAngV `/pangv_2022/`. | Alias logic may accidentally generate invalid upstream URLs. | Source paths are fixed in [source-matrix.md](source-matrix.md), and invalid aliases/paths become regression tests. |
| Search scores can vary if backend-specific ranking is exposed directly. | Regression tests can become flaky. | [contracts.md](contracts.md) defines query normalization, snippet shape, and tie-breaking rules; backend-specific scores must be normalized or bounded by tests. |
| EUR-Lex human-facing pages may challenge automated clients. | DSGVO imports could fail or become non-reproducible if based on the `TXT` page. | Source matrix uses a directly retrievable official Publications Office / Cellar XML artifact and treats the EUR-Lex `TXT` URL as reference-only. |
| EGBGB Article 246a is a structural container with child `§` entries. | Resolver could invent aggregate text or produce incompatible golden JSON. | [contracts.md](contracts.md) defines article-plus-section IDs and container behavior; [fixture-inventory.md](fixture-inventory.md) requires both container and child fixture coverage. |

## Changelog

### 2026-05-14

- Documentation refreshed after implementation: root README, overview, module docs, feature docs, and release-gate command now describe `legal-text-mcp-de`, the normalized dataset runtime, MCP/HTTP contracts, and Python 3.12 verification.
- Implementation completed and reviewed for Phases 1-9. All implementation review artifacts are final and accepted with no findings; release gate passed with 52 tests.
- Implementation planning gate completed: high-level plan re-reviewed after `INVALID_QUERY`/MCP/HTTP contract additions, Phase 1-9 implementation plans authored and reviewed with no remaining findings, and cross-phase consistency review passed.
- Plan updated after source re-check: corrected DSGVO Cellar expression from Dutch `0017.02` to German `0004.02` and added `<LG.DOC>DE</LG.DOC>` validation to source contracts.
- Plan updated after Phase 4 implementation-plan review: corrected DSGVO article source to German Cellar `DOC_2`, marked `DOC_1` as metadata/TOC only, and split normalized-dataset readiness from serving readiness.
- Plan updated after independent review: added source matrix, fixture inventory, shared contracts, dataset readiness ownership, concrete source-path validation, DSGVO/BDSG fixtures, MCP migration decision, and search determinism rules.
- Plan updated during Phase 6 authoring: added `INVALID_QUERY` as the search-specific structured error for empty or unsafe query input.
- Plan updated after second review: switched DSGVO to a retrievable Cellar XML source artifact, defined EGBGB Art. 246a container/child semantics, assigned runtime dataset migration to Phase 7, and pinned public search score normalization.
- Plan updated after third review: added explicit `child_unit`/`child_value` resolver grammar and encoded HTTP norm path for EGBGB article-plus-section citations.
- Plan created from the Phase 1 reliable legal text MCP requirements.
