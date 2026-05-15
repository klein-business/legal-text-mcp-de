---
type: planning
entity: implementation-plan
plan: "full-privacy-corpus"
phase: 11
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 11 - Runtime coverage and relationship APIs

> Implements [Phase 11](../phases/phase-11.md) of [full-privacy-corpus](../plan.md)

## Approach

Expose the validated generated-package coverage, source limitations, and relationship metadata through additive `LegalTextRuntime`, MCP, and HTTP surfaces. Preserve existing tools and endpoints, and keep relationship metadata separate from legal text. Extend resolver/runtime behavior for new citation units using the Phase 2 package contract and Phase 5/7/9/10 records.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | modify | Add runtime methods, MCP tools, HTTP endpoints/models, relationship lookup, coverage/source limitation access, and E2E fixture tests. |

## Required Context

| File | Why |
|------|-----|
| `plans/full-privacy-corpus/phases/phase-11.md` | Gated additive runtime API scope. |
| `plans/full-privacy-corpus/implementation/phase-2-impl.md` | Generated package and relationship schema. |
| `plans/full-privacy-corpus/implementation/phase-6-impl.md` | Relationship seed/fallback conversion rules. |
| `plans/full-privacy-corpus/implementation/phase-10-impl.md` | Final state-law imported-or-limited outcomes. |
| `mcp/legal_texts/dataset.py` | Current package loader and source metadata lookup. |
| `mcp/legal_texts/runtime.py` | Shared service layer used by MCP and HTTP. |
| `mcp/legal_texts/resolver.py` | Exact citation parsing and new-unit support point. |
| `mcp/server.py` | MCP tool registration and error wrapping. |
| `mcp/http_api.py` | HTTP route registration. |
| `mcp/http_models.py` | OpenAPI response model definitions. |
| `mcp/tests/test_http_api.py` | Existing HTTP endpoint compatibility tests. |
| `mcp/tests/test_mcp_tools.py` | Existing stable tool contract tests. |
| `scripts/verify_e2e.py` | Local HTTP/MCP E2E command that must include generated fixture coverage. |

## Implementation Steps

### Step 1: Load coverage, limitations, and relationships in the dataset

- **What**: Extend `NormalizedDataset` to optionally load `package.json`, generated package manifest summary, source limitations, and relationship records from Phase 2 files.
- **Where**: `mcp/legal_texts/dataset.py`; relationship helpers in `mcp/legal_texts/relationships.py`.
- **Why**: Runtime APIs should read validated package data instead of recalculating source coverage.
- **Indexes**: Build deterministic in-memory indexes for coverage by source family/state, limitations by `source_family`, `source_id`, and `limitation_id`, and relationships by subject/target IDs. Missing optional files in legacy packages return empty structures with `generated_package_present=false`.
- **Considerations**: Existing fixture packages without optional files must still load and return empty coverage/relationship structures where appropriate.

### Step 2: Add runtime service methods

- **What**: Add `LegalTextRuntime.get_corpus_coverage()`, `get_source_limitations(...)`, and `get_related_norms(...)` or equivalent methods over validated package metadata.
- **Where**: `mcp/legal_texts/runtime.py`.
- **Why**: MCP and HTTP should share the same behavior and error contracts.
- **Response contract**: Coverage responses must include package IDs, source-family counts, terminal-state counts, and generated-package presence. Limitation responses must expose limitation ID, source family/source ID, terminal state, reason, and provenance. Relationship responses must include relationship ID/type, subject/object refs, target summary when resolvable, and provenance only.
- **Considerations**: Relationship responses must return metadata/provenance and target summaries, not legal advice or editorial text.

### Step 3: Add MCP tools additively

- **What**: Register tools such as `get_corpus_coverage`, `get_source_limitations`, and `get_related_norms` in `create_mcp_app`.
- **Where**: `mcp/server.py`; `mcp/tests/test_mcp_tools.py`.
- **Why**: Phase 11 explicitly exposes coverage and relationship surfaces.
- **Considerations**: Update the stable tool list test intentionally; old tool names and response shapes must remain compatible.

