---
type: documentation
entity: feature
feature: "mcp-law-tools"
version: 1.2
---

# Feature: mcp-law-tools

> Part of [legal-text-mcp-de](../overview.md)

## Summary

The MCP law tools expose the Phase 1 legal text runtime to MCP clients. They return JSON-compatible objects directly and share the same registry, resolver, search, readiness, and source metadata services as the HTTP API.

## How It Works

### User Flow

1. Start the server with `DATASET_PATH` pointing at a validated normalized dataset.
2. Connect an MCP client to `http://localhost:8001/mcp`.
3. Discover laws with `list_laws`.
4. Fetch law metadata with `get_law`.
5. Fetch exact norms with `get_norm` or structured citations with `resolve_citation`.
6. Search loaded laws with `search_laws`.
7. Inspect provenance with `get_source_metadata`.

### Technical Flow

1. `create_mcp_app` builds a FastMCP application.
2. Tool handlers call methods on `LegalTextRuntime`.
3. Runtime delegates to `LawRegistry`, `NormalizedDataset`, `resolve_citation`, and `SearchService`.
4. Domain errors are returned as `{"error": {"code", "message", "details"}}`.
5. Successful responses are plain dictionaries/lists, not JSON strings.

## Implementation

| Module | Symbols | Role |
| ------ | ------- | ---- |
| [mcp-server](../modules/mcp-server.md) | `create_mcp_app` | Registers the MCP tool surface. |
| [mcp-server](../modules/mcp-server.md) | `LegalTextRuntime` | Shared service layer for all tools. |
| [mcp-server](../modules/mcp-server.md) | `LawRegistry` | Resolves aliases and exposes canonical IDs. |
| [mcp-server](../modules/mcp-server.md) | `resolve_citation` | Handles exact citation requests. |
| [mcp-server](../modules/mcp-server.md) | `SearchService` | Handles deterministic search. |

## Tool Contract

| Tool | Required Inputs | Output |
| ---- | --------------- | ------ |
| `list_laws` | optional `query` | Law summaries with canonical ID, display code, display name, source kind, and norm count. |
| `get_law` | `code` | Law metadata and normalized norm summaries. |
| `get_norm` | `code`, `norm` | Structured norm data for a canonical norm path or shorthand. |
| `resolve_citation` | `code`, `unit`, `paragraph_or_article`, optional child/subdivision fields | Citation response with law, norm, source, canonical citation, and optional selection. |
| `search_laws` | `query`, optional `codes` | Deterministically ordered search results with plain snippets and normalized scores. |
| `get_source_metadata` | optional `code` | Source metadata for one law or all supported laws. |

## Edge Cases & Limitations

- Missing datasets return `DATASET_NOT_READY`.
- Unknown laws return `LAW_NOT_FOUND` with suggestions.
- Ambiguous aliases return `AMBIGUOUS_LAW_ALIAS`; no law is selected silently.
- Missing norms return `NORM_NOT_FOUND`.
- Invalid citation shapes return `INVALID_CITATION`.
- Empty or punctuation-only search input returns `INVALID_QUERY`.
- The tools do not provide legal interpretation or hallucinated fallback text.
- A plain HTTP probe against `/mcp` is not a valid MCP readiness check and may return `406 Not Acceptable`; use a real MCP streamable-HTTP client handshake for E2E verification.

## E2E Verification

`scripts/verify_e2e.py` starts the MCP server process with the fixture dataset, connects through `mcp.client.streamable_http.streamablehttp_client`, initializes a `ClientSession`, verifies the Phase 1 tool list, and calls `get_norm`, `resolve_citation`, `search_laws`, and a structured missing-norm error path.

## Related Features

- [api-contracts](api-contracts.md)
- [law-loading-and-indexing](law-loading-and-indexing.md)
- [source-provenance](source-provenance.md)
