---
type: documentation
entity: module
module: "data-preparation"
version: 1.2
---

# Module: data-preparation

> Part of [legal-text-mcp-de](../overview.md)

## Overview

The `prepare_data/` directory contains the legacy helper workflow around `gesetze-tools`. It is kept for historical/manual experimentation, but it is not the production import path.

### Responsibility

This module can bootstrap an external helper checkout and convert law data to Markdown. The reliable pipeline instead uses `mcp/legal_texts/importer.py`, `normalizer.py`, source manifests, and validated normalized datasets.

### Dependencies

| Dependency | Type | Purpose |
| ---------- | ---- | ------- |
| `git` | command-line tool | Clones the external `gesetze-tools` helper project. |
| `uv` | command-line tool | Runs the helper with the locked `prepare-data` dependency group. |
| `lawde.py`, `lawdown.py` | external scripts | Download and convert data in the legacy helper workflow. |

## Structure

| Path | Type | Purpose |
| ---- | ---- | ------- |
| `prepare_data/prepare_gesetze_im_internet.sh` | file | Legacy helper script for `gesetze-tools`. |

## Validation

The helper supports a no-network dependency check:

```bash
prepare_data/prepare_gesetze_im_internet.sh --dry-run
```

That path uses `uv run --group prepare-data` against the repository project metadata and does not perform upstream checkout or import work.

## Production Boundary

Production serving does not use this module. Docker, MCP startup, HTTP startup, and source import tests use the normalized dataset pipeline and official source specs under `mcp/legal_texts/`.

## Inventory Notes

- **Coverage**: legacy only.
- **Notes**: Keep this documentation explicit so `prepare_data/` is not mistaken for the reliable import path.