### Step 4: Add HTTP endpoints and OpenAPI models

- **What**: Add endpoints such as `/corpus/coverage`, `/corpus/source-limitations`, and `/laws/{code}/norms/{norm}/relationships` with flexible response models.
- **Where**: `mcp/http_api.py`; `mcp/http_models.py`; `mcp/tests/test_http_api.py`.
- **Why**: HTTP should expose the same runtime data as MCP.
- **Considerations**: Existing `/health`, `/ready`, `/laws`, `/laws/{code}`, `/laws/{code}/norms/{norm}`, and `/search` tests must continue to pass.

### Step 5: Add resolver/API coverage for new units

- **What**: Ensure `recital`, `chapter`, `section`, `annex`, and structural containers are accepted or rejected deterministically in `parse_norm_reference` and `resolve_citation`.
- **Where**: `mcp/legal_texts/resolver.py`; `mcp/tests/test_resolver.py`.
- **Why**: Phase 11 acceptance requires positive and negative resolver/API tests for new citation units.
- **Considerations**: Existing child `art:.../par:...` behavior must not regress.

## Testing Plan

Primary verify command: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_runtime_coverage_relationships.py mcp/tests/test_http_api.py mcp/tests/test_mcp_tools.py mcp/tests/test_resolver.py && PYTHONPATH=mcp uv run --group dev python scripts/verify_e2e.py`

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Runtime | Coverage, source limitations, and relationship records load from generated fixture package. | Runtime returns structured metadata and empty data where package files are absent. |
| MCP/HTTP | New additive tools/endpoints expose coverage and related-norm metadata. | Existing tools/endpoints remain compatible. |
| E2E | Local HTTP/MCP E2E exercises generated fixture coverage endpoints/tools. | Transport behavior works outside in-process unit tests. |
| Resolver | New units are accepted or rejected deterministically. | Positive and negative API tests pass. |

### Test Integrity Constraints

- Update `mcp/tests/test_mcp_tools.py::test_tool_registry_has_only_supported_tools` only to add approved Phase 11 tools; do not remove existing tools.
- Existing HTTP OpenAPI path assertions must be extended, not weakened.
- Relationship tests must assert absence of copied editorial text.
- Do not change existing tool names, argument names, or response fields except by additive fields that remain backwards compatible.

## Rollback Strategy

Remove new runtime methods, MCP tools, HTTP endpoints/models, optional dataset loading for coverage/relationships, and tests. Existing law/norm/search/source-metadata runtime behavior remains from Phase 10.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Related-norm surface | Combined coverage endpoint only; dedicated related-norm lookup | Dedicated related-norm lookup plus coverage endpoints | Phase scope calls out related-norm lookup behavior if approved by implementation planning, and package relationships are already validated. |
| Missing optional package files | Error; empty compatible responses | Empty compatible responses with package metadata noting absence | Existing fixture packages must remain compatible. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/legal_texts/runtime.py` | `LegalTextRuntime` methods | Both transports delegate through this service layer. |
| `mcp/server.py` | `create_mcp_app` tool registrations | MCP surface is currently six tools. |
| `mcp/http_api.py` | Route definitions | HTTP currently lacks source metadata, coverage, and relationship endpoints. |
| `mcp/http_models.py` | `SourceMetadataResponse` | A source metadata response model already exists but is not routed. |
| `mcp/legal_texts/resolver.py` | `CANONICAL_NORM_RE`, `parse_norm_reference` | New units need deterministic resolver support. |

### Mismatches / Notes

- Current HTTP API does not expose `get_source_metadata` even though MCP does; Phase 11 can add this or keep source limitations under corpus endpoints, but docs must reflect the chosen route.
- Current `NormalizedDataset` has no optional relationship or limitation indexes.
