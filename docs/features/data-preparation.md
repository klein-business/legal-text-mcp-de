---
type: documentation
entity: feature
feature: "data-preparation"
version: 1.2
---

# Feature: data-preparation

> Part of [legal-text-mcp-de](../overview.md)

## Summary

The historical data-preparation helper is retained, but reliable data preparation is the importer/normalizer workflow under `mcp/legal_texts/`.

## Reliable Data Workflow

1. Use source specs from `mcp/legal_texts/sources.py`.
2. Probe and download official source artifacts with `mcp/legal_texts/importer.py`.
3. Persist raw artifacts and manifests with SHA-256 hashes.
4. Normalize with `mcp/legal_texts/normalizer.py`.
5. Validate the serving package with `mcp/legal_texts/validation.py`.
6. Start MCP/HTTP with `DATASET_PATH` pointing at the normalized package.

## Legacy Helper

`prepare_data/prepare_gesetze_im_internet.sh` still exists for manual Markdown-era experimentation through `gesetze-tools`. Its output is not a production source for the supported runtime.

## Related Features

- [law-loading-and-indexing](law-loading-and-indexing.md)
- [source-provenance](source-provenance.md)
