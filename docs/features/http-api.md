---
type: documentation
entity: feature
feature: "http-api"
version: 1.1
---

# Feature: http-api

> Part of [legal-text-mcp-de](../overview.md)

## Summary

The HTTP API is a read-only FastAPI transport over `LegalTextRuntime`. It exists for tests, deployments, OpenAPI clients, and future integrations while MCP remains the primary interface.

## Endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| `GET` | `/health` | Returns process health even when no dataset is ready. |
| `GET` | `/ready` | Returns serving dataset readiness or `DATASET_NOT_READY`. |
| `GET` | `/laws` | Lists supported/loaded laws. |
| `GET` | `/laws/{code}` | Returns one law by canonical ID or alias. |
| `GET` | `/laws/{code}/norms/{norm}` | Returns one norm by canonical norm path or shorthand. |
| `GET` | `/search` | Searches with `query` and optional repeated `codes` filters. |
| `GET` | `/openapi.json` | Returns generated OpenAPI. |

## Examples

```text
GET /laws/uwg
GET /laws/egbgb/norms/art%3A246a
GET /laws/egbgb/norms/art%3A246a%2Fpar%3A1
GET /search?query=widerruf&codes=bgb&codes=egbgb
```

## Runtime

```bash
DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
uvicorn http_api:create_http_app --factory --host 127.0.0.1 --port 8080
```

## Error Handling

HTTP errors preserve the shared envelope:

```json
{
  "error": {
    "code": "NORM_NOT_FOUND",
    "message": "Norm not found",
    "details": {}
  }
}
```

The API does not return silent empty successes for missing datasets, unknown laws, missing norms, invalid citations, or invalid search queries.
