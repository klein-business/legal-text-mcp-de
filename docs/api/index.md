# HTTP API overview

The HTTP API is a FastAPI application exposing the same runtime as the
MCP server. It is intended for non-MCP clients such as scripts, cURL,
or other HTTP consumers.

Default port: **8001** (from `PORT` env / `settings.port`).

## Starting the HTTP API

```bash
DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
uv run uvicorn http_api:app --host 127.0.0.1 --port 8001
```

Equivalent CLI subcommand (v2.1.0+):

```bash
legal-text-mcp-de http --host 127.0.0.1
```

Pass `--port <N>` to override the default.

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
curl http://localhost:8001/laws
curl "http://localhost:8001/laws?query=datenschutz"
```

### Fetch a norm

```bash
curl http://localhost:8001/laws/bgb/norms/par%3A242
```

### Search

```bash
curl "http://localhost:8001/search?q=Treu+und+Glauben"
curl "http://localhost:8001/search?q=Datenschutz&codes=dsgvo"
```

### Corpus coverage

```bash
curl http://localhost:8001/corpus/coverage
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

## Environment variables

The HTTP API reads these in addition to the MCP server's settings:

| Variable | Default | Effect |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8001` | Bind port used by both `http` CLI and direct uvicorn invocation |
| `DATASET_PATH` | unset (auto-download) | Path to corpus bundle |
| `STRICT_STARTUP` | `false` | Fail fast on dataset load errors |
| `MAX_REQUEST_BODY_BYTES` | `1048576` | Reject `Content-Length > N` with 413 (defence-in-depth on top of the reverse-proxy limit) |

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
