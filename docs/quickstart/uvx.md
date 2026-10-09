# Quickstart with uvx

`uvx` runs published Python tools in isolated environments without
permanent installation. This is the recommended way to start.

## Prerequisites

- Python 3.12 or 3.13.
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/).

## Run with a dataset

```bash
DATASET_PATH=/absolute/path/to/compatible-dataset \
HOST=127.0.0.1 \
  uvx legal-text-mcp-de==2.1.3 serve
```

- The package does not bundle fixtures. Keep `DATASET_PATH` configured.
- The MCP endpoint is `http://localhost:8001/mcp` using Streamable HTTP.
- For current-source federal data, use the [federal corpus guide](federal-corpus.md); its repealed-norm fix is newer than v2.1.3.
- Repository fixtures can be used for development from a source checkout; they are not a complete production corpus.

## Verification

Keep the server running. In a second terminal, use an MCP client that initializes the session:

```bash
uvx --from mcp==1.28.1 python - <<'PYCLIENT'
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client("http://127.0.0.1:8001/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print([tool.name for tool in (await session.list_tools()).tools])

asyncio.run(main())
PYCLIENT
```

Expected: tool names including `list_laws` and `research_topic`.

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `DATASET_PATH` | unset (required) | Path to a generated corpus package or fixture directory. |
| `STRICT_STARTUP` | `true` | Fail fast on dataset errors when `true`. |
| `HOST` | `0.0.0.0` | Bind address for the MCP server. |
| `PORT` | `8001` | Port for the MCP server. |

## Related

- [Claude Desktop](claude-desktop.md) — wiring the server into Claude Desktop.
- [Cursor](cursor.md) — wiring the server into Cursor.
- [Docker](docker.md) — containerized deployment.
