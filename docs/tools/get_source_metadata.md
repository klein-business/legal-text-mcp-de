# `get_source_metadata`

Return source provenance for all laws or one law code/alias.

## Parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `code` | `string` | no | Law abbreviation or alias. If omitted, returns provenance for all loaded laws. |

## Returns

When `code` is provided:

```typescript
{
  code: string;
  source_url: string;       // original official source URL
  fetch_timestamp: string;  // ISO 8601 timestamp of the fetch
  content_hash: string;     // SHA-256 of the source payload
  terminal_state: string;   // "imported" for successfully loaded laws
  source_family: string;    // "gesetze-im-internet" or "eur-lex"
}
```

When `code` is omitted, returns an object with a `sources` array of the above shape.

## Example

Provenance for a single law:

```python
result = mcp_client.call_tool("get_source_metadata", {"code": "bgb"})
```

```json
{
  "code": "bgb",
  "source_url": "https://www.gesetze-im-internet.de/bgb/",
  "fetch_timestamp": "2026-05-15T10:23:00Z",
  "content_hash": "sha256:abc123...",
  "terminal_state": "imported",
  "source_family": "gesetze-im-internet"
}
```

All sources:

```python
result = mcp_client.call_tool("get_source_metadata", {})
```

## Notes

- This tool returns only successfully imported laws. For laws that failed
  to load, use `get_source_limitations`.
- The `content_hash` can be used to detect if the upstream source has
  changed since the corpus was generated.

## Related

- [`get_source_limitations`](get_source_limitations.md) — limitations and non-imported sources.
- [`get_corpus_coverage`](get_corpus_coverage.md) — aggregate coverage statistics.

## Source

`mcp/server.py` — `@app.tool()` definition for `get_source_metadata`.
