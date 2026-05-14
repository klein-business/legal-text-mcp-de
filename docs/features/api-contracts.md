---
type: documentation
entity: feature
feature: "api-contracts"
version: 1.2
---

# Feature: api-contracts

> Part of [legal-text-mcp-de](../overview.md)

## Summary

Phase 1 exposes one shared domain contract through MCP and HTTP. Transport handlers are intentionally thin; they return the same law, norm, citation, search, source metadata, readiness, and error shapes.

## MCP Tools

| Tool | Inputs | Notes |
| ---- | ------ | ----- |
| `list_laws` | `query?: string` | Lists laws and optional metadata matches. |
| `get_law` | `code: string` | Accepts canonical IDs and registered aliases. |
| `get_norm` | `code: string`, `norm: string` | Accepts canonical norm IDs like `par:312` and shorthand like `§ 312`. |
| `resolve_citation` | `code`, `unit`, `paragraph_or_article`, optional `child_unit`, `child_value`, `absatz`, `satz`, `nummer`, `buchstabe` | Exact structured citation resolver. |
| `search_laws` | `query: string`, `codes?: string[]` | Deterministic plain-text search. |
| `get_source_metadata` | `code?: string` | Provenance for one law or all laws. |

MCP tools return JSON-compatible dictionaries/lists directly. Returning serialized JSON strings is a regression.

## HTTP Endpoints

| Endpoint | Purpose |
| -------- | ------- |
| `GET /health` | Process health independent of dataset readiness. |
| `GET /ready` | Dataset readiness state. |
| `GET /laws` | Law list. |
| `GET /laws/{code}` | Law metadata and norm summaries. |
| `GET /laws/{code}/norms/{norm}` | Exact norm lookup. |
| `GET /search` | Search with `query` and optional repeated `codes` parameters. |
| `GET /openapi.json` | OpenAPI contract. |

## Error Contract

Errors use this envelope:

```json
{
  "error": {
    "code": "LAW_NOT_FOUND",
    "message": "Law not found: xyz",
    "details": {}
  }
}
```

Supported codes:

- `LAW_NOT_FOUND`
- `NORM_NOT_FOUND`
- `AMBIGUOUS_LAW_ALIAS`
- `SOURCE_UNAVAILABLE`
- `DATASET_NOT_READY`
- `INVALID_CITATION`
- `INVALID_QUERY`

HTTP maps these errors to stable non-2xx responses. MCP returns the same object shape as a tool result.

## Citation IDs

Canonical norm IDs use `par:<value>` or `art:<value>`. EGBGB article-plus-section citations use a child path, for example:

```text
egbgb/art:246a/par:1
```

For HTTP path transport, slash-containing norm IDs must be URL encoded:

```text
/laws/egbgb/norms/art%3A246a%2Fpar%3A1
```

## Search Contract

Search normalizes Unicode, case-folds input, collapses whitespace, tokenizes as plain text, and uses AND semantics for unique query tokens. Snippets are plain text and do not include HTML fragments. Public scores are normalized so the top result is `1.0`, with stable tie-breaking by score, canonical law ID, and norm ID.

## Verification

Transport contracts are covered at two levels:

- in-process contract tests for MCP tool registration, HTTP route schemas, structured errors, resolver behavior, and search behavior;
- local network E2E through `scripts/verify_e2e.py`, which starts real HTTP and MCP streamable-HTTP server processes and calls them through network clients.
