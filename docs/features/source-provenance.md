---
type: documentation
entity: feature
feature: "source-provenance"
version: 1.2
---

# Feature: source-provenance

> Part of [legal-text-mcp-de](../overview.md)

## Summary

Every law and norm response carries provenance. Clients can distinguish German GII sources from the DSGVO Cellar source, inspect URLs and hashes, and avoid treating fixture text as untraceable model output.

## Metadata Fields

| Field | Purpose |
| ----- | ------- |
| `source_kind` | `gesetze-im-internet` or `eur-lex-cellar`. |
| `source_identifier` | GII source path or CELEX identifier. |
| `source_url` | Canonical import/source URL. |
| `retrieved_at` | Snapshot retrieval timestamp. |
| `stand_date` | Source stand date when available. |
| `stand_date_status` | Whether stand date is available, missing, or a known issue. |
| `content_hash` | SHA-256 over the source or normalized content. |
| `source_metadata` | Source-kind-specific fields such as Cellar work/expression/document. |
| `known_issues` | Explicit limitations or source anomalies. |

## Data Separation

Raw snapshots and normalized data are separate:

- raw snapshots: `data/sources/raw/{snapshot_id}/` (ignored local data);
- normalized serving packages: `data/normalized/{dataset_id}/` (ignored local data);
- committed test fixtures: `mcp/tests/fixtures/normalized/`.

## Source Rules

- Supported German laws use `gesetze-im-internet.de` source paths from the source matrix.
- DSGVO uses the official Publications Office / Cellar XML source for CELEX `32016R0679`, German expression `0004.02`, document `DOC_2`.
- Known invalid GII paths, including `tddsg` and `pangv`, are regression checks and are not production source paths.
- Missing or invalid source metadata fails validation instead of producing partial silent data.
