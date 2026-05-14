---
type: review
entity: plan-review
plan: "reliable-law-data-mcp"
status: final
reviewer: "general"
created: "2026-05-14"
---

# Plan Review: reliable-law-data-mcp

> Reviewing [reliable-law-data-mcp](../plan.md)

## Overall Assessment

**Verdict**: Ready

Cold review found no remaining Critical, Major, Minor, or Note findings. The DSGVO source correction is consistently reflected in the current source matrix, contracts, Phase 2 implementation plan, Phase 3 registry implementation plan, and todo changelog: the accepted source is the German Publications Office / Cellar expression `0004.02` at `https://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0004.02/DOC_1`, with language `DE` and validation requiring `<LG.DOC>DE</LG.DOC>`. The old `0017.02` Dutch expression is only mentioned as historical context or as a value to reject; it is not used as the accepted source in the active plan artifacts.

## Requirement Coverage

| Requirement | Covered By | Gap? | Notes |
| ----------- | ---------- | ---- | ----- |
| German Phase 1 laws use `gesetze-im-internet.de`, with no production dependence on `bundestag/gesetze` | [plan.md](../plan.md), [source-matrix.md](../source-matrix.md), [phase-2.md](../phases/phase-2.md), [phase-7.md](../phases/phase-7.md) | No | Source replacement, import ownership, and runtime/Docker migration are assigned to concrete phases. |
| Reproducible import, raw/normalized separation, hashing, manifests, retrieval timestamp, stand date/status, and content hash | [contracts.md](../contracts.md), [phase-2.md](../phases/phase-2.md), [phase-4.md](../phases/phase-4.md), [implementation/phase-2-impl.md](../implementation/phase-2-impl.md) | No | Phase 2 owns raw snapshots/manifests; Phase 4 owns normalized records/readiness. |
| Complete Phase 1 law set, aliases, source paths, known invalid paths, and DSGVO/EUR-Lex separation | [source-matrix.md](../source-matrix.md), [fixture-inventory.md](../fixture-inventory.md), [contracts.md](../contracts.md), [phase-3.md](../phases/phase-3.md) | No | Matrix covers all required laws, valid source paths, invalid `tddsg`/`pangv`, and DSGVO as `eur-lex-cellar`. |
| DSGVO accepted source must be German Cellar expression `0004.02`, not Dutch `0017.02` | [source-matrix.md](../source-matrix.md), [contracts.md](../contracts.md), [implementation/phase-2-impl.md](../implementation/phase-2-impl.md), [implementation/phase-3-impl.md](../implementation/phase-3-impl.md) | No | `source-matrix.md` line 33 pins expression `0004.02`, language `DE`, and the exact URL; line 38 requires `<LG.DOC>DE</LG.DOC>`. Contracts and implementation plans mirror `0004.02`/`DE`. |
| Shared canonical IDs, citation grammar, structured errors, readiness, MCP, HTTP, and search contracts | [contracts.md](../contracts.md), [phase-5.md](../phases/phase-5.md), [phase-6.md](../phases/phase-6.md), [phase-7.md](../phases/phase-7.md), [phase-8.md](../phases/phase-8.md) | No | Contracts include canonical ID grammar, article-plus-section grammar, error mappings, readiness states, MCP migration, and normalized search score rules. |
| Fixture coverage and golden tests for German laws, EGBGB child citations, BDSG, and DSGVO articles | [fixture-inventory.md](../fixture-inventory.md), [plan.md](../plan.md), [phase-5.md](../phases/phase-5.md), [phase-9.md](../phases/phase-9.md) | No | Required fixture list is explicit, including DSGVO Art. 5, 6, 12, 13, 14, 15, 17, 21, 25, 32, and 82. |
| MCP tools return real JSON objects and old demo tool names are removed from the stable surface | [contracts.md](../contracts.md), [phase-7.md](../phases/phase-7.md), [plan.md](../plan.md) | No | Phase 7 owns tool migration, dataset runtime migration, and double-serialization regression tests. |
| HTTP API and OpenAPI are exposed with shared structured errors | [phase-8.md](../phases/phase-8.md), [contracts.md](../contracts.md), [plan.md](../plan.md) | No | Phase 8 owns the listed endpoints, readiness behavior, OpenAPI, and HTTP contract tests. |
| Non-goals exclude SaaS, billing, tenants, auth/user management, and legal advice | [plan.md](../plan.md), [phase-9.md](../phases/phase-9.md) | No | Scope and release gate explicitly preserve these boundaries. |

