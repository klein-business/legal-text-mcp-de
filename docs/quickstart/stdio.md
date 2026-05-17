# Quickstart — stdio transport (offline / Claude Desktop)

The MCP SDK supports two transports: streamable-HTTP (default,
`http://localhost:8001/mcp`) and stdio. Stdio is the right choice for:

- **Claude Desktop's launcher** when you want it to spawn the server
  as a subprocess instead of pointing at a long-running HTTP endpoint.
- **Offline / air-gapped environments** where you don't want to bind
  a TCP port.
- **Sandboxed setups** that prefer pipe-based IPC over HTTP.

## Launch the server in stdio mode

`legal-text-mcp-de` auto-selects stdio when stdin is a pipe (the
default for MCP clients that spawn it as a subprocess) — no flag
needed. To force stdio explicitly, set `MCP_TRANSPORT=stdio`:

```bash
DATASET_PATH=tests/fixtures/normalized \
STRICT_STARTUP=true \
MCP_TRANSPORT=stdio \
uv run legal-text-mcp-de
```

The server reads JSON-RPC frames from stdin and writes replies to
stdout. Log output goes to stderr so it doesn't corrupt the protocol
channel.

## Claude Desktop config — stdio variant

`~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "legal-de-stdio": {
      "command": "uvx",
      "args": ["legal-text-mcp-de"],
      "env": {
        "DATASET_PATH": "/path/to/legal-text-package",
        "STRICT_STARTUP": "true",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

Restart Claude Desktop. The ten tools appear in the tool list and the
five `/`-prompts in the slash-command picker, identical to the HTTP
variant — only the transport differs.

## Environment variables that matter for stdio

| Variable | Default | Effect |
| --- | --- | --- |
| `MCP_TRANSPORT` | `streamable-http` if a TTY/port is available, else `stdio` | Force one transport explicitly |
| `DATASET_PATH` | unset (auto-download) | Path to corpus bundle |
| `STRICT_STARTUP` | `false` | Fail-fast on dataset load errors |

`HOST` and `PORT` are ignored in stdio mode.

## Trade-offs vs. streamable-HTTP

| | stdio | streamable-HTTP |
| --- | --- | --- |
| Multiple clients | one client per process | many clients, one server |
| Long-running | client owns the lifetime | server is independent |
| Network exposure | none | bind on host:port |
| Suitable for | desktop clients, offline | hosted, multi-tenant |
| Bandwidth overhead | lowest | TCP/HTTP framing |

For the public-hosted endpoint at `mcp.klein.business/legal/de` you
will always use streamable-HTTP — stdio is local-only.

## Related

- [Claude Desktop quickstart](claude-desktop.md) — streamable-HTTP variant
- [MCP and HTTP surface](../concepts/mcp-and-http-surface.md) — transport overview
