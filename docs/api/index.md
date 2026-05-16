# HTTP API overview

The HTTP API is a FastAPI application exposing the same runtime as the
MCP server. It is intended for non-MCP clients such as scripts, cURL,
or other HTTP consumers.

Default port: **8080**.

## Starting the HTTP API

```bash
DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
uv run uvicorn http_api:app --host 127.0.0.1 --port 8080
```

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness — returns `{"status": "ok"}` |
| `GET` | `/ready` | Readiness — dataset validation check |
| `GET` | `/laws` | List laws; optional `?query=` filter |
| `GET` | `/laws/{code}` | Law detail with norm summaries |
| `GET` | `/laws/{code}/norms/{norm}` | Single norm (full text + provenance) |
| `GET` | `/laws/{code}/norms/{norm}/relationships` | Relationship metadata for a norm |
| `GET` | `/corpus/coverage` | Coverage statistics for the loaded corpus |
| `GET` | `/corpus/source-limitations` | Non-imported source entries with optional filters |
| `GET` | `/search` | Full-text search; `?q=` required, `?codes=` optional |
| `GET` | `/openapi.json` | OpenAPI document (machine-readable) |

## URL encoding

Norm paths that contain `/` or `:` must be URL-encoded in HTTP:

```
GET /laws/egbgb/norms/art%3A246a%2Fpar%3A1
```

In MCP tool calls, use the canonical path directly: `art:246a/par:1`.

## Example requests

### List laws

```bash
curl http://localhost:8080/laws
curl "http://localhost:8080/laws?query=datenschutz"
```

### Fetch a norm

```bash
curl http://localhost:8080/laws/bgb/norms/par%3A242
```

### Search

```bash
curl "http://localhost:8080/search?q=Treu+und+Glauben"
curl "http://localhost:8080/search?q=Datenschutz&codes=dsgvo"
```

### Corpus coverage

```bash
curl http://localhost:8080/corpus/coverage
```

## Error responses

All endpoints return structured errors in JSON:

```json
{
  "error": "not_found",
  "message": "Law 'xyz' not found",
  "code": "xyz"
}
```

HTTP status codes:

| Code | Meaning |
| --- | --- |
| `200` | Success |
| `404` | Law or norm not found |
| `409` | Conflict (e.g. ambiguous alias) |
| `422` | Unprocessable entity (invalid input) |
| `503` | Runtime not ready (dataset not loaded) |

## Related

- [OpenAPI reference](openapi.md) — full schema documentation.
- [MCP tools reference](../tools/list_laws.md) — equivalent MCP surface.
- [MCP and HTTP surface](../concepts/mcp-and-http-surface.md) — architecture overview.
