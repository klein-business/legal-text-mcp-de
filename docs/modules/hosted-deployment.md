---
type: documentation
entity: module
module: "hosted-deployment"
version: 1.0
---

# Module: hosted-deployment

> Part of [legal-text-mcp-de](../overview.md)

## Overview

The `deployment/` directory contains everything needed to run the optional
public hosted instance at `mcp.klein.business`. It is a thin layer on top of the
standard container image: a specialised `Dockerfile.hosted`, Caddy reverse-proxy
config, and Python middleware modules for rate-limiting, bearer-token validation,
Prometheus metrics, and health reporting.

### Responsibility

This module is responsible for:

- the `Dockerfile.hosted` that layers production middleware onto the base image;
- the `Caddyfile` that handles TLS, CSP headers, and path routing;
- per-IP / per-token rate limiting;
- optional bearer-token authentication for higher-quota callers;
- Prometheus metrics (`requests_total`, `request_latency_seconds`, `corpus_version`);
- an extended `/health` endpoint that includes corpus version and uptime.

It is not responsible for the MCP tool surface, corpus loading, or data
preparation — those remain in the standard `src/` and `prepare_data/` packages.

### Dependencies

| Dependency | Type | Purpose |
| ---------- | ---- | ------- |
| `ghcr.io/klein-business/legal-text-mcp-de:2.0.0-rc.4` | container base | Provides the complete MCP runtime. |
| `Caddy` | reverse proxy | TLS termination, compression, security headers, path routing. |
| `starlette` | library | `BaseHTTPMiddleware` for rate limiting. |
| `prometheus_client` | library | `Counter`, `Histogram`, `Gauge`, `generate_latest`. |

## Structure

| Path | Type | Purpose |
| ---- | ---- | ------- |
| `deployment/Dockerfile.hosted` | file | Extends the base image with hosted middleware; sets `HOSTED=true`, `STRICT_DATASET=true`. |
| `deployment/Caddyfile` | file | Caddy config for `mcp.klein.business`; proxies `/legal/de*` to the MCP container. |
| `deployment/ratelimit_middleware.py` | file | `RateLimitMiddleware` — 100 req/min, 1000 req/day per (ip, token). |
| `deployment/bearer_token.py` | file | `validate_bearer` — reads `HOSTED_BEARER_TOKENS` env; returns caller-id or `None`. |
| `deployment/metrics.py` | file | Prometheus metric definitions and `render_metrics()`. |
| `deployment/health.py` | file | `health_payload` — returns `status`, `uptime_s`, `corpus_version`. |
| `deployment/anonymised_logging.py` | file | IP-anonymising log middleware (truncates last octet). |
| `deployment/deploy.sh` | file | Deployment helper: pull image, restart containers, wait for health. |

## Key Symbols

| Symbol | Kind | Location | Purpose |
| ------ | ---- | -------- | ------- |
| `RateLimitMiddleware` | class | `ratelimit_middleware.py` | Starlette middleware; sliding window per (ip, token) pair. |
| `validate_bearer` | function | `bearer_token.py` | Returns token string when valid, `None` for IP-based limits. |
| `REQUESTS_TOTAL` | Counter | `metrics.py` | `legal_mcp_requests_total{tool, status}`. |
| `REQUEST_LATENCY` | Histogram | `metrics.py` | `legal_mcp_request_latency_seconds{tool}`. |
| `RATE_LIMIT_REJECTIONS` | Counter | `metrics.py` | `legal_mcp_rate_limit_rejections_total{bucket}`. |
| `CORPUS_VERSION` | Gauge | `metrics.py` | `legal_mcp_corpus_version_info{version}`. |
| `health_payload` | function | `health.py` | Returns `{"status", "uptime_s", "corpus_version"}`. |

## Topology

```
[Internet] → Caddy (TLS + CSP) → legal-text-mcp-de container → /data/corpus/latest.tar.zst
```

Caddy routes:

- `GET /legal/de*` → `reverse_proxy legal-text-mcp-de:8001`
- `GET /privacy` → static file
- `GET /terms` → static file
- All others → 404

## Configuration

| Env variable | Default | Purpose |
| ------------ | ------- | ------- |
| `HOSTED` | `true` | Activates hosted-mode middleware registration. |
| `DATASET_PATH` | `/data/corpus/latest.tar.zst` | Corpus bundle path inside the container. |
| `STRICT_DATASET` | `true` | Fail startup when the corpus file is missing or corrupt. |
| `HOSTED_BEARER_TOKENS` | `""` | Comma-separated list of allowed bearer tokens. |
| `PORT` | `8001` | MCP server bind port. |

## Corpus Refresh

A daily cron job on the host pulls the latest bundle from S3 and swaps
`/data/corpus/latest.tar.zst` atomically (symlink swap). The MCP process
reads the bundle at startup, so a corpus refresh requires a container restart.

## Inventory Notes

- **Coverage**: unit tests cover `RateLimitMiddleware` (per-minute and per-day
  windows), `validate_bearer`, and `health_payload`. Metrics registration is
  tested via import.
- **See also**: [public-hosted-service feature](../features/public-hosted-service.md)
  for the end-user connection instructions; [operations/hosted-service.md](../operations/hosted-service.md)
  for the deploy/rollback runbook.
