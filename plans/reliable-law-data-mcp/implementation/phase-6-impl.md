---
type: planning
entity: implementation-plan
plan: "reliable-law-data-mcp"
phase: 6
status: draft
created: "2026-05-14"
updated: "2026-05-14"
---

# Implementation Plan: Phase 6 - Search Index and Result Contract

> Implements [Phase 6](../phases/phase-6.md) of [reliable-law-data-mcp](../plan.md)

## Approach

Phase 6 adds a transport-independent search service over Phase 4 normalized records, using Phase 3 registry resolution for selected-law filters and the shared dataset readiness model. It must return `SearchResult` JSON-compatible objects with plain-text snippets, canonical law/norm metadata, source provenance, stable URLs, and normalized deterministic scores. It must not expose SQLite FTS markup, silently return empty success for invalid queries, or reuse legacy Markdown search behavior as the public contract.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| `mcp/legal_texts/search.py` | create | Search query normalization, normalized-record indexing, scoring, snippets, selected-law filtering, and result/error construction. |
| `mcp/legal_texts/dataset.py` | modify | Expose iterable normalized norms/laws and search-index readiness inputs. |
| `mcp/legal_texts/models.py` | modify | Finalize `SearchResult` model and shared search configuration constants if needed. |
| `mcp/legal_texts/errors.py` | modify | Add/verify `INVALID_QUERY` and reuse registry/dataset structured errors. |
| `mcp/legal_texts/validation.py` | modify | Validate `stage="serving_dataset"` once a search index exists and keep pre-index pending behavior intact. |
| `mcp/tests/test_search.py` | create | Search service tests for all-law search, filtered search, invalid queries, snippets, scores, and readiness. |
| `mcp/tests/golden/search/` | create/modify | Golden search responses and error payloads for fixture-backed terms. |
| `docs/features/law-loading-and-indexing.md` | modify/reference | Document normalized search service boundary and legacy search limitations. |

## Required Context

| File | Why |
|------|-----|
| `plans/reliable-law-data-mcp/plan.md` | Global search, structured error, source metadata, and no-demo-source requirements. |
| `plans/reliable-law-data-mcp/phases/phase-6.md` | Gated Phase 6 scope and acceptance criteria. |
| `plans/reliable-law-data-mcp/contracts.md` | `SearchResult`, `INVALID_QUERY`, readiness, snippet, score, and tie-break contracts. |
| `plans/reliable-law-data-mcp/fixture-inventory.md` | Required laws/norms whose text fixtures must be searchable. |
| `plans/reliable-law-data-mcp/implementation/phase-3-impl.md` | Registry behavior for selected-law filter resolution and ambiguity semantics. |
| `plans/reliable-law-data-mcp/implementation/phase-4-impl.md` | Normalized records, fixture package layout, and readiness stages consumed by search. |
| `plans/reliable-law-data-mcp/implementation/phase-5-impl.md` | Dataset lookup conventions and golden JSON patterns shared by service layers. |
| `mcp/legal_texts/data/laws.v1.json` | Committed law metadata and aliases used for selected-law filter tests. |
| `mcp/tests/fixtures/normalized/` | Normalized fixture package used to build the search index. |
| `mcp/parser.py` | Legacy `LawLibrary.search` regression anchor for HTML snippets, swallowed errors, and URL construction. |
| `mcp/server.py` | Runtime boundary: MCP tool migration is deferred to Phase 7. |
| `mcp/tests/conftest.py` | Existing pytest fixture style. |

## Search Contract

`search_laws(query, codes=None)` must:

