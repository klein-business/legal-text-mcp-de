# Quickstart with uvx

`uvx` runs published Python tools in isolated environments without
permanent installation. This is the recommended way to start.

## Prerequisites

- Python 3.12 or 3.13.
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/).

## Run

```bash
uvx legal-text-mcp-de
```

This starts the MCP server on `http://localhost:8001/mcp` against
the committed fixture dataset.

## With a generated dataset

```bash
DATASET_PATH=/path/to/legal-text-package \
STRICT_STARTUP=true \
  uvx legal-text-mcp-de
```

`STRICT_STARTUP=true` causes the server to fail-fast on dataset
validation errors. Recommended for production.

## Verification

```bash
curl http://localhost:8001/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Expected: JSON response listing ten tools (9 v1 law tools +
`research_topic`).

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `DATASET_PATH` | bundled fixture | Path to a generated corpus package or fixture directory. |
| `STRICT_STARTUP` | `false` | Fail fast on dataset errors when `true`. |
| `HOST` | `127.0.0.1` | Bind address for the MCP server. |
| `PORT` | `8001` | Port for the MCP server. |

## Related

- [Claude Desktop](claude-desktop.md) — wiring the server into Claude Desktop.
- [Cursor](cursor.md) — wiring the server into Cursor.
- [Docker](docker.md) — containerized deployment.
