# `get_law`

Return law metadata and normalized norm summaries for a law code or alias.

## Parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `code` | `string` | yes | Law abbreviation (e.g. `bgb`) or a known alias (e.g. `BGB`). Case-insensitive. |

## Returns

An object with law metadata and a list of norm summaries:

```typescript
{
  code: string;
  title: string;
  jurisdiction: string;
  source_url: string;
  provenance: {
    fetch_timestamp: string;  // ISO 8601
    content_hash: string;     // SHA-256 hex
  };
  norms: Array<{
    norm: string;       // canonical norm path, e.g. "par:242"
    heading: string;    // norm heading / title
    text_preview: string;  // first 200 characters of normalized text
  }>;
}
```

## Example

```python
result = mcp_client.call_tool("get_law", {"code": "bgb"})
```

```json
{
  "code": "bgb",
  "title": "Bürgerliches Gesetzbuch",
  "jurisdiction": "federal",
  "source_url": "https://www.gesetze-im-internet.de/bgb/",
  "provenance": {
    "fetch_timestamp": "2026-05-15T10:23:00Z",
    "content_hash": "sha256:abc123..."
  },
  "norms": [
    {
      "norm": "par:242",
      "heading": "Leistung nach Treu und Glauben",
      "text_preview": "Der Schuldner ist verpflichtet, die Leistung so zu bewirken..."
    }
  ]
}
```

## Notes

- Code lookup is case-insensitive.
- Known aliases (e.g. `BGB` → `bgb`, `DSGVO` → `dsgvo`) are resolved automatically.
- Returns a structured error if the code is not found.

## Related

- [`get_norm`](get_norm.md) — fetch full text for a single norm.
- [`list_laws`](list_laws.md) — discover available law codes.

## Source

`mcp/server.py` — `@app.tool()` definition for `get_law`.
