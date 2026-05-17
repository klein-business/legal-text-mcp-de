# Quickstart with Claude Desktop

Wire `legal-text-mcp-de` into Claude Desktop as a custom MCP server.

## Prerequisites

- Claude Desktop installed.
- `uv` available on PATH ([installation](https://docs.astral.sh/uv/getting-started/installation/)).

## Configuration

Edit Claude Desktop's MCP servers configuration (Settings → Developer
→ Edit Config) and add:

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

Restart Claude Desktop. The ten tools (9 v1 law tools + `research_topic`)
appear in the tool list, alongside the 10 `legal://` resources and 5
slash-prompts.

## Verification

In a new Claude conversation:

> List the available German law codes.

Claude should invoke `list_laws` and return a list including
abbreviations like `BGB`, `StGB`, `DSGVO`.

## Configuration file location

| Platform | Path |
| --- | --- |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

## Related

- [Cursor](cursor.md) — same approach with Cursor's config path.
- [uvx](uvx.md) — running the server standalone.
- [MCP tools reference](../tools/list_laws.md) — what each tool does.
