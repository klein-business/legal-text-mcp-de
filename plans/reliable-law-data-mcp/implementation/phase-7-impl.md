---
type: planning
entity: implementation-plan
plan: "reliable-law-data-mcp"
phase: 7
status: draft
created: "2026-05-14"
updated: "2026-05-14"
---

# Implementation Plan: Phase 7 - MCP Tool API Migration

> Implements [Phase 7](../phases/phase-7.md) of [reliable-law-data-mcp](../plan.md)

## Approach

Phase 7 replaces the legacy demo MCP surface with the stable Phase 1 tools backed by the registry, normalized dataset, resolver, search service, and source metadata records created in earlier phases. The implementation should introduce a small runtime composition layer for validated dataset loading, register only the Phase 1 MCP tools, return JSON-compatible dictionaries directly, and migrate container/runtime defaults away from `/app/gesetze/` and `bundestag/gesetze`.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| `mcp/server.py` | rewrite/modify | Register Phase 1 MCP tools, compose services, return dict objects, and remove stable registrations for `get_lawlibrary` and `get_paragraph`. |
| `mcp/config.py` | modify | Replace legacy Markdown source defaults with dataset package settings and strict startup behavior. |
| `mcp/legal_texts/runtime.py` | create | Load settings, registry, normalized dataset, resolver, search index, and readiness into one runtime object for tools/tests. |
| `mcp/legal_texts/dataset.py` | modify | Expose law lists, norm summaries, source metadata, canonical norm-path lookup, and readiness errors used by MCP tools. |
| `mcp/legal_texts/resolver.py` | modify/reference | Provide `get_norm`/canonical norm-path wrapper behavior or helpers for MCP `get_norm`. |
| `mcp/legal_texts/search.py` | modify/reference | Provide MCP-compatible search response container with canonical filter metadata. |
| `mcp/legal_texts/errors.py` | modify/reference | Provide a single structured-error-to-dict path for MCP tools. |
| `mcp/tests/test_mcp_tools.py` | create | MCP tool tests without a real LLM client for tool names, JSON objects, errors, and EGBGB child parameters. |
| `Dockerfile` | modify | Stop cloning `bundestag/gesetze`; package server code and expect a validated dataset path. |
| `docs/features/mcp-law-tools.md` | modify | Document stable Phase 1 MCP tools and response contracts. |
| `docs/modules/mcp-server.md` | modify | Update module inventory for runtime/data-service based MCP server. |

## Required Context

| File | Why |
|------|-----|
| `plans/reliable-law-data-mcp/plan.md` | Global MCP tool, no-demo-source, startup, and JSON-object requirements. |
| `plans/reliable-law-data-mcp/phases/phase-7.md` | Gated Phase 7 scope and acceptance criteria. |
| `plans/reliable-law-data-mcp/contracts.md` | MCP tool response contracts, error payloads, dataset readiness, norm path grammar, and MCP migration decision. |
| `plans/reliable-law-data-mcp/implementation/phase-3-impl.md` | Registry and alias behavior consumed by all code-bearing tools. |
| `plans/reliable-law-data-mcp/implementation/phase-5-impl.md` | Resolver and `CitationResponse` behavior for `get_norm` and `resolve_citation`. |
| `plans/reliable-law-data-mcp/implementation/phase-6-impl.md` | Search service behavior for `search_laws`. |
| `mcp/server.py` | Current tool registration, import-time loading, string returns, and old demo tool names. |
| `mcp/config.py` | Current defaults to `/app/gesetze/` and legacy source options. |
| `Dockerfile` | Current production image clones `bundestag/gesetze`. |
| `mcp/tests/fixtures/normalized/` | Test dataset package for MCP tool tests. |
| `mcp/tests/conftest.py` | Existing pytest fixture style. |
| `docs/features/mcp-law-tools.md` | Existing documentation of legacy tool surface and known limitations. |
| `docs/modules/mcp-server.md` | Existing module inventory and runtime data-flow documentation. |

## MCP Runtime Contract

The stable MCP surface contains only:

- `list_laws(query: str | None = None)`;
- `get_law(code: str)`;
- `get_norm(code: str, norm: str)`;
- `resolve_citation(code: str, unit: str, paragraph_or_article: str, child_unit: str | None = None, child_value: str | None = None, absatz: str | None = None, satz: str | None = None, nummer: str | None = None, buchstabe: str | None = None)`;
- `search_laws(query: str, codes: list[str] | None = None)`;
- `get_source_metadata(code: str | None = None)`.

Tool handlers must return dictionaries/lists/numbers/strings directly, never `json.dumps(...)` output. Structured failures return the shared `{"error": ...}` object shape. `get_lawlibrary` and `get_paragraph` must not be registered as stable MCP tools after this phase.

`get_norm(code, norm)` is a bounded convenience wrapper. It may parse canonical norm paths such as `par:312`, `art:5`, and `art:246a/par:1`, plus simple `§ 312` and `Art. 5` shorthands. It must reject ranges or free-form prose with `INVALID_CITATION` and must not implement broad LLM-style citation parsing.

## Implementation Steps

