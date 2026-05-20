---
type: documentation
entity: module
module: "container-runtime"
version: 2.1.3
---

# Module: container-runtime

> Part of [legal-text-mcp-de](../overview.md)

## Overview

The container runtime ships two Dockerfiles:

- `Dockerfile` — the standard image used for self-hosting. It packages the MCP
  server code and dependencies, then expects a validated corpus bundle or
  normalized dataset at `/data/legal-texts`.
- `deployment/Dockerfile.hosted` — the hosted-service image layered on top of
  the standard image. It adds rate-limiting and anonymised-logging middleware
  and is used at `mcp.klein.business`.

### Responsibility

The images are responsible for running the MCP server in a reproducible Python
environment. They are not responsible for cloning demo data, generating source
snapshots, running full-corpus import gates, or embedding legal texts in the
image.

### Dependencies

| Dependency | Type | Purpose |
| ---------- | ---- | ------- |
| `python:3.12-slim` | container base image | Provides the Python runtime. |
| `uv.lock` and `pyproject.toml` | dependency metadata | Provide the locked uv-managed runtime dependencies. |
| `/data/legal-texts` (standard) | mounted data path | Supplies the validated normalized or generated dataset package. |
| `/data/corpus/latest.tar.zst` (hosted) | mounted data path | Supplies the daily-refreshed v2 corpus bundle. |

## Structure

| Path | Type | Purpose |
| ---- | ---- | ------- |
| `Dockerfile` | file | Standard server image; expects dataset at `/data/legal-texts`. |
| `deployment/Dockerfile.hosted` | file | Hosted-service image; layers middleware, sets `HOSTED=true`, `STRICT_DATASET=true`. |
| `deployment/Caddyfile` | file | Caddy reverse-proxy config for `mcp.klein.business`. |

## Key Symbols

| Symbol | Kind | Location | Purpose |
| ------ | ---- | -------- | ------- |
| `FROM python:3.12-slim` | Docker instruction | `Dockerfile:1` | Selects the Python base image. Pinned by digest. |
| `LABEL io.modelcontextprotocol.server.name="io.github.klein-business/legal-text-mcp-de"` | Docker instruction | `Dockerfile` | OCI ownership annotation required by the [MCP Registry](../features/mcp-registry-distribution.md) for OCI-package verification. Added in v2.1.3. Must match `server.json` `.name` exactly. |
| `COPY --from=ghcr.io/astral-sh/uv:0.11.14` | Docker instruction | `Dockerfile` | Adds the pinned uv binary. |
| `RUN uv sync --frozen --no-dev --no-group prepare-data --no-install-project --compile-bytecode` | Docker instruction | `Dockerfile` | Installs locked runtime dependencies. |
| `ENV DATASET_PATH=/data/legal-texts` | Docker instruction | `Dockerfile` | Points strict startup at the mounted normalized dataset. |
| `CMD ["uv", "run", "--frozen", "--no-sync", "legal-text-mcp-de", "serve"]` | Docker instruction | `Dockerfile` | Starts the MCP server via the `legal-text-mcp-de serve` CLI subcommand. The `serve` argument is required as of v2.1.0 because bare invocation now prints `--help`. |
| `FROM ghcr.io/klein-business/legal-text-mcp-de:2.1.0` | Docker instruction | `Dockerfile.hosted:4` | Extends the published base image. |
| `ENV HOSTED=true` | Docker instruction | `Dockerfile.hosted` | Activates rate-limit and logging middleware registration. |
| `ENV DATASET_PATH=/data/corpus/latest.tar.zst` | Docker instruction | `Dockerfile.hosted` | Points to the daily-refreshed v2 bundle. |

## Data Flow

At runtime, `server.py` resolves the corpus via `_resolve_dataset_path` and
validates readiness through `LegalTextRuntime`. The standard image mounts a
legacy fixture or generated package; the hosted image mounts a v2 `.tar.zst`
bundle that the `corpus/loader.py` stack reads directly.

Generated production packages and bundles should be built and validated before
container startup. Operational artifacts remain outside the image and outside Git.

## Configuration

**Standard image:**

```bash
docker run --rm -p 8001:8001 \
  -v /path/to/legal-text-package:/data/legal-texts:ro \
  ghcr.io/klein-business/legal-text-mcp-de:2.1.3
```

**Self-host with v2 bundle:**

```bash
docker run --rm -p 8001:8001 \
  -v /path/to/corpus.tar.zst:/data/legal-texts:ro \
  -e STRICT_DATASET=true \
  ghcr.io/klein-business/legal-text-mcp-de:2.1.3
```

**Docker Compose (HTTP mode):**

A minimal copy-pasteable Compose example lives at
[`examples/docker-compose/http/`](../../examples/docker-compose/http/)
in the repo. It boots the FastAPI HTTP transport on port 8001 with no
corpus mounted — `/health` responds, but law and search endpoints
return errors until a corpus is bind-mounted. The Dockerfile's
Python-urllib HEALTHCHECK is inherited automatically (no `curl` needed
in the slim base). For a corpus-backed production stack see
[production-deployment](../operations/production-deployment.md).

The mounted path may be:

- a legacy fixture directory with `laws.json` and `norms.json`;
- a strict generated package with `package.json`, `manifest.json`,
  `source-limitations.json`, `relationships.json`, `readiness.json`, and
  `search-index.json`;
- a v2 `.tar.zst` corpus bundle (standard image with `CORPUS_AUTO_DOWNLOAD`
  disabled, or hosted image).

## Inventory Notes

- **Coverage**: full.
- **Notes**: Production data supply is external to the image and auditable through
  manifests and cosign signatures. See [hosted-deployment](hosted-deployment.md)
  for the full hosted-service topology and [public-hosted-service feature](../features/public-hosted-service.md)
  for end-user connection instructions.
- **Registry distribution**: the same multi-arch image is the `oci` package
  registered on the [official MCP Registry](https://registry.modelcontextprotocol.io)
  as `ghcr.io/klein-business/legal-text-mcp-de:<version>` — see
  [features/mcp-registry-distribution](../features/mcp-registry-distribution.md).
  The `LABEL io.modelcontextprotocol.server.name` directive must stay in the
  Dockerfile for the next OCI publish to succeed.
