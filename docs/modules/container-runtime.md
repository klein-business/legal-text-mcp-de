---
type: documentation
entity: module
module: "container-runtime"
version: 1.2
---

# Module: container-runtime

> Part of [legal-text-mcp-de](../overview.md)

## Overview

The container runtime is the root `Dockerfile`. It packages the MCP server code
and dependencies, then expects a validated fixture or generated package at
`/data/legal-texts`.

### Responsibility

The image is responsible for running the MCP server in a reproducible Python
environment. It is not responsible for cloning demo data, generating source
snapshots, running full-corpus import gates, or embedding legal texts in the
image.

### Dependencies

| Dependency | Type | Purpose |
| ---------- | ---- | ------- |
| `python:3.12-slim` | container base image | Provides the Python runtime. |
| `uv.lock` and `pyproject.toml` | dependency metadata | Provide the locked uv-managed runtime dependencies. |
| `/data/legal-texts` | mounted data path | Supplies the validated normalized or generated dataset package. |

## Structure

| Path | Type | Purpose |
| ---- | ---- | ------- |
| `Dockerfile` | file | Defines the server container image and startup command. |

## Key Symbols

| Symbol | Kind | Location | Purpose |
| ------ | ---- | -------- | ------- |
| `FROM python:3.12-slim` | Docker instruction | `Dockerfile:1` | Selects the Python base image. |
| `COPY --from=ghcr.io/astral-sh/uv:0.10.12` | Docker instruction | `Dockerfile` | Adds the pinned uv binary. |
| `RUN uv sync --frozen --no-dev --no-group prepare-data --no-install-project --compile-bytecode` | Docker instruction | `Dockerfile` | Installs locked runtime dependencies. |
| `COPY mcp/ ./mcp/` | Docker instruction | `Dockerfile` | Copies server code into `/app/mcp`. |
| `ENV DATASET_PATH=/data/legal-texts` | Docker instruction | `Dockerfile` | Points strict startup at the mounted normalized dataset. |
| `CMD ["uv", "run", "--frozen", "--no-sync", "python", "mcp/server.py"]` | Docker instruction | `Dockerfile` | Starts the MCP server from the uv-managed environment. |

## Data Flow

At runtime, `server.py` loads `DATASET_PATH=/data/legal-texts`, validates
readiness through `LegalTextRuntime`, and serves the MCP tools. The image no
longer installs Git and no longer clones `bundestag/gesetze`.

Generated production packages should be built and validated before container
startup. Operators mount the package read-only; operational artifacts such as
`.artifacts/full-corpus/validation-bundle.json` remain outside the image and
outside Git.

## Configuration

Mount a validated package into the configured path:

```bash
docker run --rm -p 8001:8001 -v /path/to/legal-text-package:/data/legal-texts:ro legal-text-mcp-de
```

The mounted directory may be a legacy fixture package with `laws.json` and
`norms.json`, or a strict generated package with `package.json`, `manifest.json`,
`source-limitations.json`, `relationships.json`, `readiness.json`, and
`search-index.json`.

## Inventory Notes

- **Coverage**: full.
- **Notes**: Production data supply is external to the image and auditable through manifests.
