---
type: documentation
entity: module
module: "container-runtime"
version: 1.1
---

# Module: container-runtime

> Part of [legal-text-mcp-de](../overview.md)

## Overview

The container runtime is the root `Dockerfile`. It packages the MCP server code and dependencies, then expects a validated normalized dataset at `/data/legal-texts`.

### Responsibility

The image is responsible for running the MCP server in a reproducible Python environment. It is not responsible for cloning demo data, generating source snapshots, or embedding legal texts in the image.

### Dependencies

| Dependency | Type | Purpose |
| ---------- | ---- | ------- |
| `python:3.12-slim` | container base image | Provides the Python runtime. |
| `mcp/requirements.txt` | dependency file | Installs MCP, FastAPI, and runtime dependencies. |
| `/data/legal-texts` | mounted data path | Supplies the validated normalized dataset package. |

## Structure

| Path | Type | Purpose |
| ---- | ---- | ------- |
| `Dockerfile` | file | Defines the server container image and startup command. |

## Key Symbols

| Symbol | Kind | Location | Purpose |
| ------ | ---- | -------- | ------- |
| `FROM python:3.12-slim` | Docker instruction | `Dockerfile:1` | Selects the Python base image. |
| `COPY mcp/ .` | Docker instruction | `Dockerfile` | Copies server code into `/app`. |
| `RUN pip install --no-cache-dir -r requirements.txt` | Docker instruction | `Dockerfile` | Installs runtime dependencies. |
| `ENV DATASET_PATH=/data/legal-texts` | Docker instruction | `Dockerfile` | Points strict startup at the mounted normalized dataset. |
| `CMD ["python", "server.py"]` | Docker instruction | `Dockerfile` | Starts the MCP server. |

## Data Flow

At runtime, `server.py` loads `DATASET_PATH=/data/legal-texts`, validates readiness through `LegalTextRuntime`, and serves the MCP tools. The image no longer installs Git and no longer clones `bundestag/gesetze`.

## Configuration

Mount a normalized dataset package into the configured path:

```bash
docker run --rm -p 8001:8001 -v /path/to/normalized-dataset:/data/legal-texts legal-text-mcp-de
```

## Inventory Notes

- **Coverage**: full.
- **Notes**: Production data supply is external to the image and auditable through manifests.
