# `get_corpus_coverage`

Return generated package, manifest, limitation, and relationship coverage metadata.

## Parameters

This tool takes no parameters.

## Returns

```typescript
{
  package: {
    generated_at: string;   // ISO 8601 timestamp
    generator_version: string;
    total_laws: number;
    total_norms: number;
  };
  manifest: {
    total_entries: number;
    by_terminal_state: {
      imported: number;
      parse_failed: number;
      source_unavailable: number;
      unsupported_format: number;
      excluded_by_policy: number;
    };
  };
  limitations: {
    total: number;
    by_source_family: Record<string, number>;
  };
  relationships: {
    total: number;
    has_relationships: boolean;
  };
}
```

## Example

```python
result = mcp_client.call_tool("get_corpus_coverage", {})
```

```json
{
  "package": {
    "generated_at": "2026-05-15T08:00:00Z",
    "generator_version": "1.0.0",
    "total_laws": 312,
    "total_norms": 42853
  },
  "manifest": {
    "total_entries": 350,
    "by_terminal_state": {
      "imported": 312,
      "parse_failed": 5,
      "source_unavailable": 18,
      "unsupported_format": 12,
      "excluded_by_policy": 3
    }
  },
  "limitations": {
    "total": 38,
    "by_source_family": {
      "gesetze-im-internet": 30,
      "eur-lex": 8
    }
  },
  "relationships": {
    "total": 18540,
    "has_relationships": true
  }
}
```

## Notes

- When using the fixture corpus, counts will reflect the ~10 fixture laws.
- When using a generated production corpus, counts reflect the full dataset.
- `has_relationships` is `false` when the corpus was generated without the
  relationship-building step.

## Related

- [`get_source_limitations`](get_source_limitations.md) — detail on non-imported sources.
- [`get_source_metadata`](get_source_metadata.md) — provenance for individual laws.

## Source

`mcp/server.py` — `@app.tool()` definition for `get_corpus_coverage`.
