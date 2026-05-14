---
type: planning
entity: phase
plan: "reliable-law-data-mcp"
phase: 7
status: completed
created: "2026-05-14"
updated: "2026-05-14"
---

# Phase 7: MCP Tool API Migration

> Part of [reliable-law-data-mcp](../plan.md)

## Objective

Replace the demo MCP tool surface with a small stable Phase 1 API that returns real JSON-compatible objects and delegates to shared domain, resolver, metadata, and search services.

## Scope

### Includes

- MCP tools: `list_laws(query?: string)`, `get_law(code: string)`, `get_norm(code: string, norm: string)`, `resolve_citation(...)`, `search_laws(query: string, codes?: string[])`, and `get_source_metadata(code?: string)`.
- Removal of old stable demo tool names `get_lawlibrary` and `get_paragraph` from the Phase 1 tool surface according to [contracts.md](../contracts.md).
- Runtime config/default migration so the MCP server starts from a validated dataset package rather than `/app/gesetze/` or a cloned `bundestag/gesetze` repository.
- Dockerfile/runtime packaging migration away from cloning `bundestag/gesetze` as production data.
- Real JSON object returns, not double-serialized strings.
- Shared structured error payloads.
- MCP readiness behavior using the shared dataset readiness contract.
- MCP tool tests without real LLM clients.
- Regression tests for double JSON serialization and wrong URLs.

### Excludes (deferred to later phases)

- HTTP API and OpenAPI.
- UI or SaaS client concerns.
- Legal reasoning prompts.

## Prerequisites

- [x] Phase 3 registry is complete.
- [x] Phase 5 resolver is complete.
- [x] Phase 6 search service is complete.
- [x] Source metadata service exists from Phases 2 and 4.

## Deliverables

- [x] Updated MCP server tool definitions.
- [x] Updated runtime defaults and container packaging for validated dataset package loading.
- [x] Transport-independent service calls from MCP tools.
- [x] MCP response and error tests.
- [x] MCP `resolve_citation` tests for EGBGB article-plus-section parameters `child_unit="par"` and `child_value="1"`.
- [x] Documentation of the Phase 1 MCP API contract.

## Acceptance Criteria

- [x] All required MCP tools are present with stable parameter names.
- [x] Old demo tool names are absent from the stable Phase 1 MCP surface, or any temporary compatibility aliases are internal/deprecated and removed before Phase 9.
- [x] Server startup no longer defaults to `/app/gesetze/` from `bundestag/gesetze`, and Docker build no longer clones `bundestag/gesetze` for production serving.
- [x] MCP tools return JSON-compatible objects directly.
- [x] `list_laws`, `get_law`, `get_norm`, `resolve_citation`, `search_laws`, and `get_source_metadata` include canonical IDs and source metadata where applicable.
- [x] Legacy double serialization is covered by a failing-then-passing regression test.
- [x] Missing data and invalid input never produce silent empty successful responses.
- [x] Missing or invalid datasets produce `DATASET_NOT_READY` through the shared readiness/error shape.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 3 | blocked-by | Tools resolve law codes through registry. |
| Phase 5 | blocked-by | Citation and norm retrieval require resolver behavior. |
| Phase 6 | blocked-by | Search tool requires search service. |
| Phase 8 | parallel | HTTP can share the same services after resolver/search contracts exist. |

## Notes

- This phase is a deliberate API cleanup and may be breaking for clients using the old demo tool names.
