# stdio transport status

- **Unsupported by the current CLI:** `legal-text-mcp-de serve` explicitly selects Streamable HTTP.
- `MCP_TRANSPORT=stdio` and piped stdin do not change that selection.
- The MCP SDK supports stdio, but the CLI does not expose it. Earlier automatic-stdio instructions were incorrect.
- Desktop client compatibility remains **[UNVERIFIED]**; follow [issue #93](https://github.com/klein-business/legal-text-mcp-de/issues/93).

## Supported server transport

```bash
DATASET_PATH=/absolute/path/to/compatible-dataset \
  uvx legal-text-mcp-de==2.1.3 serve --host 127.0.0.1
```

- Endpoint: `http://localhost:8001/mcp`.
- Use a client with a Streamable HTTP connection; a stdio subprocess configuration cannot use this command.
- Supply a normalized dataset directory. The package does not bundle fixtures or automatically prepare a usable corpus.
- For current-source federal data, use the [federal corpus guide](federal-corpus.md).

## Related

- [Claude Desktop status](claude-desktop.md)
- [Cursor status](cursor.md)
- [MCP and HTTP surface](../concepts/mcp-and-http-surface.md)
