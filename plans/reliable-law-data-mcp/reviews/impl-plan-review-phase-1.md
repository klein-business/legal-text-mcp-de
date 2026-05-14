---
type: review
entity: implementation-plan-review
plan: "reliable-law-data-mcp"
phase: 1
status: final
reviewer: "general"
created: "2026-05-14"
---

# Implementation Plan Review: Phase 1 - Domain Contracts and Dataset Layout

> Reviewing [Phase 1 Implementation Plan](../implementation/phase-1-impl.md)
> Against [Phase 1 Scope](../phases/phase-1.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Major Gaps

The implementation plan is directionally aligned with Phase 1 as a documentation/contract phase and its runtime code anchors match the current codebase. It is not yet executable without guessing because it does not plan concrete schema/dataset-layout deliverables required by the phase scope, and the primary verification command fails as written.

## Scope Alignment

### Findings

- **Major**: Phase 1 scope requires domain records and contract/schema files for laws, source metadata, raw snapshots, normalized laws, norms, subdivisions, search results, citation requests/responses, structured errors, and dataset layout (`phases/phase-1.md:23-24`, `phases/phase-1.md:51-56`). The implementation plan only finalizes `source-matrix.md`, `fixture-inventory.md`, and a `contracts.md` that currently covers identifiers, citation rules, error envelope fields, readiness states, MCP migration, and search ranking (`implementation/phase-1-impl.md:45-64`, `contracts.md:15-84`). It never tells the implementer where to define the missing record schemas, response shapes, raw/normalized/manifest directory layout, or field-level required/optional/known-issue classifications, so later phases would still have to invent core contracts.
- **Minor**: Step 4 asks the implementer to align Phase 1 through Phase 9 docs "where they depend on" the artifacts (`implementation/phase-1-impl.md:66-71`). That stays within the general Phase 1 deliverable to link contracts to later phases, but it is broad enough that the implementer must decide which phase files and sections are actually in scope.

## Technical Feasibility

### Findings

- The runtime reality check is mostly accurate. `mcp/config.py` still defaults to `/app/gesetze/`, `mcp/parser.py` is a Markdown paragraph parser backed by SQLite FTS, `mcp/server.py` exposes legacy `get_lawlibrary`, `get_paragraph`, and `search_laws` tools returning strings, and the `Dockerfile` still clones `bundestag/gesetze` (`mcp/config.py:3-7`, `mcp/parser.py:30-43`, `mcp/parser.py:195-216`, `mcp/server.py:21-62`, `Dockerfile:5-6`). A no-runtime-code Phase 1 is technically feasible.
- **Major**: Source validation is not technically actionable. Step 5 says to run source URL probe checks (`implementation/phase-1-impl.md:73-78`), and the source matrix says rows were probe-checked and must be re-validated (`source-matrix.md:13`, `source-matrix.md:35-42`), but the plan provides no concrete command, expected headers, invalid-path checks, timeout behavior, or output criteria for those probes. The test table downgrades this to manual review (`implementation/phase-1-impl.md:120-124`), which is not enough for a verified source matrix.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Finalize Source Matrix | Yes | Mostly | File and required columns are clear, but probe validation is deferred to a vague later check. |
| 2 | Finalize Fixture Inventory | Yes | Yes | Required citation families and EGBGB child semantics are concrete. |
| 3 | Finalize Shared Contracts | No | Partly | Covers identifier/error/readiness/search decisions but omits phase-required domain record schemas, dataset layout, and MCP/HTTP response-shape contracts. |
| 4 | Align Phase Docs and Todo | Partly | Partly | All phase docs are named, but exact target sections/dependency links are left to judgment. |
| 5 | Validate Plan Artifact Integrity | No | No | Primary command fails as written and does not perform the promised source URL probes. |

## Required Context Assessment

### Missing Context

- `docs/overview.md` - The user supplied it as a review input and it gives the project architecture, current source-loading options, and canonical test command. The implementation plan lists more specific docs, but the overview is still useful context for a fresh executor.

### Unnecessary Context

- None. The listed code files are reference-only, but they are needed to validate the reality check and planned migration boundaries.

## Testing Plan Assessment

### Test Integrity Check

The plan states that existing runtime tests under `mcp/tests/` are unaffected, must not be disabled, and are not replaced by Phase 1 artifact checks (`implementation/phase-1-impl.md:126-130`). That addresses test weakening at a high level. However, the proposed primary verify command is not currently usable and does not exercise the source-probe portion of Phase 1.

### Test Gaps

- **Major**: The primary verify command fails against the current repository. I ran it from the repository root on 2026-05-14 and it exited 1 with `FAIL plans/reliable-law-data-mcp/implementation/phase-1-impl.md: unresolved template placeholder`. The failure is caused by the command scanning fenced code blocks and finding its own literal `{{` / `}}` placeholder-check strings (`implementation/phase-1-impl.md:84-117`).
- **Major**: There is no automated or copy-pasteable source probe check, despite Step 5 promising source URL probes and the source matrix requiring validation of German index/XML URLs, DSGVO XML content type, and invalid `tddsg`/`pangv` paths (`implementation/phase-1-impl.md:73-78`, `source-matrix.md:35-42`).
- **Minor**: The verify command only checks file existence, links, and placeholders. It would not detect whether the missing schema/dataset-layout contracts are actually present unless those artifacts become named required files or specific required headings/fields are asserted.

### Real-World Testing

Real-world testing is only planned as manual source matrix review. Because this phase locks external legal-source URLs and content-type assumptions, the implementation plan should include a deterministic HTTP probe command or script before Phase 1 is considered ready. No waiver is documented.

## Reality Check Validation

### Findings

- **Major**: The reality check validates current runtime code anchors, but it does not acknowledge the current plan-artifact gap: `contracts.md` does not yet contain concrete law/norm/source/search/citation response schemas or dataset layout sections. Since Phase 1 is contract-only, artifact completeness is part of the reality check, not just codebase anchoring.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Scope Alignment | Implementation steps omit concrete Phase 1 schema and dataset-layout deliverables required by the phase scope. | Add explicit steps and target files/sections for law, source metadata, raw snapshot, normalized law, norm, subdivision, search result, citation request/response, structured error, MCP/HTTP response, manifest, and dataset layout contracts. |
| 2 | Major | Testing | Primary verify command fails as written by detecting its own `{{` / `}}` strings inside the implementation plan code block. | Fix the command to ignore fenced code blocks or restrict placeholder checks to artifact prose/frontmatter, then rerun it successfully. |
| 3 | Major | Testing / Source Validation | Source URL probe checks are required but not specified as an executable verification step. | Add a deterministic probe script or command covering all source matrix URLs, invalid path regressions, DSGVO XML content type, and expected statuses. |
| 4 | Minor | Step Quality | Step 4 leaves all Phase 1-9 dependency-link updates to judgment. | Name the phase files/sections or acceptance criteria that must link to each support artifact. |
| 5 | Minor | Required Context | `docs/overview.md` is omitted from Required Context despite being supplied and relevant for fresh orientation. | Add `docs/overview.md` to Required Context or explain why the narrower docs supersede it. |
| 6 | Note | Technical Feasibility | Code anchors in the reality check match current files and support a no-runtime-code Phase 1. | Keep Phase 1 constrained to contracts and defer runtime edits to later phases. |

## Recommendations

1. Revise Step 3 and/or add new steps for the missing domain schemas, MCP/HTTP response shapes, metadata classifications, and dataset directory layout.
2. Replace the primary verify command with one that passes against the implementation plan itself and asserts the required contract artifacts/sections.
3. Add an executable source probe verification for source matrix URLs, DSGVO content type, and known invalid paths.
4. Tighten Step 4 so the expected phase-doc/todo updates are bounded and reviewable.
