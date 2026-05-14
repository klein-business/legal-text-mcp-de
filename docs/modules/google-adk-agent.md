---
type: documentation
entity: module
module: "google-adk-agent"
version: 1.2
---

# Module: google-adk-agent

> Part of [legal-text-mcp-de](../overview.md)

## Overview

The `google-adk-agent/` module is an optional legacy demonstration client for the MCP endpoint. It is not part of the reliable legal text data pipeline, but it can still connect to the server through `MCP_URL`.

### Responsibility

This module demonstrates one LLM client integration path. It is not responsible for law data import, normalization, citation resolution, search indexing, source provenance, or MCP tool contracts.

### Dependencies

| Dependency | Type | Purpose |
| ---------- | ---- | ------- |
| `google.adk.tools.mcp_tool.MCPToolset` | library | Exposes remote MCP tools to the ADK agent. |
| `StreamableHTTPConnectionParams` | library | Configures the MCP HTTP endpoint. |
| `google.adk.agents.llm_agent.LlmAgent` | library | Defines the Gemini-backed demo assistant. |
| `MCP_URL` | environment | Points the demo agent at a running MCP server. |

## Structure

| Path | Type | Purpose |
| ---- | ---- | ------- |
| `google-adk-agent/` | dir | Optional ADK demo assets. |
| `google-adk-agent/agent/agent.py` | file | Configures MCP connectivity and the demo LLM agent. |
| `google-adk-agent/image.png` | file | Screenshot asset referenced by archived legacy docs. |

## Current Compatibility Note

The stable MCP tool surface is `list_laws`, `get_law`, `get_norm`, `resolve_citation`, `search_laws`, and `get_source_metadata`. The ADK demo relies on dynamic MCP tool discovery, but its natural-language prompt was written for the earlier paragraph-oriented demo. Treat it as a client example, not as a tested acceptance path.

## Configuration

| Setting | Default | Purpose |
| ------- | ------- | ------- |
| `MCP_URL` | `http://localhost:8001/mcp` | MCP server endpoint. |
| `GEMINI_API_KEY` | none | Gemini credential for local ADK runs when using AI Studio credentials. |

## Inventory Notes

- **Coverage**: partial for the supported runtime.
- **Notes**: The legacy `google-adk-agent/README.md` was archived to `docs-legacy/google-adk-agent--README.md`.
