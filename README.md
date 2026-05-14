# legal-text-mcp-de

`legal-text-mcp-de` is a Python MCP server for loading, validating, searching, and resolving German legal texts with source provenance. It focuses on a reliable local/server-side legal text foundation: no SaaS, no billing, no accounts, no tenant model, and no legal advice.

The server uses `gesetze-im-internet.de` as the canonical source for supported German laws. DSGVO is handled separately through the official Publications Office / Cellar XML source and is not mixed into GII provenance.

Older repository documentation was archived under [docs-legacy/summary.md](docs-legacy/summary.md).

## Supported Scope

Supported canonical law IDs:

- `bgb`
- `egbgb`
- `ddg`
- `uwg_2004`
- `tdddg`
- `bdsg_2018`
- `bfsg`
- `vsbg`
- `pangv_2022`
- `dsgvo_eu_2016_679`

The data model separates raw snapshots from normalized serving packages. Every normalized law and norm carries canonical IDs, source URL, retrieval timestamp, stand-date status, content hash, and source-kind metadata.

## MCP Tools

| Tool | Purpose |
| ---- | ------- |
| `list_laws(query?: string)` | List supported laws, optionally filtered by metadata. |
| `get_law(code: string)` | Return law metadata and normalized norm summaries. |
| `get_norm(code: string, norm: string)` | Return one structured norm by canonical ID or shorthand. |
| `resolve_citation(...)` | Resolve exact structured citations without legal interpretation. |
| `search_laws(query: string, codes?: string[])` | Search normalized texts with optional law filters. |
| `get_source_metadata(code?: string)` | Return provenance metadata for one law or all laws. |

MCP tools return JSON-compatible objects directly. They do not return double-serialized JSON strings.

## HTTP API

The HTTP API is a small FastAPI transport over the same services:

- `GET /health`
- `GET /ready`
- `GET /laws`
- `GET /laws/{code}`
- `GET /laws/{code}/norms/{norm}`
- `GET /search`
- `GET /openapi.json`

Article-plus-section norm paths must be URL encoded, for example:

```text
/laws/egbgb/norms/art%3A246a%2Fpar%3A1
```

## Installation

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r mcp/requirements.txt
```

## Run MCP

Use a validated normalized dataset package:

```bash
DATASET_PATH=/path/to/normalized-dataset \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
python mcp/server.py
```

For local development, the committed fixture dataset can be used:

```bash
DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
python mcp/server.py
```

The default MCP transport is streamable HTTP on `http://localhost:8001/mcp`.

## Run HTTP API

```bash
DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
uvicorn http_api:create_http_app --factory --host 127.0.0.1 --port 8080
```

## Docker

The Docker image no longer clones `bundestag/gesetze`. Mount or provide a normalized dataset at `/data/legal-texts`:

```bash
docker build -t legal-text-mcp-de .
docker run --rm -p 8001:8001 -v /path/to/normalized-dataset:/data/legal-texts legal-text-mcp-de
```

## Tests

Run the full release gate:

```bash
PYTHONPATH=mcp python scripts/verify_release.py
```

The release gate covers source matrix probes, fixture coverage, import validation, parser normalization, citation resolution, search, MCP tools, HTTP/OpenAPI, structured errors, scope exclusions, and real local HTTP/MCP network E2E.

Run only the local network E2E check:

```bash
PYTHONPATH=mcp python scripts/verify_e2e.py
```

The E2E check starts real local HTTP and MCP streamable-HTTP server processes against the fixture dataset, then verifies HTTP routes over network requests and MCP tools through the official MCP client.

## License

This project is proprietary commercial software. See [LICENSE](LICENSE).

## Documentation

- [Project overview](docs/overview.md)
- [MCP/server module](docs/modules/mcp-server.md)
- [Supported laws](docs/features/supported-laws.md)
- [Source provenance](docs/features/source-provenance.md)
- [API contracts](docs/features/api-contracts.md)
- [HTTP API](docs/features/http-api.md)
- [Known issues](docs/features/known-issues.md)