- normalize `query` by Unicode normalization, trimming, casefolding, and collapsing internal whitespace;
- tokenize normalized queries into Unicode word tokens and use unique query tokens in first-seen order;
- require every unique query token to appear in the indexed title/text token stream for a norm to match;
- return `INVALID_QUERY` for empty normalized queries, punctuation-only queries that produce no tokens, or backend-unsafe input that cannot be converted into safe search tokens;
- resolve every optional `codes` entry through the registry before search, collapse duplicates by canonical law ID, and preserve `LAW_NOT_FOUND` / `AMBIGUOUS_LAW_ALIAS` errors;
- build/search an index from normalized `NormRecord` text-bearing records, not from legacy Markdown `LawParser` objects;
- exclude structural container records from text hits unless they contain explicit text;
- return results shaped as `SearchResult` with `law_id`, `law_display_code`, `law_display_name`, `norm_id`, `canonical_id`, `title`, plain-text `snippet`, `source`, `url`, and normalized `score`;
- omit `highlight` by default; if added later, it must be a separate field and must not replace `snippet`;
- calculate raw score as the sum of occurrence counts for all unique query tokens, normalize public score as `raw_score / top_raw_score` rounded to 6 decimal places, return at most 20 results by default, and sort by score descending, then canonical law ID ascending, then norm ID ascending for ties;
- return `DATASET_NOT_READY` if the normalized dataset or search index is missing/invalid.

## Implementation Steps

### Step 1: Define Search Models and Configuration

- **What**: Add or finalize `SearchResult`, search query normalization helpers, snippet length, max result count, and public score formula.
- **Where**: `mcp/legal_texts/models.py` and `mcp/legal_texts/search.py`.
- **Why**: Search output and tests need one stable shape independent of backend internals.
- **Considerations**: Use the deterministic public score formula from `contracts.md`: unique query tokens in first-seen order, AND match semantics, raw score from token occurrence counts, public score normalized by the top raw score and rounded to 6 decimal places, default snippet length of 240 characters, and default result limit of 20. If using SQLite FTS5 internally, do not expose raw rank and instead map results to this public score contract.

### Step 2: Build Search Index from Normalized Dataset

- **What**: Implement a search index builder that consumes normalized laws and norms from the dataset loader.
- **Where**: `mcp/legal_texts/search.py` and `mcp/legal_texts/dataset.py`.
- **Why**: Search must use validated normalized data and preserve source metadata and stable URLs from `NormRecord`.
- **Considerations**: Index `title` plus full `text` for text-bearing norms. Do not index fabricated EGBGB container text. Keep canonical law and norm IDs in the index row so results never infer URLs from display codes.

### Step 3: Implement Query Validation and Tokenization

- **What**: Normalize and validate user queries before executing search.
- **Where**: `mcp/legal_texts/search.py`.
- **Why**: Empty and unsafe queries must produce `INVALID_QUERY`, not silent empty results or backend exceptions.
- **Considerations**: Treat the public query language as plain text in Phase 1. Tokenize with Unicode word tokens; punctuation-only input is invalid because it produces no query tokens. Do not pass raw user query syntax directly into SQLite FTS `MATCH` if FTS5 is used; tokenize or quote safely. Tests must cover whitespace-only input, punctuation-only input, multi-token AND semantics, and at least one FTS-special-character input that previously could trigger `sqlite3.OperationalError`.

### Step 4: Resolve Selected Law Filters Through Registry

- **What**: Resolve optional `codes` filters to canonical law IDs before searching.
- **Where**: `mcp/legal_texts/search.py` and `mcp/legal_texts/registry.py`.
- **Why**: Selected-law search must use the same alias and ambiguity behavior as resolver/MCP/HTTP paths.
- **Considerations**: Tests should cover canonical IDs, aliases such as `UWG`, `TTDSG`, `pangv`, and `DSGVO`, duplicate filters, unknown law errors, and synthetic ambiguity through the Phase 3 non-validating registry test path.

### Step 5: Generate Plain-Text Snippets

