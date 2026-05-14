---
type: planning
entity: phase
plan: "reliable-law-data-mcp"
phase: 1
status: completed
created: "2026-05-14"
updated: "2026-05-14"
---

# Phase 1: Domain Contracts and Dataset Layout

> Part of [reliable-law-data-mcp](../plan.md)

## Objective

Define the Phase 1 domain model, JSON contracts, dataset directory layout, error contract, fixture inventory, and source-boundary rules before changing parser or API behavior. This phase turns the requirements into stable schemas and testable contracts so later phases can implement against a fixed target.

## Scope

### Includes

- Domain records for laws, source metadata, raw snapshots, normalized laws, norms, norm subdivisions, search results, citation requests/responses, and structured errors.
- Dataset layout for raw snapshots, normalized output, manifests, fixture input, and golden JSON output.
- Verified source matrix covering every Phase 1 law, expected index/source URLs, probe status, source kind, source path, and known invalid paths.
- Phase 1 supported law inventory and provenance policy, including separate DSGVO/EUR-Lex marking.
- Canonical identifier grammar for law IDs, norm IDs, citation IDs, subdivision paths, and HTTP norm path encoding.
- Article-plus-section request grammar and structural container semantics for EGBGB `Art. 246a`, including `child_unit`/`child_value` resolver fields and encoded HTTP norm paths.
- DSGVO source artifact policy using retrievable official Publications Office / Cellar XML, not the challenge-prone EUR-Lex `TXT` page.
- Structured error payload schema and transport mapping for MCP and HTTP.
- Dataset readiness state model shared by startup, import validation, MCP, and HTTP.
- Contract definitions for MCP and HTTP response shapes at the schema/documentation level.
- Fixture plan for the required BGB, EGBGB, DDG, UWG, TDDDG/TTDSG, BDSG, BFSG, VSBG, PAngV, and DSGVO references.
- Explicit MCP migration decision for legacy tool names.
- Decision records for non-goals: no SaaS, billing, tenants, legal advice, or hallucinated fallback behavior.

### Excludes (deferred to later phases)

- Actual source downloading and snapshot generation.
- Parser replacement and real normalization.
- Runtime resolver, search index, MCP tool implementation, and HTTP server implementation.
- Complete OpenAPI generation and runtime transport wiring.

## Prerequisites

- [x] Current generated docs exist under `docs/`.
- [x] Current MCP server behavior and known limitations are understood from `docs/modules/mcp-server.md` and `docs/features/mcp-law-tools.md`.

## Deliverables

- [x] Contract documentation or schema files for laws, norms, source metadata, search results, citation resolution, and errors.
- [x] Verified source matrix matching [source-matrix.md](../source-matrix.md), including `ttdsg` and `pangv_2022` source path decisions and invalid-path regression requirements.
- [x] DSGVO source contract matching [source-matrix.md](../source-matrix.md), including CELEX, Cellar work ID, expression, language, XML URL, content type, and hash requirements.
- [x] Canonical identifier and citation grammar matching [contracts.md](../contracts.md).
- [x] Dataset readiness contract matching [contracts.md](../contracts.md).
- [x] Dataset layout documentation for raw and normalized artifacts.
- [x] Phase 1 supported-law registry draft with source kind and provenance policy.
- [x] Test fixture inventory document matching [fixture-inventory.md](../fixture-inventory.md), including exact BDSG and DSGVO fixtures.
- [x] Updated plan or project docs linking the contracts to implementation phases.

## Acceptance Criteria

- [x] Every later phase can reference a concrete contract or schema from this phase.
- [x] Every required source has an explicit source path/identifier, source URL, expected probe status, and invalid-path regression rule where applicable.
- [x] DSGVO is explicitly separated from `gesetze-im-internet.de` provenance.
- [x] Canonical norm IDs and citation grammar cover `§`, `Art.`, suffix norms such as `5a`, EGBGB article references, invalid ranges, and URL encoding.
- [x] EGBGB `Art. 246a` behavior is explicit: container metadata for `art:246a`, text-bearing child for `art:246a/par:1`.
- [x] EGBGB article-plus-section wire forms are explicit for resolver service, MCP tool parameters, and HTTP `/laws/{code}/norms/{norm}` path encoding.
- [x] Required metadata fields are classified as required, optional, or known-issue-capable.
- [x] Structured error payload fields, suggestion limits, and HTTP/MCP transport mappings are documented before runtime implementation.
- [x] Dataset readiness states and serving behavior are documented before any transport consumes the dataset.
- [x] Legacy MCP tool names have a documented migration decision before implementation.
- [x] No code path relies on `bundestag/gesetze` as a planned production source.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 2 | blocks | Import must use the dataset layout and source metadata contract. |
| Phase 3 | blocks | Alias registry depends on canonical law contract. |
| Phase 4 | blocks | Normalization depends on norm and subdivision contracts. |
| Phase 5 | blocks | Resolver response/error contracts must be known first. |
| Phase 6 | blocks | Search result shape depends on norm ID and metadata contracts. |
| Phase 7 | blocks | MCP tools depend on stable response contracts. |
| Phase 8 | blocks | HTTP/OpenAPI schemas depend on stable response contracts. |

## Notes

- Keep this phase focused on contracts and repository-visible documentation/schema artifacts. The detailed implementation approach belongs in `implementation/phase-1-impl.md`.
