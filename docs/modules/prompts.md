---
type: documentation
entity: module
module: "prompts"
version: 1.0
---

# Module: prompts

> Part of [legal-text-mcp-de](../overview.md)

## Overview

The `src/legal_text_mcp_de/prompts/` package registers MCP Prompt templates
(slash-commands) on the FastMCP app. Each template pre-fills a structured
user message that guides the MCP client's LLM through a specific legal workflow,
reducing prompt engineering effort on the client side.

### Responsibility

This module is responsible for:

- registering the 5 standard legal slash-commands;
- parameterising each prompt so that client-provided arguments are embedded safely;
- returning `list[base.Message]` as required by the FastMCP Prompt contract.

It is not responsible for executing the workflows described in the prompts (that
is the client LLM's job) or for running sampling calls (see
[sampling](sampling.md)).

### Dependencies

| Dependency | Type | Purpose |
| ---------- | ---- | ------- |
| `mcp.server.fastmcp.FastMCP` | library | `@app.prompt()` registration. |
| `mcp.server.fastmcp.prompts.base` | library | `UserMessage`, `Message` types. |

## Structure

| Path | Type | Purpose |
| ---- | ---- | ------- |
| `src/legal_text_mcp_de/prompts/templates/rechtsfrage.py` | file | `/rechtsfrage` — answer a German legal question with exact norm citations. |
| `src/legal_text_mcp_de/prompts/templates/zitation_checken.py` | file | `/zitation-checken` — resolve a citation and show the Stand-Datum. |
| `src/legal_text_mcp_de/prompts/templates/norm_erklaeren.py` | file | `/norm-erklaeren` — plain-language explanation of a norm with cross-references. |
| `src/legal_text_mcp_de/prompts/templates/recherche.py` | file | `/recherche` — multi-step legal research (manual fallback until `research_topic` tool). |
| `src/legal_text_mcp_de/prompts/templates/dsgvo_check.py` | file | `/dsgvo-check` — GDPR compliance walkthrough for a processing activity. |
| `src/legal_text_mcp_de/prompts/templates/__init__.py` | file | `register_prompts` — calls each template's `register(app)`. |
| `src/legal_text_mcp_de/prompts/__init__.py` | file | Re-exports `register_prompts`. |

## Key Symbols

| Symbol | Kind | Location | Purpose |
| ------ | ---- | -------- | ------- |
| `register_prompts` | function | `templates/__init__.py` | Registers all 5 prompts on the FastMCP app. |
| `rechtsfrage` | prompt | `rechtsfrage.py` | Parameters: `frage` (required), `rechtsgebiet` (optional). |
| `zitation_checken` | prompt | `zitation_checken.py` | Parameters: `citation` (required). |
| `norm_erklaeren` | prompt | `norm_erklaeren.py` | Parameters: `code` (required), `norm` (required). |
| `recherche` | prompt | `recherche.py` | Parameters: `topic` (required). |
| `dsgvo_check` | prompt | `dsgvo_check.py` | Parameters: `aktivitaet` (required). |

## Prompt Catalogue

| Slash-command | Parameters | Workflow described |
| ------------- | ---------- | ------------------ |
| `/rechtsfrage` | `frage`, `rechtsgebiet?` | `list_laws` → `legal://laws/{code}/norms/{norm_id}` → structured answer with citations. |
| `/zitation-checken` | `citation` | `resolve_citation` → canonical form + Stand-Datum + deviation hints. |
| `/norm-erklaeren` | `code`, `norm` | Resource fetch + relationship fetch → plain-language explanation in 5 sections. |
| `/recherche` | `topic` | `search_laws` → norm hydration → cluster analysis → research summary. |
| `/dsgvo-check` | `aktivitaet` | Systematic GDPR walkthrough: Art. 5, 6, 7, 9, 13, 14 with per-article verdicts. |

## Inventory Notes

- **Coverage**: prompts are registered and listed via the MCP `prompts/list`
  endpoint; end-to-end tests verify registration.
- **Notes**: The `/recherche` template includes an inline note that the
  `research_topic` smart tool (v2 Phase E) automates the same workflow. Once the
  tool is stable, clients should prefer it over the manual prompt workflow.
- **See also**: [mcp-prompts feature](../features/mcp-prompts.md) for usage
  examples and client integration notes.
