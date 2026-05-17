<!--
SPDX-License-Identifier: Apache-2.0
Copyright 2026 klein-business
-->

# MCP Resources

v2.0 exposes 10 read-only URIs under the `legal://` scheme. MCP clients can load these directly into the LLM context window — no tool call required.

## URI catalogue

| URI | Content type | Description |
|---|---|---|
| `legal://laws` | JSON | Paginated law index (first page, default 20 items) |
| `legal://laws/page/{cursor}/{limit}` | JSON | Explicit page with cursor token and limit |
| `legal://laws/{code}` | Markdown | Law header + norm index (e.g. `legal://laws/bgb`) |
| `legal://laws/{code}/full` | Markdown | Full law text — can be large for complex laws |
| `legal://laws/{code}/norms/{norm_id}` | Markdown | Single norm (e.g. `legal://laws/bgb/norms/par:433`) |
| `legal://laws/{code}/norms/{norm_id}/relationships` | JSON | Related-norm graph for a norm |
| `legal://laws/{code}/source` | JSON | Provenance: source URL, fetch timestamp, content hash |
| `legal://corpus/coverage` | JSON | Aggregate counts by law type + schema version |
| `legal://corpus/limitations` | JSON | Known gaps and caveats in source coverage |
| `legal://corpus/manifest` | JSON | Full bundle manifest with per-law metadata |

## Usage examples

### Load BGB § 433 directly

In a supporting MCP client, attach the resource URI before prompting:

```
Resource: legal://laws/bgb/norms/par:433
Question: Welche Pflichten hat der Verkäufer nach § 433 BGB?
```

### Check corpus coverage before research

```
Resource: legal://corpus/coverage
Question: Welche bayerischen Gesetze sind im Corpus?
```

### Paginate through the law index

```
Resource: legal://laws/page/0/50
```

Returns the first 50 laws. Use the `next_cursor` from the response for subsequent pages.

## Performance notes

- `legal://laws/{code}/full` is loaded synchronously into context. For large laws (e.g. HGB with 900+ norms), prefer per-norm URIs.
- Corpus metadata URIs (`coverage`, `limitations`, `manifest`) are fast — they read from the cached bundle manifest, not individual law files.
- Resources are read-only and have no side effects.

## See also

- [MCP-native architecture](../concepts/mcp-native.md)
- [MCP Prompts](../prompts/index.md) — use Resources together with Prompts for curated workflows