### Step 1: Replace Runtime Configuration Defaults

- **What**: Add dataset-oriented settings `dataset_path` from `DATASET_PATH`, `strict_startup` from `STRICT_STARTUP`, plus host/port/debug if needed, preserve `min_paragraphs` for legacy parser/library tests, and remove `/app/gesetze/` as a default serving path.
- **Where**: `mcp/config.py`.
- **Why**: Runtime must start from a validated normalized dataset package, not cloned Markdown demo data.
- **Considerations**: Keep environment variable compatibility simple and explicit. `DATASET_PATH` is the only production dataset path setting for MCP serving. `MIN_PARAGRAPHS` may stay because `mcp/parser.py` tests still patch it. `LOAD_FROM_FOLDER` and `LOAD_FROM_GITHUB` may remain only as unsupported legacy settings if needed for parser/library tests, but they must not be production defaults or server startup paths.

### Step 2: Add Runtime Composition Layer

- **What**: Create a runtime object that loads registry, dataset, resolver, search index, source metadata access, and readiness at startup.
- **Where**: `mcp/legal_texts/runtime.py`.
- **Why**: MCP tools should delegate to shared services and tests need a way to inject fixture datasets without importing a globally broken server.
- **Considerations**: In strict mode, startup fails fast unless readiness is `stage="serving_dataset", state="ready"` because MCP tools need resolver data and search index data. In test/diagnostic mode, tool handlers may return `DATASET_NOT_READY` using the shared error shape.

### Step 3: Rewrite MCP Tool Registration

- **What**: Replace old tool functions with stable Phase 1 tool handlers.
- **Where**: `mcp/server.py`.
- **Why**: Phase 1 requires a small stable MCP API and removal of old demo names.
- **Considerations**: Prefer an app factory such as `create_mcp_app(runtime)` plus a module-level default app for `python mcp/server.py`. This keeps tests deterministic. Do not register `get_lawlibrary` or `get_paragraph` as stable tools.

### Step 4: Implement Law and Metadata Tool Handlers

- **What**: Implement `list_laws`, `get_law`, and `get_source_metadata` over registry/dataset metadata.
- **Where**: `mcp/server.py`, `mcp/legal_texts/runtime.py`, and `mcp/legal_texts/dataset.py`.
- **Why**: Clients need discovery and provenance without retrieving full law text through legacy parser paths.
- **Considerations**: `list_laws` returns `{"laws", "count", "query"}`. `get_law` returns `{"law", "norms"}` with norm summaries, not a huge concatenated law body. `get_source_metadata` always returns a `sources` list so the shape is stable with or without a code filter.

### Step 5: Implement Norm and Citation Tool Handlers

- **What**: Wire `get_norm` and `resolve_citation` to the resolver service.
- **Where**: `mcp/server.py`, `mcp/legal_texts/resolver.py`, and `mcp/legal_texts/runtime.py`.
- **Why**: MCP norm access must share service-level citation behavior and EGBGB article-plus-section semantics.
- **Considerations**: `resolve_citation` exposes `child_unit` and `child_value` parameters exactly. `get_norm("EGBGB", "art:246a/par:1")` and `resolve_citation(code="EGBGB", unit="art", paragraph_or_article="246a", child_unit="par", child_value="1")` should produce equivalent `CitationResponse` norm payloads.

### Step 6: Implement Search Tool Handler

- **What**: Wire `search_laws(query, codes=None)` to the Phase 6 search service.
- **Where**: `mcp/server.py` and `mcp/legal_texts/search.py`.
- **Why**: MCP search must return the service-level result contract and no backend HTML or serialized strings.
- **Considerations**: Response shape is `{"query", "codes", "results", "count"}`. Invalid query returns `INVALID_QUERY`; invalid filters return registry errors.

### Step 7: Migrate Docker Runtime Packaging

- **What**: Remove `git` install and `git clone https://github.com/bundestag/gesetze.git`; configure the image to run against a mounted or copied validated dataset package.
- **Where**: `Dockerfile`.
- **Why**: Phase 1 must not use `bundestag/gesetze` as production data.
- **Considerations**: Do not bake ignored full datasets into the image by accident. Document expected `DATASET_PATH` mount behavior, for example mounting a validated package at `/data/legal-texts` and setting `DATASET_PATH=/data/legal-texts`. The image may fail fast without a dataset in strict mode.

### Step 8: Add MCP Tool Regression Tests

- **What**: Test stable tool names, absence of old demo names, direct JSON object returns, structured errors, EGBGB child citation parameters, source metadata, and search response shape.
- **Where**: `mcp/tests/test_mcp_tools.py`.
- **Why**: The known regressions are double JSON serialization, wrong URLs, missing dataset failures, and legacy tool leakage.
- **Considerations**: Tests must not use a real LLM client. If FastMCP exposes a tool registry, assert registered names; otherwise test app-factory registration plus direct handler functions. Include a test that fails if any tool returns `str` containing serialized JSON.

### Step 9: Update MCP Documentation

