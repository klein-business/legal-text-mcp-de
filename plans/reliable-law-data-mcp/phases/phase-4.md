---
type: planning
entity: phase
plan: "reliable-law-data-mcp"
phase: 4
status: completed
created: "2026-05-14"
updated: "2026-05-14"
---

# Phase 4: Structured Normalization and Validation

> Part of [reliable-law-data-mcp](../plan.md)

## Objective

Transform raw legal source snapshots into validated normalized records with structured laws, norms, subdivisions, source metadata, stable URLs, and duplicate detection.

## Scope

### Includes

- Parser/normalizer support for law metadata, available structural containers, `§`, `Art.`, Absatz, Satz, Nummer, Buchstabe, headings, and full text.
- EGBGB article container and article-plus-section normalization, including `Art. 246a` as a container and `Art. 246a § 1` as a text-bearing child norm.
- Normalized norm IDs and stable URL fields.
- Required-field validation for every norm: ID, text, URL, source, and metadata; title remains optional where source data lacks it.
- Duplicate norm ID detection.
- URL validation or explicit known-issue marking.
- Normalized data output separated from raw snapshots.
- Normalized dataset package validation and stage-aware readiness state production using the shared readiness contract.
- Parser regression tests for absatz parsing and URL construction.

### Excludes (deferred to later phases)

- Citation resolver API behavior.
- Search ranking and snippets.
- MCP and HTTP endpoint migration.

## Prerequisites

- [x] Phase 1 norm contracts are defined.
- [x] Phase 2 raw snapshots and manifests exist.
- [x] Phase 3 canonical registry can identify laws.

## Deliverables

- [x] Normalizer producing structured law and norm records.
- [x] Validation layer for required fields, duplicates, URLs, and source metadata.
- [x] Normalized dataset readiness validator that produces `ready`, `missing`, `invalid`, or `source_unavailable` for `stage="normalized_dataset"`; serving readiness remains pending until Phase 6 search index validation.
- [x] Normalized fixture artifacts for the Phase 1 citation list.
- [x] Normalized EGBGB container/child artifacts for `art:246a` and `art:246a/par:1`.
- [x] Parser and validation tests for required legal structure levels.
- [x] Documentation of parser coverage and known structural limits.

## Acceptance Criteria

- [x] Required fixture norms normalize into structured JSON records.
- [x] EGBGB `Art. 246a` normalizes as a structural container with child references, while `Art. 246a § 1` normalizes as a text-bearing norm.
- [x] Each normalized norm includes canonical law ID, norm ID, text, URL, source metadata, stand date when available, and hash.
- [x] Duplicate IDs and missing required fields fail validation.
- [x] The parser does not silently return empty data for malformed or unsupported source records.
- [x] Known upstream URL issues are represented explicitly rather than hidden.
- [x] Invalid or missing normalized dataset packages produce the shared readiness state and do not allow silent serving; Phase 4 does not emit `stage="serving_dataset", state="ready"`.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 1 | blocked-by | Requires norm and validation contracts. |
| Phase 2 | blocked-by | Requires raw source snapshots. |
| Phase 3 | blocked-by | Requires canonical law IDs. |
| Phase 5 | blocks | Resolver operates over normalized records. |
| Phase 6 | blocks | Search index uses normalized records. |

## Notes

- The parser should preserve full norm text even when fine-grained subdivisions cannot be confidently extracted.