- **What**: Produce bounded plain-text snippets around the first deterministic match.
- **Where**: `mcp/legal_texts/search.py`.
- **Why**: API contracts must not contain backend-specific HTML fragments such as `<b>` in `snippet`.
- **Considerations**: Collapse internal whitespace for snippets, preserve enough legal text to identify the hit, anchor the snippet at the earliest occurrence of the first matched query token in query order, cap length at 240 characters with ASCII `...` truncation, and test that `<b>`, `</b>`, and raw HTML tags are absent from default snippets.

### Step 6: Score and Sort Deterministically

- **What**: Normalize raw search relevance into public `score` values and sort with tie-breakers.
- **Where**: `mcp/legal_texts/search.py`.
- **Why**: Search tests must be stable across local environments and backend upgrades.
- **Considerations**: Top result score must be `1.0`; lower scores must remain in `[0.0, 1.0]`. Tests should assert AND semantics for multi-token queries, occurrence-count score normalization, score range, top score, and a tie-break fixture sorted by `law_id` then `norm_id`, not raw backend rank internals.

### Step 7: Validate Serving Dataset Readiness

- **What**: Extend readiness validation so `stage="serving_dataset"` can become `ready` once normalized dataset and search index are valid.
- **Where**: `mcp/legal_texts/validation.py`, `mcp/legal_texts/dataset.py`, and `mcp/legal_texts/search.py`.
- **Why**: Phase 6 is the first phase where the serving dataset can have a valid search index.
- **Considerations**: Preserve Phase 4 behavior where serving readiness before search index creation reports pending/missing search index details. Missing or corrupt search index state must return `DATASET_NOT_READY`.

### Step 8: Write Search Goldens and Regression Tests

- **What**: Add fixture-backed search goldens for representative all-law and filtered queries plus error payloads.
- **Where**: `mcp/tests/test_search.py` and `mcp/tests/golden/search/`.
- **Why**: Later MCP and HTTP search tests should compare against the same service-level contract.
- **Considerations**: Include terms from required fixtures such as cancellation/withdrawal BGB text, DDG provider/imprint text, UWG advertising text, PAngV price text, and DSGVO data-subject/security terms where fixture wording supports stable hits. Include regression coverage for legacy `<b>` snippets and swallowed query syntax errors.

### Step 9: Document Search Service Boundary

- **What**: Document that normalized search is a shared service consumed by future MCP/HTTP phases and that legacy `LawLibrary.search` remains only until Phase 7 migration removes the demo tool surface.
- **Where**: `docs/features/law-loading-and-indexing.md` and `docs/modules/mcp-server.md` if module inventory needs updating.
- **Why**: Documentation should not claim new MCP search behavior before Phase 7.
- **Considerations**: Keep advanced semantic search, embeddings, and legal evaluation as non-goals.

## Testing Plan

Primary verify command:

```bash
PYTHONPATH=mcp python3 -m pytest mcp/tests/test_search.py mcp/tests/test_resolver.py mcp/tests/test_normalizer_gii.py mcp/tests/test_normalizer_eurlex.py mcp/tests/test_dataset_validation.py mcp/tests/test_registry.py mcp/tests/test_source_import.py mcp/tests/test_source_matrix.py mcp/tests/test_parser.py mcp/tests/test_library.py
```

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Search index build | Build index from `mcp/tests/fixtures/normalized/`. | Text-bearing normalized norms are indexed with canonical IDs, URLs, source metadata, and law display fields. |
| All-law search | Query representative legal terms across the normalized fixture package. | Results include matches across laws, sorted by score and tie-break rules. |
| Multi-token search semantics | Query terms that appear together in one fixture and separately across other fixtures. | Only norms containing every unique query token match; scoring follows occurrence counts. |
| Selected-law search | Filter by aliases and canonical IDs such as `UWG`, `uwg_2004`, `TTDSG`, `pangv`, and `DSGVO`. | Filters resolve to canonical law IDs; duplicate filters are harmless; invalid aliases return registry errors. |
| Search result contract | Every result contains `law_id`, display fields, `norm_id`, `canonical_id`, `title`, `snippet`, `source`, `url`, and `score`. | JSON matches `SearchResult`; no double-serialized strings. |
| Snippet safety | Default snippets for fixture hits. | Snippets are plain text, bounded to 240 characters with ASCII `...` truncation, and contain no `<b>` or backend HTML fragments. |
| Score determinism | Multiple-hit and tie-break fixtures. | Top score is `1.0`, all scores are in `[0.0, 1.0]`, scores are rounded to 6 decimal places, and tie order is stable. |
| Query errors | Whitespace-only, punctuation-only, and backend-special-character queries. | `INVALID_QUERY` structured errors when no safe tokens exist; backend syntax never leaks to clients. |
| Dataset readiness | Missing/invalid normalized dataset or missing/corrupt search index. | `DATASET_NOT_READY` structured errors; serving readiness reports correctly. |
| Existing prior-phase tests | Import, registry, normalizer, resolver, and legacy parser/library tests. | Earlier behavior remains passing. |

