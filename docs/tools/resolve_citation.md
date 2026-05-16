# `resolve_citation`

Resolve a structured legal citation without free-form parsing.

This tool resolves precise legal citations (e.g. "§ 242 Abs. 1 Satz 2 BGB") using
structured parameters rather than parsing free-form citation strings. This avoids
ambiguity and ensures deterministic resolution.

## Parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `code` | `string` | yes | Law abbreviation (e.g. `bgb`). |
| `unit` | `string` | yes | Top-level unit type: `paragraph` (`§`) or `article` (`Art.`). |
| `paragraph_or_article` | `string` | yes | Number of the paragraph or article (e.g. `242`). |
| `child_unit` | `string` | no | Sub-unit type within the top-level unit (e.g. `paragraph` for nested §). |
| `child_value` | `string` | no | Sub-unit number (e.g. `1` for nested § 1). |
| `absatz` | `string` | no | Absatz (subsection) number, e.g. `1` for Abs. 1. |
| `satz` | `string` | no | Satz (sentence) number, e.g. `2` for Satz 2. |
| `nummer` | `string` | no | Nummer (list item) number, e.g. `3` for Nr. 3. |
| `buchstabe` | `string` | no | Buchstabe (letter) within a list item, e.g. `a`. |

## Returns

The norm record for the resolved citation, equivalent to `get_norm` output.

## Example

Resolve "§ 242 BGB":

```python
result = mcp_client.call_tool("resolve_citation", {
    "code": "bgb",
    "unit": "paragraph",
    "paragraph_or_article": "242"
})
```

Resolve "Art. 5 Abs. 1 lit. a DSGVO":

```python
result = mcp_client.call_tool("resolve_citation", {
    "code": "dsgvo",
    "unit": "article",
    "paragraph_or_article": "5",
    "absatz": "1",
    "buchstabe": "a"
})
```

```json
{
  "code": "dsgvo",
  "norm": "art:5",
  "heading": "Grundsätze für die Verarbeitung personenbezogener Daten",
  "text": "...",
  "citation_fragment": "Art. 5 Abs. 1 lit. a"
}
```

## Notes

- Use this tool when you have a structured citation (from a document, contract, or court ruling)
  and want to look up the exact text.
- Do not use this for free-form queries — use `search_laws` for that.
- `child_unit` / `child_value` are used for laws that have nested paragraph structures
  (e.g. EGBGB Art. 246a § 1).

## Related

- [`get_norm`](get_norm.md) — simpler path when you already have the norm path.
- [`search_laws`](search_laws.md) — when you have keywords, not a structured citation.

## Source

`mcp/server.py` — `@app.tool()` definition for `resolve_citation`.
