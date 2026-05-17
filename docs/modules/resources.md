---
type: documentation
entity: module
module: "resources"
version: 1.0
---

# Module: resources

> Part of [legal-text-mcp-de](../overview.md)

## Overview

The `src/legal_text_mcp_de/resources/` package implements the MCP Resource layer
for the `legal://` URI scheme. Resources complement the tool surface: where tools
answer point queries, resources expose full law and norm texts as readable
Markdown that MCP clients can embed directly into context.

### Responsibility

This module is responsible for:

- registering all `legal://` URI handlers on the FastMCP app;
- rendering law headers and norm texts to LLM-friendly Markdown;
- exposing corpus coverage, source limitations, and the bundle manifest as JSON
  resources.

It is not responsible for resolving citations (see `legal_texts/resolver.py`),
running search (see `legal_texts/search.py`), or authenticating clients.

### Dependencies

| Dependency | Type | Purpose |
| ---------- | ---- | ------- |
| `mcp.server.fastmcp.FastMCP` | library | `@app.resource()` registration. |
| `legal_text_mcp_de.legal_texts.runtime.LegalTextRuntime` | internal | Data access for laws, norms, coverage, and limitations. |

## Structure

| Path | Type | Purpose |
| ---- | ---- | ------- |
| `src/legal_text_mcp_de/resources/handlers.py` | file | `register_resources` — registers all 10 `legal://` URI handlers. |
| `src/legal_text_mcp_de/resources/markdown_render.py` | file | `render_law`, `render_norm` — pure functions; no I/O. |
| `src/legal_text_mcp_de/resources/__init__.py` | file | Re-exports `register_resources`. |

## Key Symbols

| Symbol | Kind | Location | Purpose |
| ------ | ---- | -------- | ------- |
| `register_resources` | function | `handlers.py` | Registers all 10 `legal://` URIs on the FastMCP app. |
| `render_law` | function | `markdown_render.py` | Renders law header + clickable norm index as Markdown. |
| `render_norm` | function | `markdown_render.py` | Renders a single norm with provenance line and cross-references. |

## Registered URIs

| URI | Content type | Description |
| --- | ------------ | ----------- |
| `legal://laws` | JSON | First page of laws (cursor=0, limit=50). |
| `legal://laws/page/{cursor}/{limit}` | JSON | Paginated law list (limit clamped to 1–500). |
| `legal://laws/{code}` | Markdown | Law header + norm index. |
| `legal://laws/{code}/full` | Markdown | Full law text — header followed by all norm texts. |
| `legal://laws/{code}/norms/{norm_id}` | Markdown | Single norm with provenance and cross-reference links. |
| `legal://laws/{code}/norms/{norm_id}/relationships` | JSON | Related-norm metadata. |
| `legal://laws/{code}/source` | JSON | Source metadata for a law. |
| `legal://corpus/coverage` | JSON | Per-law inventory, counts, and source families. |
| `legal://corpus/limitations` | JSON | Known source limitations and gaps. |
| `legal://corpus/manifest` | JSON | Bundle-level provenance: bundle ID, version, source versions. |

## Markdown Output Shape

`render_norm` produces:

```
# {display_id} {code} — {title}

**Stand:** {stand_date} · **Retrieved:** {retrieved_at} · **Source:** [{url}]({url})

{norm text}

**Querverweise:** {related canonical IDs}
```

`render_law` produces an H1 header with stand date and norm count, followed by a
bullet list of norms where each bullet is a `legal://laws/{id}/norms/{norm_id}`
link.

## Pagination

Pagination on `legal://laws/page/{cursor}/{limit}` uses zero-based integer
offsets, not opaque cursors. The response includes `next_cursor` (an integer or
`null`) and `total` so clients can detect the last page without over-fetching.

## Inventory Notes

- **Coverage**: full; all 10 URIs are covered by integration tests.
- **Notes**: FastMCP 1.27.x routes URI template variables only through path
  components, not query-string parameters. Pagination is therefore expressed as
  path segments (`/page/{cursor}/{limit}`), not `?cursor=…`.
- **See also**: [mcp-resources feature](../features/mcp-resources.md) for the
  user-facing URI catalogue and usage examples.
