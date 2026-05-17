<!--
SPDX-License-Identifier: Apache-2.0
Copyright 2026 klein-business
-->

# MCP-native architecture

v2.0 implements all four MCP capability classes:

| Capability | What it is | Where in this server |
|---|---|---|
| Tools | LLM-callable functions | 10 tools incl. `research_topic` |
| Resources | URIs the LLM loads as context | 10 `legal://` URIs |
| Prompts | Slash-command workflows | 5 prompts |
| Sampling | Server-orchestrated LLM inference | `safe_sample` + `research_topic` |

See the spec at `docs/superpowers/specs/2026-05-17-v2-mcp-native-design.md` for the design rationale and the per-tier deep dives below for usage.

## Why all four tiers matter

A REST API with 9 endpoints is not an MCP server — it's a transport choice. The four MCP capability classes only make sense when implemented together:

- **Resources** let the LLM load context (e.g. a law's full text) without a tool roundtrip. The client decides when to prefetch; the server just declares the URI catalogue.
- **Prompts** give users discoverable, curated entry points. Instead of learning which tool to call with which arguments, users pick `/rechtsfrage` and fill a form.
- **Sampling** enables server-orchestrated multi-step reasoning. `research_topic` runs two LLM calls per invocation — ranking and synthesis — entirely server-side.

Together these reduce LLM latency, improve discoverability, and allow complex workflows that a REST-only surface cannot express.

## Resource URI catalogue

| URI | Content type | Description |
|---|---|---|
| `legal://laws` | JSON | Paginated law index |
| `legal://laws/page/{cursor}/{limit}` | JSON | Explicit page |
| `legal://laws/{code}` | Markdown | Law header + norm index |
| `legal://laws/{code}/full` | Markdown | Full law text |
| `legal://laws/{code}/norms/{norm_id}` | Markdown | Single norm |
| `legal://laws/{code}/norms/{norm_id}/relationships` | JSON | Related-norm graph |
| `legal://laws/{code}/source` | JSON | Provenance |
| `legal://corpus/coverage` | JSON | Coverage summary |
| `legal://corpus/limitations` | JSON | Source limitations |
| `legal://corpus/manifest` | JSON | Bundle manifest |

## Further reading

- [MCP Resources](../resources/index.md) — usage examples
- [MCP Prompts](../prompts/index.md) — slash-command reference
- [research_topic smart tool](../tools/research_topic.md) — deep dive
- [Migration v1 → v2](../operations/migration-v1-v2.md)
