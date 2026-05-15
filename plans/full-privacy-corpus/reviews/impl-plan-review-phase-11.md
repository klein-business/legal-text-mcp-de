---
type: review
entity: implementation-plan-review
plan: "full-privacy-corpus"
phase: 11
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 11 - Runtime coverage and relationship APIs

> Reviewing [Phase 11 Implementation Plan](../implementation/phase-11-impl.md)
> Against [Phase 11 Scope](../phases/phase-11.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Ready

The implementation plan is aligned with the gated Phase 11 scope and is concrete enough for execution without additional planning. It keeps the work additive, routes MCP and HTTP behavior through the existing `LegalTextRuntime` service layer, explicitly covers generated-package coverage/source-limitation/relationship data, and includes real-world HTTP/MCP E2E verification against generated fixture coverage.

## Scope Alignment

The plan implements the required runtime access to corpus coverage, source limitations, relationship metadata, MCP/HTTP surfaces, resolver/API tests for new citation units, compatibility checks, and generated-fixture E2E coverage. It does not introduce excluded work such as search ranking changes, production-corpus performance tuning, or additional source-family imports.

## Technical Feasibility

The approach matches the current code structure. `NormalizedDataset` is the correct loading/indexing point for optional generated-package metadata, `LegalTextRuntime` is the shared service layer used by MCP and HTTP, `create_mcp_app` is the current MCP tool registration point, `create_http_app` owns route registration, and `resolver.py` is the right place to extend exact citation parsing while preserving existing child article/paragraph behavior.

The plan also correctly accounts for current reality: HTTP does not yet route source metadata, dataset loading has no optional relationship/limitation indexes, and resolver parsing currently accepts only `par`/`art` canonical units plus existing shorthands.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Load coverage, limitations, and relationships in the dataset | Yes | Yes | None |
| 2 | Add runtime service methods | Yes | Yes | None |
| 3 | Add MCP tools additively | Yes | Yes | None |
| 4 | Add HTTP endpoints and OpenAPI models | Yes | Yes | None |
| 5 | Add resolver/API coverage for new units | Yes | Yes | None |

## Required Context Assessment

The required context is sufficient for execution. It includes the Phase 11 scope, the generated-package and relationship schema plans from prior phases, final state-law outcome context, and the current dataset/runtime/resolver/MCP/HTTP/test anchors that will be modified.

No unnecessary context was identified.

## Testing Plan Assessment

### Test Integrity Check

The testing plan has exactly one primary verify command and exercises the changed runtime, HTTP, MCP, resolver, and E2E behavior. It explicitly protects the stable MCP tool list, existing OpenAPI path assertions, existing HTTP endpoints, old tool names/arguments/response fields, and relationship metadata boundaries.

### Test Gaps

No test gaps were identified.

### Real-World Testing

Real-world integration testing is planned through `scripts/verify_e2e.py`, which must exercise generated fixture coverage through both local HTTP and MCP transports after the new endpoints/tools are added.

## Reality Check Validation

The Reality Check is accurate against the current repository. The cited current anchors exist and match their described roles: `LegalTextRuntime` mediates runtime behavior, `create_mcp_app` currently registers six tools, `create_http_app` lacks coverage/source-limitation/relationship routes, `SourceMetadataResponse` exists without an HTTP route, and `CANONICAL_NORM_RE`/`parse_norm_reference` currently handle only the existing exact citation forms.

## Findings Summary

| Severity | Count |
| -------- | ----- |
| Critical | 0 |
| Major | 0 |
| Minor | 0 |
| Note | 0 |

No Critical, Major, Minor, or Note findings were identified.

## Recommendations

Proceed to Phase 11 execution.
