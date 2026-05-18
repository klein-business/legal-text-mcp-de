<!--
SPDX-License-Identifier: Apache-2.0
Copyright 2026 klein-business
-->

# Migration v1 → v2

`legal-text-mcp-de` v2.0 is a **strict drop-in upgrade** for v1.0 callers. All 9 v1 tools keep identical signatures and return shapes.

## What's new in v2.0

| Capability | v1.0 | v2.0 |
|---|---|---|
| MCP Tools | 9 (`list_laws`, `get_law`, etc.) | 9 v1 + 1 new (`research_topic`) |
| MCP Resources | none | **10 `legal://` URIs** (laws, norms, corpus inventory) |
| MCP Prompts | none | **5 slash-workflows** (`/rechtsfrage`, `/zitation-checken`, `/norm-erklaeren`, `/recherche`, `/dsgvo-check`) |
| MCP Sampling | unused | `safe_sample` helper + `research_topic` smart-tool driving 2 sampling calls per invocation |
| Corpus | 5 fixture laws | ~8500 laws (federal + 5 states + 5 EU acts) as signed `.tar.zst` bundle on GHCR |
| Distribution | PyPI + GHCR (single image) | PyPI + GHCR (slim + full) + optional public host at `mcp.klein.business` |

## Documented breaks

Two minor breaks; both can be opted out with env vars.

### 1. `DATASET_PATH` default behaviour

- **v1.0:** unset `DATASET_PATH` → server fails to start.
- **v2.0:** unset `DATASET_PATH` → server auto-downloads the latest signed bundle from GHCR.
- **Restore v1 behaviour:** set `STRICT_DATASET=true` to require an explicit path.

### 2. `get_corpus_coverage` schema bump

- Schema version field bumped from `"1"` → `"2"`.
- New fields added: `bund_law_count`, `land_law_count`, `eu_act_count`.
- All existing v1 fields preserved.
- Clients that schema-validate the response need to accept the new fields (which Pydantic does by default with `extra="ignore"`).

## Upgrade procedure

```bash
# 1. Update the package
uv pip install -U legal-text-mcp-de   # → 2.0.0

# 2. (optional) drop explicit DATASET_PATH — auto-download now handles it

# 3. Restart your MCP client; new Resources + Prompts appear automatically
```

## Rollback procedure

If something goes wrong, downgrade to the last v1.x:

```bash
uv pip install legal-text-mcp-de==1.5.0
```

v1.5.0 is the last v1 release; it contains the corpus pipeline expansion but NOT the MCP-native v2 surface, so it is safe to roll back to.

## What stays the same

- All 9 v1 tool names and signatures
- HTTP API surface (`/laws`, `/laws/{code}`, etc.)
- Docker entry point `legal-text-mcp-de`
- pydantic-settings env-var conventions
- Apache-2.0 license
- Source layout (`src/legal_text_mcp_de/`)

## What's deferred to v2.1+

- Additional smart tools (`cite_for_thesis`, `simulate_case`, `compliance_gap_analysis`)
- Hardware-2FA gating for the public service
- ML-based norm embeddings for better `search_laws`
- Versioning of norm texts (historical Stände)
- State law tiers Mittel + Klein (11 more Bundesländer)

See `docs/superpowers/specs/2026-05-17-v2-mcp-native-design.md` Section 13 for the full out-of-scope list.

## v2.0 → v2.1 — CLI introduction (BREAKING for invocation form)

v2.1.0 introduces a `typer`-based CLI as the new `legal-text-mcp-de`
entry point. Bare invocation now prints `--help`; the MCP server
requires the explicit `serve` subcommand.

**Migration:**

| Before (v2.0.x) | After (v2.1.0+) |
|---|---|
| `legal-text-mcp-de` | `legal-text-mcp-de serve` |
| `uvx legal-text-mcp-de` | `uvx legal-text-mcp-de serve` |
| `docker run … :2.0.1` | `docker run … :2.1.0 serve` |
| Claude Desktop `"args": ["legal-text-mcp-de"]` | `"args": ["legal-text-mcp-de", "serve"]` |

**Not breaking:**

- All 9 v1 MCP tool signatures + `research_topic`
- HTTP API surface
- Environment variables (`DATASET_PATH`, `STRICT_STARTUP`,
  `MAX_REQUEST_BODY_BYTES`, …)
- Corpus bundle format

**Why not v3.0.0:** the `docs/operations/versioning.md` stability
contract explicitly enumerates "MCP tool signature, HTTP route, or
dataset schema". CLI invocation form is outside that contract and
evolves with minor versions.
