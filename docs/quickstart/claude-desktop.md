# Claude Desktop compatibility and setup status

- First-hand client compatibility: **[UNVERIFIED]**. Track evidence in [issue #93](https://github.com/klein-business/legal-text-mcp-de/issues/93).
- The current `serve` command uses Streamable HTTP. It does not implement stdio or honor `MCP_TRANSPORT=stdio`.
- A client configuration that launches `uvx legal-text-mcp-de serve` as a stdio subprocess will not work.
- The package contains no bundled fixture corpus. Provide a compatible normalized dataset directory.

## Start the HTTP MCP server

```bash
DATASET_PATH=/absolute/path/to/compatible-dataset \
  uvx legal-text-mcp-de==2.1.3 serve --host 127.0.0.1
```

- Endpoint: `http://localhost:8001/mcp`.
- Use a Streamable HTTP client connection; desktop-version-specific configuration remains [UNVERIFIED].
- For a current-source federal dataset, follow the [federal corpus guide](federal-corpus.md), including its runtime version requirement.

## Evidence needed before marking tested

1. Record the client version, operating system, server revision, and transport.
2. Confirm successful MCP initialization and `tools/list`.
3. Run `list_laws` and record the result.
4. Add that evidence to issue #93.

## Related

- [uvx](uvx.md)
- [Transport limitations](stdio.md)
- [MCP tools reference](../tools/list_laws.md)
