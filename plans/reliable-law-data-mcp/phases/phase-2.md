---
type: planning
entity: phase
plan: "reliable-law-data-mcp"
phase: 2
status: completed
created: "2026-05-14"
updated: "2026-05-14"
---

# Phase 2: Reproducible Source Import

> Part of [reliable-law-data-mcp](../plan.md)

## Objective

Replace demo-data assumptions with a reproducible import pipeline that downloads Phase 1 source material, stores raw snapshots, records hashes and metadata, and produces a manifest that can be validated and diffed.

## Scope

### Includes

- `gesetze-im-internet.de` import workflow for German Phase 1 laws.
- Live source probing against every German-law entry in [source-matrix.md](../source-matrix.md), including index and XML ZIP URLs.
- DSGVO source probing against the Publications Office / Cellar XML artifact in [source-matrix.md](../source-matrix.md), including status, XML content type, language/expression metadata, and hash.
- Raw snapshot storage with source URL, retrieval timestamp, stand date when discoverable, and content hash.
- Manifest generation and manifest comparison for snapshot changes.
- Explicit source-kind handling for DSGVO/EUR-Lex without mixing it into the German-law source.
- Import failure behavior for unavailable sources and missing required metadata.
- Documentation for which laws are safely supported by the current import pipeline.

### Excludes (deferred to later phases)

- Full norm subdivision parsing beyond enough metadata to validate snapshots.
- Citation resolver and search index.
- HTTP API and MCP tool changes.
- Legal interpretation of source content.

## Prerequisites

- [x] Phase 1 contracts and dataset layout are complete.
- [x] Supported law identifiers and source-kind policy are defined.
- [x] [source-matrix.md](../source-matrix.md) is complete and reviewed.

## Deliverables

- [x] Reproducible import command or module.
- [x] Source-probe validation for every matrix row, with expected 200 checks for valid URLs and expected 404 checks for known invalid source paths.
- [x] DSGVO source-probe validation against the Cellar XML URL, with no dependency on the EUR-Lex `TXT` page for machine import.
- [x] Raw snapshot artifact layout populated by import fixtures or real source snapshots.
- [x] Manifest format with hashes, source URLs, retrieval timestamps, stand dates, and canonical IDs.
- [x] Import validation failures for unavailable source and missing required fields.
- [x] Documentation of supported and known-issue source entries.

## Acceptance Criteria

- [x] Running the import twice against unchanged source material yields stable hashes and manifest semantics.
- [x] Import validation fails if any required matrix index URL or XML ZIP URL does not match expected status.
- [x] Import validation fails if DSGVO Cellar XML is unavailable, non-XML, or does not match the expected CELEX/language metadata.
- [x] Known invalid paths `tddsg` and `pangv` are tested as invalid source paths while remaining valid aliases where configured.
- [x] Import does not depend on `bundestag/gesetze` for production data.
- [x] Manifest changes between snapshots are visible and testable.
- [x] Missing required source metadata causes a controlled import failure.
- [x] DSGVO provenance is represented separately from `gesetze-im-internet.de`.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 1 | blocked-by | Requires dataset and metadata contracts. |
| Phase 4 | blocks | Normalization consumes raw snapshots and manifest metadata. |
| Phase 9 | blocks | Release gate verifies source documentation and fixture completeness. |

## Notes

- This phase may keep a small committed fixture snapshot for tests while allowing real imports to write ignored local data.
