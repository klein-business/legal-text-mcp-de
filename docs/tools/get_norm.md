# `get_norm`

Return one structured norm by canonical norm path or simple norm shorthand.

## Parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `code` | `string` | yes | Law abbreviation (e.g. `bgb`). Case-insensitive. |
| `norm` | `string` | yes | Canonical norm path (e.g. `par:242`) or simple shorthand (e.g. `242`). |

## Returns

A full norm record:

```typescript
{
  code: string;
  norm: string;          // canonical norm path
  heading: string;       // norm heading / title
  text: string;          // full normalized text
  text_html: string;     // normalized text as HTML (structure preserved)
  provenance: {
    source_url: string;
    fetch_timestamp: string;
    content_hash: string;
    parser_path: string;
  };
  metadata: {
    norm_type: string;   // "paragraph", "article", "section", etc.
    number: string;      // e.g. "242"
    sub_parts: string[]; // e.g. ["(1)", "(2)"]
  };
}
```

## Example

```python
result = mcp_client.call_tool("get_norm", {"code": "bgb", "norm": "242"})
```

```json
{
  "code": "bgb",
  "norm": "par:242",
  "heading": "Leistung nach Treu und Glauben",
  "text": "Der Schuldner ist verpflichtet, die Leistung so zu bewirken, wie Treu und Glauben mit Rücksicht auf die Verkehrssitte es erfordern.",
  "provenance": {
    "source_url": "https://www.gesetze-im-internet.de/bgb/__242.html",
    "fetch_timestamp": "2026-05-15T10:23:00Z",
    "content_hash": "sha256:def456...",
    "parser_path": "paragraph"
  },
  "metadata": {
    "norm_type": "paragraph",
    "number": "242"
  }
}
```

## Norm path format

| Input | Resolved as |
| --- | --- |
| `242` | `par:242` (paragraph 242) |
| `par:242` | `par:242` (explicit) |
| `art:2` | `art:2` (article 2) |
| `art:246a/par:1` | nested article/paragraph (URL-encode in HTTP) |

## Notes

- Norm path resolution is tolerant of common shorthand forms.
- Returns a structured error if the norm is not found.
- For complex nested paths, prefer the canonical `type:number` form.

## Related

- [`resolve_citation`](resolve_citation.md) — resolve a structured citation with sub-unit precision.
- [`get_related_norms`](get_related_norms.md) — find norms related to this one.

## Source

`mcp/server.py` — `@app.tool()` definition for `get_norm`.
