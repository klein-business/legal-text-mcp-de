---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 12
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 12: Documentation, diagrams, and release readiness

> Part of [full-privacy-corpus](../plan.md)

## Objective

Update project documentation and release gates so operators and future agents can
understand, verify, and maintain the full generated corpus.

## Scope

### Includes

- Update feature docs for supported laws, source provenance, law loading,
  indexing, MCP tools, HTTP API, and scope/invariants.
- Update module docs for source adapters, generated package loading, runtime
  coverage, and relationship metadata.
- Add Mermaid architecture and sequence diagrams where they clarify corpus
  discovery, normalization, package loading, and citation resolution.
- Add or update docs link and image checks.
- Final release-readiness verification over fast CI and available corpus gates.

### Excludes (deferred to later phases)

- New corpus source adapter work.
- New runtime features beyond documentation alignment.
- Generated production dataset commits.

## Prerequisites

- [ ] All implementation phases that change runtime or source behavior are
      complete.

## Deliverables

- [ ] Updated `docs/overview.md`.
- [ ] Updated affected module and feature docs.
- [ ] Architecture and sequence diagrams in Markdown.
- [ ] Docs link/image verification.
- [ ] Final release-readiness checklist.

## Acceptance Criteria

- [ ] Docs describe fixture vs generated production corpus accurately.
- [ ] Docs explain official text provenance and third-party relationship
      metadata.
- [ ] Docs explain complete GII coverage measurement through the manifest.
- [ ] Docs explain DSGVO articles, recitals, and related privacy-law scope.
- [ ] Release gates pass after documentation updates.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 11 | blocked-by | Docs should include final operational gate behavior. |

## Notes

This phase should use `update-docs` after implementation changes are complete.
