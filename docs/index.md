# legal-text-mcp-de

A Python [Model Context Protocol](https://modelcontextprotocol.io)
server and HTTP API for loading, validating, searching, and resolving
**German legal texts** with source provenance.

!!! warning "Not legal advice"
    This software returns text and structured metadata. It does not
    interpret the law, advise on it, or produce any legal conclusion.
    The maintainer assumes no liability for use in legal
    decision-making contexts.

## What it is

- An MCP-native domain server (streamable HTTP transport, default
  `:8001/mcp`) that implements all four MCP capability classes for
  German federal + state laws and EU acts:
    - **Tools** — 10 callable tools (9 v1 law tools + `research_topic`
      multi-step smart tool with Sampling).
    - **Resources** — 10 read-only `legal://` URIs (paginated law
      index, full law text, single norm, relationships, corpus
      coverage/limitations/manifest).
    - **Prompts** — 5 curated slash-workflows (`/rechtsfrage`,
      `/zitation-checken`, `/norm-erklaeren`, `/recherche`,
      `/dsgvo-check`).
    - **Sampling** — `safe_sample` helper for server-orchestrated
      LLM calls with retry + schema validation, used by
      `research_topic`.
- A FastAPI HTTP API over the same runtime, for non-MCP clients.
- Local or server-side infrastructure: no SaaS account required.
  Self-host via `uvx` / Docker, or use the optional public-hosted
  endpoint at `mcp.klein.business/legal/de`.

## What it is not

- A legal-advice engine. No interpretation, no AI legal reasoning.
- A tenant-specific SaaS or legal-advice service. The optional public
  endpoint is stateless; you can also run it locally or on your own
  infrastructure.
- A bundler of editorial law text. Texts come from official sources
  (gesetze-im-internet.de, EUR-Lex / Cellar) at runtime.

## Quickstart

```bash
uvx legal-text-mcp-de
```

See [Quickstart → uvx](quickstart/uvx.md) for the full setup,
[Claude Desktop](quickstart/claude-desktop.md), or
[Docker](quickstart/docker.md).

## Architecture at a glance

```mermaid
flowchart LR
  Client[MCP client] -->|streamable HTTP :8001/mcp| Server
  Client2[HTTP client] -->|FastAPI :8001| Server
  Server[legal-text-mcp-de] -->|loads| Dataset
  Dataset[(DATASET_PATH)] -->|fixture or generated| Sources
  Sources[gesetze-im-internet.de<br/>EUR-Lex / Cellar]
```

The server runs against either committed fixture packages (deterministic
CI tests) or a generated production corpus (`DATASET_PATH=...`).

## Where to next

- [Concepts → Data modes](concepts/data-modes.md)
- [Concepts → Provenance](concepts/provenance.md)
- [MCP tools reference](tools/list_laws.md)
- [HTTP API overview](api/index.md)
