---
type: documentation
entity: feature
feature: "law-loading-and-indexing"
version: 1.1
---

# Feature: law-loading-and-indexing

> Part of [legal-text-mcp-de](../overview.md)

## Summary

Law loading now means loading a validated normalized dataset package, not scraping or cloning demo Markdown at server startup. Search indexing is deterministic over normalized text-bearing norms.

## How It Works

### Operator Flow

1. Import official source artifacts into a raw snapshot directory.
2. Store source URL, retrieval timestamp, stand date when available, and SHA-256 hashes in a manifest.
3. Normalize raw artifacts into `laws.json`, `norms.json`, `readiness.json`, and `search-index.json`.
4. Start MCP or HTTP with `DATASET_PATH` set to the normalized package.

### Runtime Flow

1. `LegalTextRuntime.from_settings` reads `DATASET_PATH`.
2. `validate_dataset_package` checks required files and required law/norm fields.
3. `NormalizedDataset` loads laws and norms and resolves law aliases through `LawRegistry`.
4. `SearchService` builds deterministic in-memory rows from text-bearing norms.
5. MCP and HTTP tools read only from the validated runtime.

## Implementation

| Module | Symbols | Role |
| ------ | ------- | ---- |
| [mcp-server](../modules/mcp-server.md) | `SOURCE_SPECS`, `probe_source`, `import_snapshot`, `diff_manifests` | Source import and manifest handling. |
| [mcp-server](../modules/mcp-server.md) | `parse_gii_zip`, `parse_dsgvo_xml`, `normalize_snapshot` | Raw source normalization. |
| [mcp-server](../modules/mcp-server.md) | `validate_dataset_package`, `NormalizedDataset` | Dataset readiness and loading. |
| [mcp-server](../modules/mcp-server.md) | `SearchService` | Search indexing and result generation. |

## Data Contract

Normalized serving packages contain:

- `laws.json`
- `norms.json`
- `readiness.json`
- `search-index.json`

Every text-bearing norm requires canonical law ID, norm ID, text, URL, source metadata, and content hash. Container norms, such as `egbgb/art:246a`, carry child references instead of invented aggregate text.

## Edge Cases & Limitations

- Startup is strict by default and fails when no valid dataset is configured.
- Known invalid upstream paths, such as `tddsg` and `pangv`, are regression checks and not import sources.
- DSGVO uses Cellar XML (`CELEX:32016R0679`, German expression `0004.02`, `DOC_2`) and is separate from GII.
- Search is Phase 1 deterministic plain-text search, not backend-specific relevance ranking.

## Related Features

- [source-provenance](source-provenance.md)
- [supported-laws](supported-laws.md)
- [mcp-law-tools](mcp-law-tools.md)
