<!--
SPDX-License-Identifier: Apache-2.0
Copyright 2026 klein-business
-->

# MCP Prompts

v2.0 ships 5 curated slash-command workflows. These appear automatically in MCP clients that support prompt discovery (e.g. Claude Desktop, Cursor).

## Prompt catalogue

| Slash-command | Required args | Optional args | Purpose |
|---|---|---|---|
| `/rechtsfrage` | `frage` | `rechtsgebiet` | Answer a German legal question with exact norm citations |
| `/zitation-checken` | `citation` | — | Resolve a citation (e.g. `§ 433 Abs. 1 BGB`) + Stand-Datum |
| `/norm-erklaeren` | `code`, `norm` | — | Plain-language explanation with cited cross-references |
| `/recherche` | `topic` | — | Multi-step research using `research_topic` smart tool |
| `/dsgvo-check` | `aktivitaet` | — | Walk through GDPR Art. 5, 6, 7, 9, 13, 14 against a processing activity |

## Prompt details

### `/rechtsfrage`

Answers a legal question grounded in the corpus. The prompt orchestrates:

1. A `search_laws` call to find candidate norms.
2. Norm text loading via `get_norm`.
3. A structured answer with exact `§ X Abs. Y SGB/BGB/...` citations.

**Example:** `/rechtsfrage frage="Wann haftet ein GmbH-Geschäftsführer persönlich?" rechtsgebiet="Gesellschaftsrecht"`

### `/zitation-checken`

Resolves a structured citation to a specific norm, verifies it exists in the corpus, and returns the current Stand-Datum from the source metadata.

**Example:** `/zitation-checken citation="§ 433 Abs. 1 S. 1 BGB"`

### `/norm-erklaeren`

Loads a norm's full text and its relationship graph, then produces a plain-language explanation with all cross-referenced norms cited.

**Example:** `/norm-erklaeren code="bgb" norm="par:433"`

### `/recherche`

Triggers the `research_topic` smart tool for multi-step corpus research with LLM ranking and synthesis. See [research_topic deep dive](../tools/research_topic.md).

**Example:** `/recherche topic="Datenschutz bei der Videoüberwachung im Einzelhandel"`

### `/dsgvo-check`

Walks through GDPR Articles 5, 6, 7, 9, 13, and 14 against a described processing activity. Each article is checked systematically with norm text loaded from the corpus.

**Example:** `/dsgvo-check aktivitaet="Speicherung von Kundendaten für 3 Jahre nach Vertragsende"`

## Implementation note

All prompts are declared in `src/legal_text_mcp_de/prompts/` and registered via `register_prompts(app)` in `server.py`. They are stateless — each invocation is independent.

## See also

- [MCP Resources](../resources/index.md) — load law text into context before prompting
- [research_topic smart tool](../tools/research_topic.md)
- [MCP-native architecture](../concepts/mcp-native.md)
