<!--
SPDX-License-Identifier: Apache-2.0
Copyright 2026 klein-business
-->

# `research_topic` — Smart Tool

`research_topic` is the v2.0 showcase smart tool. It orchestrates 2 LLM-sampling calls per invocation to produce a structured legal research report.

## Signature

```python
research_topic(
    topic: str,
    max_norms: int = 10,
    include_eu: bool = True,
) -> ResearchReport
```

## Execution flow

```
topic input
    │
    ▼
Step 1: corpus search (search_laws)
    │  → candidate norms list
    ▼
Step 2: norm text hydration (get_norm × N)
    │  → norm texts + metadata
    ▼
Step 3: LLM ranking (sampling call 1)
    │  → ranked candidates with relevance scores
    ▼
Step 4: related-norms graph (get_related_norms × top-K)
    │  → cross-reference context
    ▼
Step 5: LLM synthesis (sampling call 2)
    │  → structured ResearchReport
    ▼
ResearchReport returned to client
```

## ResearchReport schema

```python
class ResearchReport(BaseModel):
    topic: str
    summary: str                    # 2–4 sentence executive summary
    key_norms: list[RankedNorm]     # top-K norms with relevance scores
    cross_references: list[str]     # related norm IDs loaded in Step 4
    sources: list[str]              # source URLs from provenance
    degraded: bool                  # True if sampling was unavailable
    degradation_reason: str | None  # reason if degraded
```

## Graceful degradation

When the MCP client does not support sampling, the tool falls back to a degraded report:

- Steps 1–2 still run (corpus search + norm hydration).
- Steps 3 and 5 are skipped (no LLM calls).
- `degraded=True`, `degradation_reason="client_no_sampling"`.
- `key_norms` contains unranked candidates sorted by corpus search score.
- `summary` is a templated string noting the degradation.

This ensures the tool always returns a useful response, even in clients like Cursor that may not implement the sampling extension.

## Progress reporting

The tool calls `ctx.report_progress` at each step boundary:

| Step | Progress |
|---|---|
| 1 — search | 0.1 |
| 2 — hydrate | 0.3 |
| 3 — rank | 0.5 |
| 4 — graph | 0.7 |
| 5 — synthesise | 0.9 |
| Done | 1.0 |

Clients that display progress bars will show incremental updates.

## Sampling configuration

Sampling calls use `safe_sample` with:

- `timeout=30s`
- `max_retries=2`
- Schema validation via `RankingResult` / `ResearchReport` pydantic models

If a sampling call times out or returns an invalid schema, the step is retried up to `max_retries` times. After exhausting retries, the tool degrades gracefully.

## Testing

Use `MockSamplingClient` (from `src/legal_text_mcp_de/sampling/mock_client.py`) for deterministic tests. It accepts a list of canned responses and returns them in order.

```python
from legal_text_mcp_de.sampling.mock_client import MockSamplingClient

client = MockSamplingClient(responses=[ranking_response, synthesis_response])
report = await research_topic("Datenschutz", sampling_client=client)
assert not report.degraded
```

## See also

- [MCP Prompts → /recherche](../prompts/index.md#recherche)
- [Sampling infrastructure](../concepts/mcp-native.md)
- [MCP-native architecture](../concepts/mcp-native.md)
