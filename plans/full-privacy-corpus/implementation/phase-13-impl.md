---
type: planning
entity: implementation-plan
plan: "full-privacy-corpus"
phase: 13
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 13 - Documentation, diagrams, and release readiness

> Implements [Phase 13](../phases/phase-13.md) of [full-privacy-corpus](../plan.md)

## Approach

Update user-facing, operator-facing, and agent-facing docs after all runtime/source phases are complete. Align README, overview, module docs, feature docs, diagrams, and release gates with the final generated-corpus behavior, and extend docs verification to include README, `docs/`, `docs-legacy/`, and `plans/`.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | modify | Document generated package loading, source adapters, runtime coverage, relationship metadata, and MCP/HTTP APIs. |
| [container-runtime](../../../docs/modules/container-runtime.md) | modify | Document generated dataset mounting and operational expectations. |

## Required Context

| File | Why |
|------|-----|
| `plans/full-privacy-corpus/phases/phase-13.md` | Gated docs/release-readiness scope. |
| `plans/full-privacy-corpus/implementation/phase-12-impl.md` | Final operational gate and benchmark behavior to document. |
| `README.md` | Root user/operator entry point. |
| `docs/overview.md` | Project architecture and feature/module inventory. |
| `docs/modules/mcp-server.md` | Module docs for runtime, adapters, tests, and scripts. |
| `docs/features/law-loading-and-indexing.md` | Generated package loading and fixture-vs-production explanation. |
| `docs/features/source-provenance.md` | Official source provenance and relationship-source metadata. |
| `docs/features/supported-laws.md` | Expanded supported/generated corpus scope. |
| `docs/features/mcp-law-tools.md` | MCP runtime tool contract after Phase 11. |
| `docs/features/http-api.md` | HTTP endpoints after Phase 11. |
| `docs/features/known-issues.md` | Scope/invariants and non-legal-advice boundaries. |
| `scripts/verify_release.py` | Release gate and docs placeholder/stale workflow checks. |
| `scripts/verify_ci_workflow.py` | Existing workflow verification to keep aligned if present. |

## Implementation Steps

### Step 1: Update root and overview docs

- **What**: Update `README.md` and `docs/overview.md` to explain fixture vs generated production corpus, full-corpus generation flow, official sources, operational gates, and unchanged product boundaries.
- **Where**: `README.md`; `docs/overview.md`.
- **Why**: Users and future agents need a correct entry point after the corpus expansion.
- **Considerations**: Do not claim full generated corpus data is committed to Git.

### Step 2: Update module and feature docs

- **What**: Update `docs/modules/mcp-server.md`, `docs/features/law-loading-and-indexing.md`, `docs/features/source-provenance.md`, `docs/features/supported-laws.md`, `docs/features/mcp-law-tools.md`, `docs/features/http-api.md`, and `docs/features/known-issues.md`.
- **Where**: Existing docs files.
- **Why**: These docs currently describe the fixture-backed source matrix and six-tool runtime.
- **Considerations**: Relationship metadata must be documented separately from official legal text; source limitations must be queryable and reproducible.

### Step 3: Add diagrams where they clarify behavior

- **What**: Add Mermaid architecture/sequence diagrams for discovery, normalization, generated package loading, citation resolution, coverage APIs, and relationship lookup.
- **Where**: Markdown docs updated in Step 2.
- **Why**: The full corpus workflow spans multiple source families and operational gates.
- **Diagram set**: Include at minimum one architecture/data-flow diagram for source discovery to generated package, one sequence diagram for explicit full-corpus gate execution, and one request-flow diagram for citation/relationship lookup through MCP/HTTP.
- **Considerations**: Diagrams should clarify data flow, not replace precise text or commands.

### Step 4: Extend docs verification

- **What**: Update docs verification in `scripts/verify_release.py` or add a dedicated docs check so README, `docs/`, `docs-legacy/`, and `plans/` are scanned for unresolved placeholders, stale workflow commands, and broken local Markdown links/images.
- **Where**: `scripts/verify_release.py`; possibly `scripts/verify_docs.py`; tests under `mcp/tests/test_release_gate.py`.
- **Why**: Acceptance requires docs link/image checks across all documentation roots.
- **Link/image contract**: The docs check must parse Markdown image syntax and local links across `README.md`, `docs/`, `docs-legacy/`, and `plans/`; local targets must exist, anchors should be validated when practical, and remote URLs/images may be reported separately without making fast CI depend on network unless a cached/explicit mode is used.
- **Considerations**: Preserve current stale workflow checks that reject unsupported direct `PYTHONPATH=mcp python` commands.

### Step 5: Final release-readiness verification

- **What**: Ensure the fast release gate passes and docs mention how to run opt-in corpus gates and where validation bundles are stored.
- **Where**: `scripts/verify_release.py`; docs from Steps 1-4.
- **Why**: Phase 13 closes the plan with release-ready documentation and verification.
- **Considerations**: Do not run network-heavy full-corpus gates by default unless explicitly requested outside PR CI.

## Testing Plan

Primary verify command: `PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Release | Full fixture-backed release gate and local HTTP/MCP E2E. | Command exits successfully. |
| Docs | README, docs, docs-legacy, and plans contain no unresolved placeholders, stale commands, or broken local links/images. | Verification reports no docs violations. |
| Regression | Existing runtime tests still pass after docs/check updates. | No source behavior changes are introduced. |

### Test Integrity Constraints

- Do not weaken `scripts/verify_release.py` checks to make docs pass.
- Do not delete docs references to unresolved operational limitations; document them accurately.
- Do not add network-heavy corpus gate execution to the default release command.

## Rollback Strategy

Revert docs edits and verification-script changes. Source/runtime code from earlier phases remains intact, but release-readiness documentation would no longer be accurate.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Docs check location | Fold into `verify_release.py`; separate script called by release gate | Separate script called by release gate if checks become complex | Keeps release behavior centralized while avoiding overloading `verify_release.py`. |
| Diagram placement | One architecture page; inline in relevant feature docs | Inline in relevant feature docs | Readers encounter diagrams next to the behavior they explain. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `docs/overview.md` | Architecture, modules, feature inventory | Currently describes fixture-backed official sources and current test commands. |
| `docs/modules/mcp-server.md` | Structure, key symbols, test coverage | Needs new source adapters, manifest/package validation, and runtime coverage APIs. |
| `docs/features/law-loading-and-indexing.md` | Current data contract | Currently lists only four serving package files. |
| `docs/features/source-provenance.md` | Metadata fields and source rules | Needs source limitations, state law, EU neighbors, and relationship-source metadata. |
| `scripts/verify_release.py` | `check_docs_links`, `check_no_stale_workflow_refs` | Current docs checks scan only `docs` for placeholders and selected roots for stale commands. |

### Mismatches / Notes

- Current docs list supported scope as a committed legal-audit fixture set, not a generated full corpus.
- Current docs link/image checks do not cover `README.md`, `docs-legacy/`, or `plans/` comprehensively.
