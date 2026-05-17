---
type: documentation
entity: feature
feature: "mcp-resources"
version: 1.0
---

# Feature: mcp-resources

> Part of [legal-text-mcp-de](../overview.md)

## Summary

v2 adds 10 `legal://` URI resources to the MCP surface. Resources let clients
read full law and norm texts as Markdown without calling a tool, which reduces
round-trips and keeps law text directly in the LLM's context window.

## How It Works

### User Flow

1. Connect an MCP client to the server.
2. Call `resources/list` to discover registered `legal://` URIs.
3. Subscribe to or read individual resources using `resources/read`.
4. Embed the returned Markdown or JSON directly in the LLM prompt.

### URI Catalogue

| URI | MIME type | Content |
| --- | --------- | ------- |
| `legal://laws` | application/json | First page of laws (50 entries, cursor=0). |
| `legal://laws/page/{cursor}/{limit}` | application/json | Paginated law list. |
| `legal://laws/{code}` | text/markdown | Law header + norm index with `legal://` links. |
| `legal://laws/{code}/full` | text/markdown | Full law text — header + all norm texts joined by `---`. |
| `legal://laws/{code}/norms/{norm_id}` | text/markdown | Single norm text, Stand-Datum, retrieved-at, and cross-references. |
| `legal://laws/{code}/norms/{norm_id}/relationships` | application/json | Related-norm metadata. |
| `legal://laws/{code}/source` | application/json | Source metadata (URL, kind, stand date, content hash). |
| `legal://corpus/coverage` | application/json | Per-law inventory, law/norm counts, source families. |
| `legal://corpus/limitations` | application/json | Known source limitations and gaps. |
| `legal://corpus/manifest` | application/json | Bundle provenance: bundle ID, version, source-version pins, retrieved-at. |

### Technical Flow

1. `server.py` calls `register_resources(app, runtime)` during app construction.
2. Each URI handler calls the appropriate `LegalTextRuntime` method.
3. Law and norm responses pass through `render_law` / `render_norm` in
   `resources/markdown_render.py` and are returned as Markdown strings.
4. Coverage, limitations, manifest, and relationship responses are serialised as
   indented JSON with `ensure_ascii=False`.
5. Errors are returned as Markdown error messages (law/norm URIs) or JSON
   `{"error": "…"}` payloads (JSON URIs) rather than raising, so clients never
   receive an empty resource.

## Implementation

| Module | Symbols | Role |
| ------ | ------- | ---- |
| [resources](../modules/resources.md) | `register_resources` | Registration entry point. |
| [resources](../modules/resources.md) | `render_law`, `render_norm` | Markdown rendering (pure functions). |
| [mcp-server](../modules/mcp-server.md) | `LegalTextRuntime` | Data access layer. |

## Markdown Resource Shape

A single-norm resource (`legal://laws/bgb/norms/§ 305`) looks like:

```markdown
# § 305 BGB — Einbeziehung Allgemeiner Geschäftsbedingungen in den Vertrag

**Stand:** 2024-01-01 · **Retrieved:** 2026-05-17T00:00:00Z · **Source:** [https://…](https://…)

(1) Allgemeine Geschäftsbedingungen sind alle…

**Querverweise:** bgb, uwg_2004
```

## Pagination

`legal://laws/page/{cursor}/{limit}`:

- `cursor` is a zero-based integer offset.
- `limit` is clamped server-side to 1–500.
- `next_cursor` is `null` when no further pages exist.

## Edge Cases

- Unknown `{code}` values return a Markdown error document rather than HTTP 404.
- Unknown `{norm_id}` values return a Markdown error document.
- Corpus resources degrade gracefully when the dataset is in fixture mode (no
  `package.json`).

## Related

- [resources module](../modules/resources.md)
- [mcp-law-tools](mcp-law-tools.md)
- [mcp-prompts](mcp-prompts.md)
