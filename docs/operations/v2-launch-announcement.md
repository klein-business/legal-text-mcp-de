<!--
SPDX-License-Identifier: Apache-2.0
Copyright 2026 klein-business
-->

# legal-text-mcp-de v2.0 — MCP-native domain server

## TL;DR

v2.0 of `legal-text-mcp-de` transforms the v1 Tool-wrapper into a vollwertiger MCP-native research server for German legal texts. **All four MCP capability classes** are implemented, the corpus expanded from 5 to ~8500 laws, and a public-hosted endpoint at `mcp.klein.business/legal/de` is now available alongside the self-hosted install paths.

## What's new

1. **MCP Resources** — 10 `legal://` URIs that load directly into the LLM context. No more roundtrips for known law codes.
2. **MCP Prompts** — 5 slash-commands curated for common legal-research workflows.
3. **MCP Sampling** — A `safe_sample` helper and the showcase `research_topic` smart tool that orchestrates 2 LLM inferences per invocation.
4. **Corpus ~6500 federal + 5 Länder + 5 EU acts** distributed as a signed `.tar.zst` OCI artifact on GHCR (auto-downloads on first run).
5. **Optional public-hosted service** at `mcp.klein.business/legal/de` (TLS, rate-limited, anonymised logging, no request bodies retained).

## Migration

v1.0 → v2.0 is a strict drop-in upgrade. All 9 v1 tools keep identical signatures.

```bash
uv pip install -U legal-text-mcp-de
```

See `docs/operations/migration-v1-v2.md` for the two documented (minor) breaks and the rollback path.

## Why MCP-native matters

A REST API with 9 endpoints is not an MCP server — it's a transport choice. The four MCP capability classes (Tools, Resources, Prompts, Sampling) only make sense when implemented together: Resources let the LLM load context without tool roundtrips, Prompts give users discoverable workflows, Sampling enables server-orchestrated multi-step reasoning. v2.0 ships all four, with `research_topic` as the canonical proof that smart tools can do things REST simply can't.

## Try it

- Docs: https://klein-business.github.io/legal-text-mcp-de/
- Source: https://github.com/klein-business/legal-text-mcp-de
- Hosted: https://mcp.klein.business/legal/de
- PyPI: https://pypi.org/project/legal-text-mcp-de/2.0.0/
- GHCR: `docker pull ghcr.io/klein-business/legal-text-mcp-de:2.0.0`
