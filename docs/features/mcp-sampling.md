---
type: documentation
entity: feature
feature: "mcp-sampling"
version: 1.0
---

# Feature: mcp-sampling

> Part of [legal-text-mcp-de](../overview.md)

## Summary

v2 adds MCP Sampling support to the server. Smart tools such as `research_topic`
can ask the connected MCP client to run an LLM completion — for norm ranking and
research synthesis — without managing their own API credentials. The `safe_sample`
helper wraps the raw `ctx.sample` call with retry, timeout, and schema validation.

## What MCP Sampling Is

MCP Sampling is a protocol capability that allows a server-side tool to request
an LLM completion from the client. The human operator retains control: the
client's configured LLM processes the request, and the client may surface a
confirmation dialog before completing. This differs from the tool calling the
Anthropic API directly (no server-side API key required).

## How It Works

### User Flow

1. Use a client that supports the MCP Sampling capability (Claude Desktop,
   Claude Code, compatible third-party clients).
2. Connect to the server and call `research_topic` with a legal research topic.
3. The tool internally calls `safe_sample` twice: first to rank candidate norms,
   then to synthesise a research report.
4. The client presents or auto-approves the sampling requests.
5. `research_topic` returns a `ResearchReport` dict with ranked norms, related
   norms, synthesis text, and provenance.

### Degraded Mode

When the client does not support sampling (`client_supports_sampling()` returns
false), `research_topic` returns a degraded report with up to 5 raw search
results and `status="degraded_no_sampling"`. No error is raised; the tool
remains usable.

### Technical Flow

1. `research_topic` checks `ctx.client_supports_sampling()`.
2. If supported, it calls `safe_sample(ctx, …, schema=RankingResult)` for the
   ranking step and `safe_sample(ctx, …)` (no schema) for synthesis.
3. `safe_sample` wraps `ctx.sample` with `asyncio.wait_for(timeout=30s)` and
   retries up to 2 times on timeout or general error.
4. When a schema is supplied, the raw text is parsed with
   `schema.model_validate_json`; a `SchemaValidationError` is raised and retried
   on failure.
5. `SamplingRefused` is re-raised immediately without retrying.

## Implementation

| Module | Symbols | Role |
| ------ | ------- | ---- |
| [sampling](../modules/sampling.md) | `safe_sample` | Retried, schema-validated sampling helper. |
| [sampling](../modules/sampling.md) | `SampleResult`, `RankingResult` | I/O schemas. |
| [sampling](../modules/sampling.md) | `SamplingError` hierarchy | Structured failure types. |
| [sampling](../modules/sampling.md) | `MockSamplingClient` | Test double for unit tests. |

## Error Types

| Exception | Meaning | Retried? |
| --------- | ------- | -------- |
| `SamplingNotSupported` | Client lacks sampling capability. | No (raised before first call). |
| `SamplingTimeout` | Call timed out after `timeout_s`. | Yes (up to `retries` times). |
| `SamplingRefused` | User refused the sampling request. | No. |
| `SchemaValidationError` | LLM output did not match the schema. | Yes. |
| `SamplingError` | General sampling failure. | Yes. |

## Testing Without a Real Client

```python
from legal_text_mcp_de.sampling.testing import MockSamplingClient
from legal_text_mcp_de.sampling.client import safe_sample
from legal_text_mcp_de.sampling.schemas import RankingResult

mock = MockSamplingClient(responses=['{"ranking":[{"norm_id":"bgb/§305","score":9.0,"reason":"..."}]}'])
result = await safe_sample(mock, system="s", user_message="u", schema=RankingResult)
assert result.content.ranking[0].norm_id == "bgb/§305"
```

## Client Requirements

- The MCP client must declare the `sampling` capability during initialisation.
- `ctx.client_supports_sampling()` must return `True`.
- The operator controlling the client must allow sampling requests from this server.

## Related

- [sampling module](../modules/sampling.md)
- [research-topic-smart-tool](research-topic-smart-tool.md)
