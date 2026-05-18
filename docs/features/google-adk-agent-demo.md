---
type: documentation
entity: feature
feature: "google-adk-agent-demo"
version: 1.2
---

# Feature: google-adk-agent-demo

> Part of [legal-text-mcp-de](../overview.md)

## Summary

The Google ADK demo shows that an external LLM client can connect to the MCP endpoint. It is retained as an optional legacy demonstration asset only; it is outside the core uv-managed runtime, and runtime reliability is verified through deterministic MCP tool tests rather than this LLM client.

## How It Works

1. Start the MCP server with `legal-text-mcp-de serve` and a validated normalized dataset (the `serve` subcommand is required as of v2.1.0; see [cli-shell-surface](cli-shell-surface.md)).
2. Set `MCP_URL` if the server is not at `http://localhost:8001/mcp`.
3. Set Gemini credentials such as `GEMINI_API_KEY`.
4. Run the ADK app from `google-adk-agent`.
5. The agent discovers MCP tools through the MCP toolset.

## Implementation

| Module | Symbols | Role |
| ------ | ------- | ---- |
| [google-adk-agent](../modules/google-adk-agent.md) | `MCP_URL` | Selects the MCP endpoint. |
| [google-adk-agent](../modules/google-adk-agent.md) | `toolset` | Connects the ADK agent to MCP tools. |
| [google-adk-agent](../modules/google-adk-agent.md) | `root_agent` | Defines the demo model, prompt, and tools. |
| [mcp-server](../modules/mcp-server.md) | `create_mcp_app` | Supplies the stable MCP tools. |

## Edge Cases & Limitations

- The module is not covered by the release gate.
- The module's ADK dependencies are not installed by the core uv project groups.
- The prompt predates the final structured citation resolver and may need tightening before production client use.
- Reference extraction is handled by the model, not by deterministic legal text logic.
- The module has no tests in this repository.

## Related Features

- [mcp-law-tools](mcp-law-tools.md)
- [api-contracts](api-contracts.md)