## Scope Clarity

The current scope is specific enough for execution. Phase 1 is contract-only; Phases 2-8 each own a separable implementation slice; Phase 9 is a release gate rather than a place for new architecture. No additional scope finding.

## Phase Structure Assessment

| Phase | Title | Verdict | Issue |
| ----- | ----- | ------- | ----- |
| 1 | Domain Contracts and Dataset Layout | Ready | None. Contract artifacts and validation expectations are concrete. |
| 2 | Reproducible Source Import | Ready | None. Includes German source probing, DSGVO Cellar validation, live probe command, invalid-path regressions, manifests, and docs. |
| 3 | Canonical Registry and Alias Resolution | Ready | None. Registry implementation plan now pins all required aliases and DSGVO source identity. |
| 4 | Structured Normalization and Validation | Ready | None. Owns normalized records, EGBGB container/child records, validation, and readiness production. |
| 5 | Citation Resolver | Ready | None. Resolver grammar includes `child_unit`/`child_value` and structured errors. |
| 6 | Search Index and Result Contract | Ready | None. Deterministic ranking, snippets, selected-law search, and score normalization are specified. |
| 7 | MCP Tool API Migration | Ready | None. Runtime/Docker migration away from `bundestag/gesetze` is explicitly owned here. |
| 8 | HTTP API and OpenAPI | Ready | None. Endpoint set, readiness mapping, OpenAPI, and EGBGB child norm path are covered. |
| 9 | Fixture Coverage, Docs, and Release Gate | Ready | None. Final phase verifies rather than discovers fixtures/source paths. |

## Testing Strategy Assessment

### Test Coverage Gaps

No remaining test coverage gaps found for the stated requirements.

### Real-World Testing

Real-world/source validation is planned and concrete. Phase 1's verification script probes the source matrix; Phase 2 requires an opt-in live source probe command before completion; Phase 9 re-verifies source matrix probes and full transport behavior. I also performed a live spot check of the corrected DSGVO Cellar URL during this review: it returned HTTP 200, content type `application/xml;type=fmx4;charset=UTF-8`, contained `<LG.DOC>DE</LG.DOC>`, and did not contain `<LG.DOC>NL</LG.DOC>`.

## DSGVO Source Correction Check

- Accepted matrix row: `dsgvo_eu_2016_679` uses source kind `eur-lex-cellar`, CELEX `32016R0679`, Cellar work `3e485e15-11bd-11e6-ba9a-01aa75ed71a1`, expression `0004.02`, language `DE`, and URL `https://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0004.02/DOC_1`.
- Validation requirement: source validation requires HTTP 200, XML content type, `<LG.DOC>DE</LG.DOC>`, and recording CELEX, Cellar work ID, expression, language, retrieved URL, and content hash.
- Rejection of old source: `source-matrix.md` explicitly states the similarly retrievable `0017.02` expression is Dutch (`NL`) and must not be used for German fixtures.
- Active implementation plans: Phase 2 and Phase 3 implementation plans both use expression `0004.02` and language `DE` for DSGVO metadata.
- Search result: active plan, contracts, todo, and implementation plan artifacts contain no accepted-source use of `0017.02`; remaining `0017.02` occurrences are historical review artifacts or explicit rejection text.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| - | - | - | No real findings. | No plan changes recommended. |

## Recommendations

Proceed with implementation planning/execution from the current artifacts. Keep the Phase 2 live source probe as a required completion gate so upstream source drift is caught before trusted snapshots are accepted.
