# `get_related_norms`

Return generated relationship metadata for one norm when package relationships exist.

## Parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `code` | `string` | yes | Law abbreviation (e.g. `bgb`). |
| `norm` | `string` | yes | Canonical norm path or shorthand (e.g. `242` or `par:242`). |

## Returns

```typescript
{
  code: string;
  norm: string;
  relationships: Array<{
    target_code: string;    // law code of the related norm
    target_norm: string;    // canonical norm path
    relationship_type: string;  // "references", "implements", "amends", etc.
    confidence: number;     // 0.0–1.0
  }>;
  has_relationships: boolean;
}
```

When the corpus was generated without the relationship step, `has_relationships`
is `false` and `relationships` is an empty array.

## Example

```python
result = mcp_client.call_tool("get_related_norms", {"code": "bgb", "norm": "242"})
```

```json
{
  "code": "bgb",
  "norm": "par:242",
  "relationships": [
    {
      "target_code": "bgb",
      "target_norm": "par:241",
      "relationship_type": "references",
      "confidence": 0.87
    }
  ],
  "has_relationships": true
}
```

## Notes

- Returns an empty `relationships` list when no relationships were generated
  for this norm, or when the corpus was generated without the relationship step.
- `has_relationships: false` at the top level indicates the corpus has no
  relationship data at all (not just for this norm).
- Relationship data is generated offline by the `prepare_data/` pipeline and
  is not available in the fixture corpus.

## Related

- [`get_norm`](get_norm.md) — fetch the norm text.
- [`get_corpus_coverage`](get_corpus_coverage.md) — check if relationship data is present.

## Source

`mcp/server.py` — `@app.tool()` definition for `get_related_norms`.
