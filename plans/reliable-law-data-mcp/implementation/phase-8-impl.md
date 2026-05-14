---
type: planning
entity: implementation-plan
plan: "reliable-law-data-mcp"
phase: 8
status: draft
created: "2026-05-14"
updated: "2026-05-14"
---

# Implementation Plan: Phase 8 - HTTP API and OpenAPI

> Implements [Phase 8](../phases/phase-8.md) of [reliable-law-data-mcp](../plan.md)

## Approach

Phase 8 adds a thin HTTP API beside MCP using the same runtime and domain services from Phase 7. The HTTP layer should expose health, readiness, law discovery, norm lookup, search, structured error mapping, and OpenAPI without duplicating resolver/search/business logic. FastAPI is the pragmatic fit because it provides OpenAPI and test clients directly; add it explicitly to runtime requirements if it is not already present through transitive dependencies.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| `mcp/http_api.py` | create | FastAPI app factory, route registration, service delegation, and HTTP error mapping. |
| `mcp/http_models.py` | create | Pydantic response models/OpenAPI schemas for HTTP wrapper responses and errors. |
| `mcp/legal_texts/runtime.py` | modify/reference | Reuse the Phase 7 runtime composition for HTTP app construction and readiness. |
| `mcp/legal_texts/errors.py` | modify/reference | Provide HTTP status mapping and JSON error response helpers. |
| `mcp/legal_texts/resolver.py` | modify/reference | Provide norm-path parsing used by `/laws/{code}/norms/{norm}`. |
| `mcp/legal_texts/search.py` | modify/reference | Provide search response wrapper for `/search`. |
| `mcp/requirements.txt` | modify | Add `fastapi` and `uvicorn` if not already available as direct dependencies. |
| `mcp/tests/test_http_api.py` | create | HTTP contract tests with FastAPI/TestClient and fixture runtime. |
| `docs/features/http-api.md` | create | Document endpoints, query parameters, errors, and OpenAPI location. |
| `docs/modules/mcp-server.md` | modify/reference | Note the HTTP app as a sibling transport over shared services. |

## Required Context

| File | Why |
|------|-----|
| `plans/reliable-law-data-mcp/plan.md` | Global HTTP, OpenAPI, structured error, and no-SaaS requirements. |
| `plans/reliable-law-data-mcp/phases/phase-8.md` | Gated Phase 8 scope and acceptance criteria. |
| `plans/reliable-law-data-mcp/contracts.md` | HTTP API contracts, transport error mapping, readiness, search, and norm path grammar. |
| `plans/reliable-law-data-mcp/implementation/phase-5-impl.md` | Resolver and EGBGB article-plus-section behavior. |
| `plans/reliable-law-data-mcp/implementation/phase-6-impl.md` | Search service and `INVALID_QUERY` behavior. |
| `plans/reliable-law-data-mcp/implementation/phase-7-impl.md` | Shared runtime composition, dataset settings, and tool wrapper shapes reused by HTTP. |
| `mcp/server.py` | Current MCP transport boundary so HTTP does not duplicate MCP registration logic. |
| `mcp/legal_texts/runtime.py` | Runtime object to inject into HTTP app factory. |
| `mcp/tests/fixtures/normalized/` | Fixture dataset package for HTTP contract tests. |
| `mcp/requirements.txt` | Dependency baseline for adding HTTP/OpenAPI runtime support. |
| `docs/modules/mcp-server.md` | Existing server module documentation to update with sibling HTTP transport. |

## HTTP Contract

The HTTP app must expose:

- `GET /health` returning `200 {"status": "ok"}` without requiring dataset readiness;
- `GET /ready` returning `200` with readiness when `stage="serving_dataset", state="ready"`, otherwise a structured `503` readiness error;
- `GET /laws?query=` returning the same success shape as MCP `list_laws`;
- `GET /laws/{code}` returning the same success shape as MCP `get_law`;
- `GET /laws/{code}/norms/{norm}` returning `CitationResponse`;
- `GET /search?query=&codes=` returning the same success shape as MCP `search_laws`;
- `GET /openapi.json` through FastAPI's OpenAPI support.

`codes` is a repeatable query parameter, for example `/search?query=preis&codes=PAngV&codes=UWG`. The norm route must support encoded article-plus-section child paths such as `/laws/egbgb/norms/art%3A246a%2Fpar%3A1`; use a path-capture route such as `{norm:path}` or equivalent if the framework decodes `%2F` before route matching.

## Implementation Steps

### Step 1: Add HTTP Dependencies

