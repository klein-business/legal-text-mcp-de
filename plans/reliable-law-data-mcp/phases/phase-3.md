---
type: planning
entity: phase
plan: "reliable-law-data-mcp"
phase: 3
status: completed
created: "2026-05-14"
updated: "2026-05-14"
---

# Phase 3: Canonical Registry and Alias Resolution

> Part of [reliable-law-data-mcp](../plan.md)

## Objective

Create a versioned alias registry that resolves user-facing law names and legacy paths to canonical internal IDs, source paths, and display codes. This removes hidden alias logic from parser code and makes law identity auditable.

## Scope

### Includes

- Registry entries matching [source-matrix.md](../source-matrix.md) for BGB, EGBGB, DDG, UWG / `uwg_2004`, TDDDG / TTDSG aliases with source path `ttdsg`, BDSG / `bdsg_2018`, BFSG, VSBG, PAngV / `pangv_2022`, and DSGVO/EUR-Lex source separation.
- Canonical mapping from user alias to internal ID to source path to display abbreviation.
- Alias versioning and collision detection.
- Controlled suggestions for ambiguous or unknown aliases.
- Unit tests for all required examples and collision cases.

### Excludes (deferred to later phases)

- Norm parsing and citation slicing.
- Search indexing.
- HTTP and MCP endpoint migration beyond shared registry behavior.

## Prerequisites

- [x] Phase 1 law identity contract exists.
- [x] Phase 2 source path conventions are known or stubbed in fixtures.
- [x] Source matrix has been validated against official paths or test fixtures.

## Deliverables

- [x] Versioned alias registry artifact.
- [x] Registry loader and resolver behavior.
- [x] Collision and ambiguity error handling.
- [x] Tests for required law aliases and historical path handling.
- [x] Documentation of canonical IDs and display abbreviations.

## Acceptance Criteria

- [x] `UWG`, `uwg_2004`, and `Gesetz gegen den unlauteren Wettbewerb` resolve to canonical `uwg_2004`.
- [x] `TDDDG`, `TTDSG`, `ttdsg`, and `tddsg` resolve to canonical `tdddg`, but only `ttdsg` is used as the upstream source path.
- [x] `BDSG` and `bdsg_2018` resolve unambiguously.
- [x] `PAngV`, `pangv`, and `pangv_2022` resolve to canonical `pangv_2022`, but only `pangv_2022` is used as the upstream source path.
- [x] Alias collisions fail validation before runtime serving.
- [x] Every law-facing response can include canonical ID and display code.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 1 | blocked-by | Requires law identity contracts. |
| Phase 2 | blocked-by | Needs source path conventions for registry entries. |
| Phase 5 | blocks | Citation resolver depends on canonical law resolution. |
| Phase 7 | blocks | MCP tools use registry for `code` parameters. |
| Phase 8 | blocks | HTTP routes use registry for `{code}` parameters. |

## Notes

- Registry entries should be data, not parser branches.
