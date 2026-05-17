---
type: documentation
entity: module
module: "sampling"
version: 1.0
---

# Module: sampling

> Part of [legal-text-mcp-de](../overview.md)

## Overview

The `src/legal_text_mcp_de/sampling/` package provides a typed, retried,
schema-validated wrapper around MCP Sampling. Smart tools such as
`research_topic` call `safe_sample` instead of invoking
`ctx.sample` directly, gaining automatic retry, timeout handling, and optional
Pydantic schema validation of the LLM output.

### Responsibility

This module is responsible for:

- wrapping `ctx.sample` with timeout, retry, and schema validation;
- defining the `SampleResult` envelope and shared response schemas;
- providing a structured error hierarchy for sampling failures;
- providing `MockSamplingClient` for deterministic tests.

It is not responsible for the content of sampling prompts (see
`tools/research_prompts.py`) or for deciding when to fall back to degraded mode
(that decision lives in each smart tool).

### Dependencies

| Dependency | Type | Purpose |
| ---------- | ---- | ------- |
| `pydantic` | library | `SampleResult`, `RankingResult`, and schema validation. |
| `asyncio` | standard library | `asyncio.wait_for` for timeout enforcement. |

## Structure

| Path | Type | Purpose |
| ---- | ---- | ------- |
| `src/legal_text_mcp_de/sampling/client.py` | file | `safe_sample` — the main async helper. |
| `src/legal_text_mcp_de/sampling/schemas.py` | file | `SampleResult`, `RankingEntry`, `RankingResult`. |
| `src/legal_text_mcp_de/sampling/errors.py` | file | `SamplingError` hierarchy. |
| `src/legal_text_mcp_de/sampling/testing.py` | file | `MockSamplingClient` for tests. |
| `src/legal_text_mcp_de/sampling/__init__.py` | file | Re-exports `safe_sample`, `MockSamplingClient`, and error classes. |

## Key Symbols

| Symbol | Kind | Location | Purpose |
| ------ | ---- | -------- | ------- |
| `safe_sample` | async function | `client.py` | Retried, timed-out sampling call; validates against `schema` when provided. |
| `SampleResult` | class | `schemas.py` | Holds `content` (raw string or parsed Pydantic model), `raw`, `tokens_used`, `model_used`. |
| `RankingResult` | class | `schemas.py` | LLM output schema for the `research_topic` ranking step; contains `list[RankingEntry]`. |
| `RankingEntry` | class | `schemas.py` | One ranked norm: `norm_id`, `score` (0–10), `reason`. |
| `SamplingError` | exception | `errors.py` | Base for all sampling failures. |
| `SamplingNotSupported` | exception | `errors.py` | Client does not implement the sampling capability. |
| `SamplingTimeout` | exception | `errors.py` | Timeout elapsed on all attempts. |
| `SamplingRefused` | exception | `errors.py` | User explicitly refused sampling in the client; not retried. |
| `SchemaValidationError` | exception | `errors.py` | LLM output did not parse to the requested schema. |
| `MockSamplingClient` | class | `testing.py` | Queue-based mock; returns `responses` in order from `sample()`. |

## safe_sample Contract

```python
result = await safe_sample(
    ctx,
    system="Du bist ein juristischer Assistent.",
    user_message="...",
    schema=RankingResult,   # optional; omit for plain-text responses
    max_tokens=1500,
    temperature=0.3,
    timeout_s=30.0,
    retries=2,
)
# result.content is a RankingResult instance when schema is given, else str
```

- Raises `SamplingNotSupported` immediately when `ctx.client_supports_sampling()` is falsy.
- Raises `SamplingRefused` immediately without retrying.
- Retries up to `retries` times on `TimeoutError` and general `SamplingError`.
- Raises the last exception after all attempts are exhausted.

## MockSamplingClient Usage

```python
mock = MockSamplingClient(responses=['{"ranking": []}'])
result = await safe_sample(mock, system="s", user_message="u", schema=RankingResult)
```

The mock implements `client_supports_sampling()`, `sample()`, `report_progress()`,
and `log()` so it can substitute for a real FastMCP `Context` in any smart-tool test.

## Inventory Notes

- **Coverage**: full; `safe_sample` paths (happy, timeout, refuse, schema error,
  retry exhaustion) and `MockSamplingClient` are covered by unit tests.
- **See also**: [mcp-sampling feature](../features/mcp-sampling.md) for the
  user-facing capability description and client requirements;
  [research-topic-smart-tool](../features/research-topic-smart-tool.md) for the
  primary consumer of this module.