- **What**: Add direct HTTP dependencies needed for app creation, OpenAPI, and tests.
- **Where**: `mcp/requirements.txt`.
- **Why**: Phase 8 must not rely on incidental transitive dependencies for the public HTTP API.
- **Considerations**: Add `fastapi` and `uvicorn`; FastAPI's test client may require its normal dependency set. Keep dependencies minimal and avoid auth/tenant packages.

### Step 2: Define HTTP Response Models

- **What**: Add Pydantic models or schema definitions for health, readiness, law list, law detail, citation response, search response, source metadata response, and structured errors.
- **Where**: `mcp/http_models.py` and route `response_model` / `responses` declarations in `mcp/http_api.py`.
- **Why**: OpenAPI must document real API contracts, not generic untyped dictionaries.
- **Considerations**: Models should mirror the shared contracts without becoming a second source of domain truth. If domain models already provide Pydantic models by implementation time, reuse or wrap them instead of duplicating fields manually.

### Step 3: Create HTTP App Factory

- **What**: Implement `create_http_app(runtime)` that returns a FastAPI app wired to the shared runtime.
- **Where**: `mcp/http_api.py`.
- **Why**: Tests and deployments need a deterministic HTTP app without starting a real server process.
- **Considerations**: Do not create a separate dataset/runtime at import time. Reuse Phase 7 runtime composition. The app factory should be able to receive a fixture runtime in tests. Provide a module-level `app` or documented `uvicorn` target for deployments, created from settings in the same fail-fast style as Phase 7.

### Step 4: Implement Health and Readiness Routes

- **What**: Add `/health` and `/ready`.
- **Where**: `mcp/http_api.py`.
- **Why**: Deployments need process health separate from data readiness.
- **Considerations**: `/health` must stay `200` even when dataset is missing. `/ready` must report serving readiness and map missing/invalid/source-unavailable states to structured errors and HTTP status codes from `contracts.md`.

### Step 5: Implement Law Routes

- **What**: Add `/laws` and `/laws/{code}` over runtime law metadata services.
- **Where**: `mcp/http_api.py`.
- **Why**: HTTP clients need the same law discovery and norm inventory as MCP clients.
- **Considerations**: `/laws?query=` follows the MCP `list_laws` response shape. `/laws/{code}` resolves aliases through the registry and returns `LAW_NOT_FOUND` or `AMBIGUOUS_LAW_ALIAS` structured errors when needed.

### Step 6: Implement Norm Route with Encoded Child Paths

- **What**: Add `/laws/{code}/norms/{norm}` and route encoded child norm paths to resolver behavior.
- **Where**: `mcp/http_api.py` and shared norm-path parser/helper from resolver.
- **Why**: EGBGB article-plus-section access is a Phase 1 contract and a regression-prone URL path case.
- **Considerations**: Use a path-capture parameter if necessary. Tests must call `/laws/egbgb/norms/art%3A246a` and `/laws/egbgb/norms/art%3A246a%2Fpar%3A1`; the first returns container metadata, the second returns text-bearing child norm data.

### Step 7: Implement Search Route

- **What**: Add `/search` with required `query` and repeatable optional `codes` parameters.
- **Where**: `mcp/http_api.py`.
- **Why**: HTTP search must use the same result contract and query validation as MCP search.
- **Considerations**: Missing or empty query maps to `INVALID_QUERY`; invalid law filters map to registry errors. Do not expose backend search syntax or HTML snippets.

### Step 8: Implement HTTP Error Mapping

- **What**: Convert domain structured errors to HTTP JSON responses with correct status codes.
- **Where**: `mcp/http_api.py` and `mcp/legal_texts/errors.py`.
- **Why**: HTTP clients need status codes and machine-readable error payloads.
- **Considerations**: Preserve the exact `error` object body. Do not wrap errors in a second envelope. Tests should cover every Phase 1 error code reachable through HTTP, including `INVALID_QUERY`.

### Step 9: Add OpenAPI Contract Tests

- **What**: Assert `/openapi.json` exists and includes all Phase 1 endpoints and relevant response schemas.
- **Where**: `mcp/tests/test_http_api.py`.
- **Why**: OpenAPI is a Phase 1 requirement, not optional documentation.
- **Considerations**: Tests should assert path keys for `/health`, `/ready`, `/laws`, `/laws/{code}`, `/laws/{code}/norms/{norm}`, and `/search`, plus non-empty component schemas for success and error responses. If FastAPI emits `{norm}` as `{norm_path}` because of a path-capture name, document and test the actual OpenAPI path deliberately.

