# `search_laws`

Search normalized legal texts with optional law-code filters.

## Parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `query` | `string` | yes | Search query string (keywords, phrases). |
| `codes` | `string[]` | no | Limit search to specific law codes (e.g. `["bgb", "dsgvo"]`). |

## Returns

```typescript
{
  results: Array<{
    code: string;
    norm: string;
    heading: string;
    score: number;      // relevance score (higher is better)
    text_preview: string;  // matching excerpt, ~200 characters
  }>;
  total: number;
}
```

## Example

```python
result = mcp_client.call_tool("search_laws", {"query": "Treu und Glauben"})
```

```json
{
  "results": [
    {
      "code": "bgb",
      "norm": "par:242",
      "heading": "Leistung nach Treu und Glauben",
      "score": 0.95,
      "text_preview": "Der Schuldner ist verpflichtet, die Leistung so zu bewirken, wie Treu und Glauben..."
    }
  ],
  "total": 1
}
```

Scoped to specific laws:

```python
result = mcp_client.call_tool("search_laws", {
    "query": "personenbezogene Daten",
    "codes": ["dsgvo"]
})
```

## Notes

- Search uses fuzzy matching via `rapidfuzz` on normalized text.
- Results are ranked by relevance score and capped at a bounded result set.
- Passing `codes` significantly narrows the search space and improves result relevance.
- The search index is built at corpus load time; runtime queries are fast.

## Related

- [`get_norm`](get_norm.md) — fetch full text when you have the norm path.
- [`resolve_citation`](resolve_citation.md) — look up a specific citation.
- [`list_laws`](list_laws.md) — discover available law codes to use as filters.

## Source

`mcp/server.py` — `@app.tool()` definition for `search_laws`.
