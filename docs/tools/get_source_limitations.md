# `get_source_limitations`

Return official-source limitations with optional metadata filters.

This tool exposes the non-imported portion of the corpus — sources that exist
in the manifest but could not be fully ingested. Downstream consumers can use
this to understand coverage gaps before relying on the corpus for a specific law.

## Parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `source_family` | `string` | no | Filter by source family: `gesetze-im-internet` or `eur-lex`. |
| `terminal_state` | `string` | no | Filter by terminal state: `parse_failed`, `source_unavailable`, `unsupported_format`, `excluded_by_policy`. |
| `state_code` | `string` | no | Filter by German state code (for Länder laws). |
| `law_id` | `string` | no | Filter by a specific law identifier. |

## Returns

```typescript
{
  limitations: Array<{
    law_id: string;
    source_family: string;
    terminal_state: string;
    reason: string;
    source_url: string | null;
    state_code: string | null;
  }>;
  total: number;
}
```

## Example

All limitations:

```python
result = mcp_client.call_tool("get_source_limitations", {})
```

Parse failures only:

```python
result = mcp_client.call_tool("get_source_limitations", {
    "terminal_state": "parse_failed"
})
```

```json
{
  "limitations": [
    {
      "law_id": "somelaw",
      "source_family": "gesetze-im-internet",
      "terminal_state": "parse_failed",
      "reason": "XML structure not recognized by parser",
      "source_url": "https://www.gesetze-im-internet.de/somelaw/",
      "state_code": null
    }
  ],
  "total": 1
}
```

## Notes

- Returns an empty `limitations` array when all sources are `imported`.
- Each non-imported source has exactly one terminal state; there are no
  partial states.
- Use `get_corpus_coverage` to get aggregate counts by terminal state.

## Related

- [`get_corpus_coverage`](get_corpus_coverage.md) — aggregate coverage statistics.
- [`get_source_metadata`](get_source_metadata.md) — provenance for successfully imported laws.

## Source

`mcp/server.py` — `@app.tool()` definition for `get_source_limitations`.
