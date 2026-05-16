# `list_laws`

List supported laws, optionally filtered by law metadata.

## Parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `query` | `string` | no | Free-text filter applied to law metadata (abbreviation, full name, jurisdiction). |

## Returns

An object with a `laws` array. Each entry contains:

```typescript
{
  laws: Array<{
    code: string;          // law abbreviation, e.g. "bgb"
    title: string;         // full official title
    jurisdiction: string;  // e.g. "federal", "eu"
    source_url: string;    // official source URL
    norm_count: number;    // number of normalized norms
  }>
}
```

## Example

```python
result = mcp_client.call_tool("list_laws", {})
```

```json
{
  "laws": [
    {
      "code": "bgb",
      "title": "Bürgerliches Gesetzbuch",
      "jurisdiction": "federal",
      "source_url": "https://www.gesetze-im-internet.de/bgb/",
      "norm_count": 2385
    }
  ]
}
```

With a query filter:

```python
result = mcp_client.call_tool("list_laws", {"query": "datenschutz"})
```

## Notes

- Returns all loaded laws when `query` is omitted or `null`.
- Query matching is case-insensitive and partial.
- Laws with terminal state `imported` are returned; laws with other
  terminal states appear in `get_source_limitations` output.

## Related

- [`get_law`](get_law.md) — fetch full detail for one law code.
- [`search_laws`](search_laws.md) — full-text search across norm content.

## Source

`mcp/server.py` — `@app.tool()` definition for `list_laws`.
