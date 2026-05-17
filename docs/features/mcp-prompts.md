---
type: documentation
entity: feature
feature: "mcp-prompts"
version: 1.0
---

# Feature: mcp-prompts

> Part of [legal-text-mcp-de](../overview.md)

## Summary

v2 registers 5 MCP Prompt templates (slash-commands) that pre-fill structured
user messages for common German legal workflows. Clients call `prompts/get` to
retrieve the filled message and inject it into their LLM conversation.

## How It Works

### User Flow

1. Connect an MCP client to the server.
2. Call `prompts/list` to see the 5 available prompts.
3. Call `prompts/get` with the prompt name and required arguments.
4. The server returns a `list[Message]` with a pre-filled `UserMessage`.
5. The client's LLM follows the workflow instructions, using the MCP tools and
   resources described in the message to complete the task.

### Prompt Catalogue

| Slash-command | Arguments | Use case |
| ------------- | --------- | -------- |
| `rechtsfrage` | `frage` (required), `rechtsgebiet` (optional) | Answer a German legal question with exact norm citations and Stand-Datum. |
| `zitation_checken` | `citation` (required) | Resolve a citation, show canonical form, Stand-Datum, and flag deviations. |
| `norm_erklaeren` | `code` (required), `norm` (required) | Plain-language explanation with cross-references in 5 structured sections. |
| `recherche` | `topic` (required) | Multi-step legal research: search → cluster → summary. |
| `dsgvo_check` | `aktivitaet` (required) | Systematic GDPR compliance walkthrough covering Art. 5, 6, 7, 9, 13, 14. |

### Technical Flow

1. `server.py` calls `register_prompts(app)` during construction.
2. Each prompt template calls `@app.prompt()` and returns a `list[UserMessage]`.
3. The user message body is built with `textwrap.dedent` and argument
   interpolation — no templating engine is involved.
4. Tool and resource references inside the message body use the stable names
   from [mcp-law-tools](mcp-law-tools.md) and [mcp-resources](mcp-resources.md).

## Implementation

| Module | Symbols | Role |
| ------ | ------- | ---- |
| [prompts](../modules/prompts.md) | `register_prompts` | Registration entry point. |
| [prompts](../modules/prompts.md) | `rechtsfrage`, `zitation_checken`, `norm_erklaeren`, `recherche`, `dsgvo_check` | Individual prompt functions. |

## Usage Example

```python
# MCP client (pseudocode)
result = await client.get_prompt("rechtsfrage", arguments={"frage": "Wann liegt AGB-Einbeziehung vor?"})
# result.messages[0] is a UserMessage with the pre-filled workflow instructions
```

## Notes

- The `/recherche` prompt describes a manual workflow. The `research_topic` tool
  (see [research-topic-smart-tool](research-topic-smart-tool.md)) automates the
  same steps when the client supports MCP Sampling.
- The `/dsgvo-check` prompt references `legal://laws/DSGVO/norms/Art. 5` etc.
  These URIs resolve through the [mcp-resources](mcp-resources.md) surface.

## Edge Cases

- Missing required arguments cause an MCP protocol error before the prompt body
  is constructed.
- Optional arguments (`rechtsgebiet`) are omitted from the message body when not
  supplied.

## Related

- [prompts module](../modules/prompts.md)
- [mcp-resources](mcp-resources.md)
- [mcp-law-tools](mcp-law-tools.md)
- [research-topic-smart-tool](research-topic-smart-tool.md)
