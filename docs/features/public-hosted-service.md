---
type: documentation
entity: feature
feature: "public-hosted-service"
version: 1.0
---

# Feature: public-hosted-service

> Part of [legal-text-mcp-de](../overview.md)

## Summary

`mcp.klein.business` is an optional publicly hosted instance of
`legal-text-mcp-de`. It exposes the full v2 MCP surface (9 v1 tools,
`research_topic`, 10 `legal://` resources, 5 slash-prompts) over HTTPS with
a daily-refreshed production corpus bundle and per-IP rate limiting. Self-hosting
remains fully supported and does not require this service.

## Endpoints

| URL | Purpose |
| --- | ------- |
| `https://mcp.klein.business/legal/de` | MCP streamable-HTTP endpoint |
| `https://mcp.klein.business/health` | Health check (`status`, `uptime_s`, `corpus_version`) |
| `https://mcp.klein.business/privacy` | Privacy policy |
| `https://mcp.klein.business/terms` | Terms of use |

The `/metrics` endpoint (Prometheus) is internal-only and not publicly accessible.

## Connecting

### Claude Desktop

```json
{
  "mcpServers": {
    "legal-text-de": {
      "url": "https://mcp.klein.business/legal/de"
    }
  }
}
```

### Claude Code

```bash
claude mcp add legal-text-de --transport http https://mcp.klein.business/legal/de
```

### curl (smoke test)

```bash
curl -s https://mcp.klein.business/health | python3 -m json.tool
```

## Rate Limits

Unauthenticated callers (IP-based):

- 100 requests / minute
- 1,000 requests / day

Higher-quota callers can request a bearer token. Supply it via the `Authorization`
header:

```
Authorization: Bearer <token>
```

Responses exceeding limits return `429 Too Many Requests` with a `Retry-After`
header.

## Corpus Currency

The production corpus is refreshed daily from a signed OCI artifact. The
`/health` response includes `corpus_version` (the bundle ID, e.g. `2026-05-17-corpus`)
so clients can detect stale versions. The corpus covers approximately 8,500 German
and EU privacy-law texts.

## Implementation

| Module | Symbols | Role |
| ------ | ------- | ---- |
| [hosted-deployment](../modules/hosted-deployment.md) | `RateLimitMiddleware` | Per-IP/token rate limiting. |
| [hosted-deployment](../modules/hosted-deployment.md) | `validate_bearer` | Bearer-token validation. |
| [hosted-deployment](../modules/hosted-deployment.md) | `health_payload` | `/health` response body. |
| [hosted-deployment](../modules/hosted-deployment.md) | `REQUESTS_TOTAL`, `REQUEST_LATENCY` | Prometheus metrics. |
| [hosted-deployment](../modules/hosted-deployment.md) | `Caddyfile` | TLS + CSP + path routing. |

## Security Notes

- All traffic is TLS-only (Caddy manages certificates via ACME/Let's Encrypt).
- Caddy sets strict CSP, `X-Frame-Options: DENY`, `Nosniff`, `HSTS
  max-age=63072000`.
- IPs are anonymised in logs (last octet truncated).
- The service does not store request bodies or user data beyond what is needed
  for rate-limit accounting.

## SLO

The hosted service targets P95 latency below 500 ms for `get_norm` (warm cache).
No uptime SLA is published. For production workloads, self-host with a private
OCI registry and your own corpus refresh pipeline.

## Operational Runbook

See [operations/hosted-service.md](../operations/hosted-service.md) for the
deploy, rollback, corpus refresh, and soak-test procedures.

## Related

- [hosted-deployment module](../modules/hosted-deployment.md)
- [container-runtime module](../modules/container-runtime.md)
- [operations/hosted-service.md](../operations/hosted-service.md)
