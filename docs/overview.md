---
type: documentation
entity: project-overview
version: 1.2
---

# legal-text-mcp-de

## Purpose

`legal-text-mcp-de` provides source-backed German legal texts through MCP and a small HTTP API. Phase 1 is focused on reliable local/server-side data handling: reproducible source import, normalized legal text records, deterministic search, exact citation resolution, and structured provenance/error contracts.

The project is proprietary commercial software. It does not provide legal advice and does not include SaaS, billing, account, authorization, or multi-tenant features.

## Architecture

```text
Official sources
  | gesetze-im-internet.de XML ZIPs
  | Publications Office / Cellar XML for DSGVO
  v
Raw snapshot manifest
  | source URL, retrieval time, stand date, SHA-256
  v
Normalizer and validator
  | laws.json, norms.json, readiness.json, search-index.json
  v
LegalTextRuntime
  | registry, dataset, resolver, search, source metadata
  +--> FastMCP tools
  +--> FastAPI HTTP API + OpenAPI
```

### Tech Stack

- Python 3.12
- FastMCP via `mcp[cli]`
- FastAPI and Uvicorn for the HTTP API
- Pydantic settings for runtime configuration
- Standard-library XML/ZIP/JSON/hash tooling for source import and normalization
- Pytest for unit, parser, service, transport, and release-gate tests

## Modules

| Module | Description | Documentation |
| ------ | ----------- | ------------- |
| mcp-server | MCP server, HTTP app, legal text services, importer, normalizer, resolver, search, and tests. | [Detail](modules/mcp-server.md) |
| container-runtime | Docker packaging for the server with external normalized dataset mounting. | [Detail](modules/container-runtime.md) |
| data-preparation | Legacy helper workflow for Markdown-era data preparation; not the Phase 1 production source path. | [Detail](modules/data-preparation.md) |
| google-adk-agent | Optional legacy demo agent kept outside the Phase 1 reliability surface. | [Detail](modules/google-adk-agent.md) |

## Key Features

| Feature | Description | Documentation |
| ------- | ----------- | ------------- |
| supported-laws | Phase 1 law set and canonical IDs. | [Detail](features/supported-laws.md) |
| source-provenance | Raw/normalized data separation and source metadata rules. | [Detail](features/source-provenance.md) |
| law-loading-and-indexing | Normalized dataset loading, readiness, and search index behavior. | [Detail](features/law-loading-and-indexing.md) |
| mcp-law-tools | Stable MCP tool surface. | [Detail](features/mcp-law-tools.md) |
| api-contracts | Shared JSON response and error contracts. | [Detail](features/api-contracts.md) |
| http-api | FastAPI endpoints and OpenAPI contract. | [Detail](features/http-api.md) |
| known-issues | Explicit Phase 1 limitations and non-goals. | [Detail](features/known-issues.md) |

## Development

### Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r mcp/requirements.txt
```

### Run MCP

```bash
DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
python mcp/server.py
```

### Run HTTP API

```bash
DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
uvicorn http_api:create_http_app --factory --host 127.0.0.1 --port 8080
```

### Testing

```bash
PYTHONPATH=mcp python scripts/verify_phase1_release.py
```

This command includes the full test suite plus real local HTTP and MCP streamable-HTTP E2E checks.

```bash
PYTHONPATH=mcp python scripts/verify_e2e.py
```

This command runs only the local network E2E check. It starts temporary HTTP and MCP servers with the fixture dataset, verifies HTTP endpoints through network requests, and verifies MCP through the official streamable-HTTP client.

## References

- [Model Context Protocol](https://modelcontextprotocol.io)
- [gesetze-im-internet.de](https://www.gesetze-im-internet.de)
- [EUR-Lex CELEX 32016R0679](https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679)
- Legacy documentation archive: [docs-legacy/summary.md](../docs-legacy/summary.md)