### Step 10: Document HTTP API

- **What**: Add endpoint documentation, examples, readiness/error behavior, OpenAPI location, and non-goals.
- **Where**: `docs/features/http-api.md` and `docs/modules/mcp-server.md`.
- **Why**: Phase 8 acceptance requires documented contracts.
- **Considerations**: Keep authentication, billing, tenancy, and import-trigger APIs out of scope.

## Testing Plan

Primary verify command:

```bash
PYTHONPATH=mcp python3 -m pytest mcp/tests/test_http_api.py mcp/tests/test_mcp_tools.py mcp/tests/test_search.py mcp/tests/test_resolver.py mcp/tests/test_normalizer_gii.py mcp/tests/test_normalizer_eurlex.py mcp/tests/test_dataset_validation.py mcp/tests/test_registry.py mcp/tests/test_source_import.py mcp/tests/test_source_matrix.py mcp/tests/test_parser.py mcp/tests/test_library.py
```

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Health/readiness | `/health` with missing and ready dataset; `/ready` with ready, missing, invalid, and source-unavailable states. | `/health` remains 200; `/ready` returns readiness or structured 503 errors. |
| Law endpoints | `/laws`, `/laws?query=`, and `/laws/{code}` over fixture runtime. | Shapes match MCP law wrappers and include canonical IDs/source metadata. |
| Norm endpoint | `/laws/{code}/norms/{norm}` for canonical paths, simple paths, missing norms, and EGBGB child path. | Container and child responses match resolver goldens; errors are structured. |
| Search endpoint | `/search?query=...` with all-law search, repeated `codes`, invalid code, and invalid query. | Results match search service contract; `INVALID_QUERY` and registry errors map correctly. |
| OpenAPI | `/openapi.json`. | All Phase 1 paths are present with non-empty component schemas, success response models, and documented error response statuses. |
| HTTP error mapping | Reachable error codes through endpoints. | HTTP status matches `contracts.md` and response body preserves `{"error": ...}`. |
| Existing prior-phase tests | MCP, search, resolver, normalizer, import, registry, and parser/library tests. | Earlier behavior remains passing. |

### Test Integrity Constraints

- Do not weaken MCP, resolver, search, registry, import, or validation tests to make HTTP pass.
- HTTP tests must use a fixture runtime/TestClient, not a real server process and not a real LLM client.
- OpenAPI tests must assert endpoint presence and schema shape, not only HTTP 200.

## Rollback Strategy

Remove `mcp/http_api.py`, `mcp/http_models.py`, HTTP dependency additions, `mcp/tests/test_http_api.py`, HTTP documentation, and HTTP-specific error mapping changes if unused elsewhere. Phase 2-7 domain services and MCP runtime remain intact.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| HTTP framework | FastAPI / Starlette manually / stdlib WSGI | FastAPI | Provides OpenAPI and contract testing with minimal custom code. |
| Runtime sharing | separate HTTP runtime / shared Phase 7 runtime / global singleton only | shared Phase 7 runtime | Avoids drift between MCP and HTTP behavior. |
| Search `codes` parameter | comma-separated / repeatable query param / JSON body | repeatable query param | Fits GET semantics and FastAPI/OpenAPI naturally. |
| Norm path route | single segment only / path capture / query parameter | path capture for encoded child paths | Required for EGBGB `art%3A246a%2Fpar%3A1` route behavior. |
| Import/admin routes | include now / exclude / hidden local-only | exclude | Phase 1 HTTP API is read-only and transport-focused. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/requirements.txt` | current dependencies | No direct FastAPI dependency exists yet. |
| `mcp/server.py` | FastMCP app and old tools | HTTP must be sibling transport, not mixed into MCP tool registration. |
| `plans/reliable-law-data-mcp/contracts.md` | HTTP contracts and error mapping | Defines endpoint shapes and status codes. |
| `plans/reliable-law-data-mcp/implementation/phase-7-impl.md` | runtime composition | HTTP should reuse the same dataset/search/resolver runtime. |
| `plans/reliable-law-data-mcp/phases/phase-8.md` | EGBGB encoded child route acceptance | Confirms the path-encoding regression is in scope. |

### Mismatches / Notes

- The repository currently has no HTTP app or OpenAPI artifact beyond FastMCP's transport internals.
- The HTTP API should not trigger imports or source downloads; data readiness comes from the validated dataset runtime.
- If the web framework decodes `%2F` before route matching, implementation must use path capture or equivalent and tests must prove the EGBGB child route works.