- **What**: Replace legacy tool docs with Phase 1 MCP API contracts, runtime dataset configuration, error behavior, and explicit non-goals.
- **Where**: `docs/features/mcp-law-tools.md`, `docs/modules/mcp-server.md`, and root README later in the final docs update phase if not updated here.
- **Why**: Documentation should match the new stable tool surface and no longer present old demo names as current API.
- **Considerations**: Phase 8 owns HTTP/OpenAPI docs, so keep this focused on MCP.

## Testing Plan

Primary verify command:

```bash
PYTHONPATH=mcp python3 -m pytest mcp/tests/test_mcp_tools.py mcp/tests/test_search.py mcp/tests/test_resolver.py mcp/tests/test_normalizer_gii.py mcp/tests/test_normalizer_eurlex.py mcp/tests/test_dataset_validation.py mcp/tests/test_registry.py mcp/tests/test_source_import.py mcp/tests/test_source_matrix.py mcp/tests/test_parser.py mcp/tests/test_library.py
```

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Tool registry | Registered MCP tool names. | Exactly the Phase 1 stable tools are exposed; `get_lawlibrary` and `get_paragraph` are absent. |
| JSON object returns | Every MCP handler success path and representative error path. | Results are JSON-compatible objects, not pre-serialized strings or plain text errors. |
| Dataset startup/readiness | Strict startup with missing/invalid dataset, normalized-only readiness, and diagnostic/runtime test mode. | Strict startup requires `stage="serving_dataset", state="ready"`; diagnostic handlers return `DATASET_NOT_READY` shape. |
| Law discovery | `list_laws`, `get_law`, and `get_source_metadata` over normalized fixtures. | Responses include canonical IDs, display names/codes, source metadata, URLs, counts, and norm summaries. |
| Norm and citation access | `get_norm` canonical paths and `resolve_citation` structured parameters. | Required fixtures resolve through the shared resolver; EGBGB `child_unit="par"`, `child_value="1"` works. |
| Search MCP wrapper | Valid search, selected-law filters, invalid query, and invalid code filters. | Response wraps Phase 6 results and preserves structured errors. |
| Runtime packaging regression | Dockerfile and server defaults. | No production clone/load path for `bundestag/gesetze`; no default `/app/gesetze/` serving path. |
| Existing prior-phase tests | Import, registry, normalizer, resolver, search, and legacy parser/library tests. | Earlier tests remain passing unless legacy runtime tests are intentionally moved to non-MCP parser/library coverage. |

### Test Integrity Constraints

- Do not disable, skip, xfail, delete, or weaken Phase 2-6 service tests to make MCP tests pass.
- Existing parser/library tests may keep validating legacy parser internals, but they must not be treated as MCP contract tests after this phase.
- If any existing server import tests are added, they must use fixture dataset settings and must not rely on `/app/gesetze/` or network access.

## Rollback Strategy

Revert `mcp/server.py`, `mcp/config.py`, `mcp/legal_texts/runtime.py`, MCP-specific dataset/resolver/search wrapper changes, `mcp/tests/test_mcp_tools.py`, Dockerfile edits, and MCP documentation updates. Phase 2-6 domain services and fixtures remain intact.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Legacy tool names | keep aliases / internal deprecated aliases / remove stable registration | remove stable registration | Phase 1 deliberately cleans up the MCP contract. |
| `get_law` payload | full law text / metadata plus norm summaries / metadata only | metadata plus norm summaries | Avoids huge responses while giving clients navigation data. |
| `get_source_metadata` shape | single object when filtered / list always / map by law ID | list always | Stable shape with or without `code` avoids client branching. |
| Startup behavior | fail-fast always / diagnostic soft mode only in tests / silent empty dataset | fail-fast by default with diagnostic/test mode | Satisfies production safety while allowing error-shape tests. |
| Docker dataset packaging | clone demo data / bake full generated dataset / expect mounted validated dataset | expect mounted validated dataset | Avoids demo dependency and avoids committing ignored full snapshots to the image. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/server.py` | `get_lawlibrary`, `get_paragraph`, `search_laws` | Current MCP surface uses old names and serialized strings. |
| `mcp/server.py` | module-level `library = LawLibrary()` and import-time loading | Needs replacement with validated dataset runtime composition. |
| `mcp/config.py` | `load_from_folder='/app/gesetze/'` and `load_from_github` | Current defaults point at demo Markdown sources. |
| `Dockerfile` | `RUN git clone https://github.com/bundestag/gesetze.git` | Production image currently packages demo data. |
| `mcp/parser.py` | `LawLibrary.search` and `LawLibrary.get_json` | Legacy helpers remain parser/library internals, not MCP contract. |
| `plans/reliable-law-data-mcp/contracts.md` | MCP tool response contracts and migration decision | Defines stable tool names, response shapes, and old-tool removal. |

### Mismatches / Notes

- The current server creates its data runtime at import time, which makes missing-dataset tests and strict startup behavior awkward; Phase 7 should introduce an app/runtime factory.
- The repository still contains legacy parser/library code after this phase because tests and transition docs may need it, but MCP tools must stop depending on it.
- Existing docs and root README still describe the legacy tool surface; Phase 7 updates MCP docs, and the final docs update phase will reconcile root README and repo naming.
