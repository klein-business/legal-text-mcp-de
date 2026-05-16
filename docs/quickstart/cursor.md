# Quickstart with Cursor

Wire `legal-text-mcp-de` into Cursor as a custom MCP server.

## Prerequisites

- Cursor installed.
- `uv` available on PATH ([installation](https://docs.astral.sh/uv/getting-started/installation/)).

## Configuration

Edit Cursor's MCP configuration file (`~/.cursor/mcp.json`) and add:

```json
{
  "mcpServers": {
    "legal-text-mcp-de": {
      "command": "uvx",
      "args": ["legal-text-mcp-de"],
      "env": {
        "DATASET_PATH": "/path/to/legal-text-package",
        "STRICT_STARTUP": "true"
      }
    }
  }
}
```

Replace the `DATASET_PATH` with your generated package directory, or
omit the `env` block to use the bundled fixture corpus for quick
exploration.

!!! tip "Fixture corpus"
    Omit the `env` block entirely to use the bundled fixture corpus.
    This starts the server against ~10 German federal laws and is useful
    for trying out the tools before you have a full generated corpus.

Restart Cursor. The nine tools appear in the tool list under the MCP
section.

## Verification

Open a Cursor chat and ask:

> List the available German law codes.

Cursor should invoke `list_laws` and return a list including
abbreviations like `BGB`, `StGB`, `DSGVO`.

## Configuration file location

| Platform | Path |
| --- | --- |
| macOS | `~/.cursor/mcp.json` |
| Windows | `%USERPROFILE%\.cursor\mcp.json` |
| Linux | `~/.cursor/mcp.json` |

## Related

- [Claude Desktop](claude-desktop.md) — same approach with Claude Desktop's config path.
- [uvx](uvx.md) — running the server standalone.
- [MCP tools reference](../tools/list_laws.md) — what each tool does.
