---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 2
status: completed
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 2: Generated package format and runtime compatibility

> Part of [full-privacy-corpus](../plan.md)

## Objective

Introduce a generated corpus package contract that can serve both small fixtures
and future full production datasets while preserving existing MCP and HTTP
behavior.

## Scope

### Includes

- Dataset package layout for laws, norms, search index, readiness, manifest, and
  source-failure records.
- Package layout for relationship records with stable IDs, relationship types,
  provenance, and source-target validation.
- Compatibility rules for existing `laws.json`, `norms.json`, `readiness.json`,
  and `search-index.json`.
- Additive schema support for citation units `par`, `art`, `recital`, `chapter`,
  `section`, `annex`, and structural `container`.
- Loader validation for package metadata and manifest references.
- Fixture package updates that remain small and committable.
- Runtime readiness semantics for generated packages.

### Excludes (deferred to later phases)

- Large generated production dataset.
- Bulk GII import.
- New relationship lookup APIs.
- Search performance tuning beyond preserving current behavior.

## Prerequisites

- [x] Phase 1 manifest contract is complete.

## Deliverables

- [x] Documented generated package format.
- [x] Documented citation-unit schema and backwards compatibility rules.
- [x] Documented relationship record package schema.
- [x] Runtime-compatible fixture package.
- [x] Validation tests for package metadata and manifest references.
- [x] Backwards compatibility tests for existing MCP and HTTP tools.

## Acceptance Criteria

- [x] Existing MCP and HTTP E2E checks pass against the fixture package.
- [x] Package validation fails when manifest and normalized records disagree.
- [x] Package validation rejects unsupported or malformed citation units.
- [x] Package validation rejects relationship records with missing provenance,
      unsupported relationship types, duplicate relationship IDs, or targets that
      resolve to neither official records nor source limitations.
- [x] Existing `par` and `art` fixture behavior remains unchanged.
- [x] The package format can represent source failures without adding fake law or
      norm records.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 1 | blocked-by | Requires shared manifest contract. |
| Phase 3 | blocks | GII discovery should write package-compatible manifests. |
| Phase 10 | blocks | Coverage APIs need package metadata. |

## Notes

This phase keeps the runtime stable before any high-volume corpus data is added.
