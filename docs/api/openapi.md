# OpenAPI reference

The HTTP API is documented via OpenAPI 3.1.

A static snapshot of the schema is committed at
[`docs/api/openapi.json`](https://github.com/klein-business/legal-text-mcp-de/blob/main/docs/api/openapi.json)
and is updated on each release.

## Live schema

When the server is running, the live OpenAPI document is available at:

```
http://localhost:8080/openapi.json
```

The interactive Swagger UI is at:

```
http://localhost:8080/docs
```

And ReDoc at:

```
http://localhost:8080/redoc
```

## Key schemas

### LawListResponse

```json
{
  "laws": [
    {
      "code": "bgb",
      "title": "Bürgerliches Gesetzbuch",
      "jurisdiction": "federal",
      "norm_count": 2385
    }
  ]
}
```

### NormRecord

```json
{
  "code": "bgb",
  "norm": "par:242",
  "heading": "Leistung nach Treu und Glauben",
  "text": "...",
  "provenance": {
    "source_url": "...",
    "fetch_timestamp": "...",
    "content_hash": "sha256:..."
  }
}
```

### ErrorResponse

```json
{
  "error": "not_found",
  "message": "Law 'xyz' not found",
  "code": "xyz"
}
```

## Related

- [HTTP API overview](index.md) — endpoints and examples.
- [MCP tools reference](../tools/list_laws.md) — equivalent MCP surface.