### Test Integrity Constraints

- Do not disable, skip, xfail, delete, or weaken Phase 2-5 tests or existing legacy parser/library tests to make search tests pass.
- Existing `mcp/tests/test_library.py` may keep covering legacy `LawLibrary.search` until Phase 7; new search tests must assert normalized service behavior instead of mutating legacy expectations prematurely.
- Search goldens must assert public score shape and deterministic ordering, not backend-private raw score values.

## Rollback Strategy

Remove `mcp/legal_texts/search.py`, search model/error/readiness additions if unused by later phases, `mcp/tests/test_search.py`, search golden fixtures, and search documentation updates. Phase 2-5 import, registry, normalization, and resolver artifacts remain intact.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Search backend | simple deterministic token index / SQLite FTS5 / external engine | simple deterministic token index first, SQLite FTS5 only if needed | Phase 1 needs stable fixture-backed search and safe plain-text contracts more than backend-specific ranking. |
| Public query language | raw FTS syntax / plain text / advanced boolean syntax | plain text | Prevents backend syntax leakage and keeps query errors controllable. |
| Invalid query code | reuse `INVALID_CITATION` / add `INVALID_QUERY` / return empty results | `INVALID_QUERY` | Search has a non-citation bad-input path and must not return silent empty success. |
| Snippet highlighting | inline HTML / separate highlight field / no default highlight | no default highlight | Default contract requires plain-text snippets; optional highlighting can be modeled later. |
| Container records | index all containers / exclude textless containers / aggregate child text | exclude textless containers | Avoids fabricated aggregate text, especially for EGBGB `Art. 246a`. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/parser.py` | `LawLibrary.__init__` FTS table | Current search index is built from Markdown paragraphs, not normalized records. |
| `mcp/parser.py` | `LawLibrary.search` | Current snippets use `<b>` tags, errors are printed then returned as empty lists, and URLs are inferred from display code. |
| `mcp/server.py` | `search_laws` MCP tool | MCP tool migration is intentionally deferred to Phase 7. |
| `plans/reliable-law-data-mcp/contracts.md` | `SearchResult`, error codes, readiness, and search determinism | Defines public search response behavior. |
| `plans/reliable-law-data-mcp/implementation/phase-4-impl.md` | normalized records and serving readiness boundary | Search must consume normalized package output and complete serving readiness. |
| `plans/reliable-law-data-mcp/implementation/phase-5-impl.md` | dataset loader conventions | Search should reuse the same dataset service patterns as resolver. |

### Mismatches / Notes

- The current repository has only legacy Markdown search; Phase 6 adds a new normalized search service rather than refactoring `LawLibrary.search` in place.
- The existing `search_laws` MCP tool returns JSON strings and remains unchanged until Phase 7.
- The shared contract was updated during this phase to add `INVALID_QUERY` because the previously approved error set had no semantically correct search-query validation code.
