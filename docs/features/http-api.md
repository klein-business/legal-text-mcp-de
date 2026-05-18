---
type: documentation
entity: feature
feature: "http-api"
version: 2.1
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
| `GET` | `/laws/{code}/norms/{norm}/relationships` | Returns relationship metadata for a resolved norm. |
| `GET` | `/corpus/coverage` | Returns generated-package, manifest, terminal-state, source-family, and state-law coverage summaries. |
| `GET` | `/corpus/source-limitations` | Returns source limitations filtered by source family, terminal state, state code, or law ID. |
| `GET` | `/search` | Searches with `query` and optional repeated `codes` filters. |
| `GET` | `/openapi.json` | Returns generated OpenAPI. |

## Examples

```text
GET /laws/uwg
GET /laws/egbgb/norms/art%3A246a
GET /laws/egbgb/norms/art%3A246a%2Fpar%3A1
GET /laws/dsgvo/norms/art%3A5/relationships
GET /corpus/coverage
GET /corpus/source-limitations?source_family=state-law&terminal_state=source_unavailable
GET /search?query=widerruf&codes=bgb&codes=egbgb
```

## Runtime

```bash
DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
uv run uvicorn http_api:app --host 127.0.0.1 --port 8080
```

Since v2.1.0, the HTTP API can also be started via the
`legal-text-mcp-de http` CLI subcommand:

```bash
DATASET_PATH=src/tests/fixtures/normalized \
STRICT_STARTUP=true \
uv run legal-text-mcp-de http --port 8080
```

The runtime is identical — `http` internally calls
`uvicorn.run("legal_text_mcp_de.http_api:app", …)`. This is a convenience
alternative to the direct uvicorn invocation; see
[features/cli-shell-surface](cli-shell-surface.md).

## E2E Verification

`scripts/verify_e2e.py` starts real Uvicorn processes with the fixture dataset
and the generated package fixture. It checks `/health`, `/ready`, `/laws`, EGBGB
encoded child norm lookup, generated-package DSGVO `art:5` and `recital:1`
lookup, `/search`, corpus coverage, source limitations, relationship lookup,
OpenAPI path presence for all documented endpoints, and structured invalid-query
and unknown-law errors over localhost HTTP.

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
