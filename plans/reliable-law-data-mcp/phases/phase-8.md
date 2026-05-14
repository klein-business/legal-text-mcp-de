---
type: planning
entity: phase
plan: "reliable-law-data-mcp"
phase: 8
status: completed
created: "2026-05-14"
updated: "2026-05-14"
---

# Phase 8: HTTP API and OpenAPI

> Part of [reliable-law-data-mcp](../plan.md)

## Objective

Expose a small HTTP API beside MCP for tests, deployments, and future integrations, with OpenAPI documentation and response contracts aligned to the shared domain services.

## Scope

### Includes

- `GET /health`.
- `GET /ready`.
- `GET /laws`.
- `GET /laws/{code}`.
- `GET /laws/{code}/norms/{norm}`.
- `GET /search`.
- OpenAPI generation/publication.
- HTTP error mapping for structured domain errors.
- Contract tests for endpoint response shapes and OpenAPI availability.

### Excludes (deferred to later phases)

- Authentication and authorization.
- SaaS tenant routing.
- Write APIs.
- Administrative import trigger APIs unless needed for local development and explicitly documented.

## Prerequisites

- [x] Phase 3 registry is complete.
- [x] Phase 4 normalized dataset readiness is available.
- [x] Phase 5 resolver is complete.
- [x] Phase 6 search service is complete.

## Deliverables

- [x] HTTP app/router integrated with shared services.
- [x] OpenAPI document for Phase 1 endpoints.
- [x] Readiness behavior tied to validated dataset availability.
- [x] HTTP contract tests.
- [x] Documentation of HTTP API usage and response schemas.
- [x] HTTP contract example and test for EGBGB child norm path `/laws/egbgb/norms/art%3A246a%2Fpar%3A1`.

## Acceptance Criteria

- [x] `/health` reports process health independent of dataset readiness.
- [x] `/ready` reports the shared data-layer readiness state and maps `missing`, `invalid`, and `source_unavailable` to the documented structured errors.
- [x] `/laws`, `/laws/{code}`, `/laws/{code}/norms/{norm}`, and `/search` match documented schemas.
- [x] `/laws/egbgb/norms/art%3A246a` returns container metadata, and `/laws/egbgb/norms/art%3A246a%2Fpar%3A1` returns the text-bearing child norm.
- [x] OpenAPI is available and includes all Phase 1 endpoints.
- [x] HTTP errors preserve the structured error code contract.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 3 | blocked-by | Route `{code}` values need registry resolution. |
| Phase 4 | blocked-by | Readiness and law/norm data require normalized dataset. |
| Phase 5 | blocked-by | Norm route uses citation/norm resolver behavior. |
| Phase 6 | blocked-by | Search route uses search service. |
| Phase 7 | parallel | Both transports should share services and contracts. |

## Notes

- The HTTP layer should stay thin; domain behavior belongs in shared services.
