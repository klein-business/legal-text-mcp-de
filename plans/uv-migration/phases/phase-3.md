---
type: planning
entity: phase
plan: "uv-migration"
phase: 3
status: completed
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 3: Documentation and Cleanup

> Part of [uv-migration](../plan.md)

## Objective

Make uv the documented and maintained workflow across the repository, then remove or explicitly retire obsolete requirements-based paths.

## Scope

### Includes

- Update README setup, run, Docker, and test sections to use uv.
- Update docs under `docs/` that reference `python3 -m venv`, `pip`, requirements files, or `PYTHONPATH=mcp python` commands where uv commands are now preferred.
- Document that `google-adk-agent/` remains an optional legacy demo outside the core uv-managed runtime unless a future task adds explicit ADK dependency management.
- Decide the final state of `mcp/requirements.txt` and `prepare_data/requirements.txt`: remove them, replace them with compatibility notes, or document them as retired.
- Grep for stale dependency-management instructions and reconcile all supported references.
- Run final verification after documentation and cleanup changes.

### Excludes (deferred to later phases)

- Feature documentation unrelated to setup, packaging, runtime, or verification.
- Changes to archived documentation under `docs-legacy/` unless an implementation plan explicitly decides to add a short archival note.
- New CI automation or release publishing.

## Prerequisites

- [x] Phase 1 is complete.
- [x] Phase 2 is complete.
- [x] The final uv command set has been verified.

## Deliverables

- [x] README updated to uv-first commands.
- [x] Relevant docs under `docs/` updated to uv-first commands and dependency references.
- [x] Optional Google ADK demo scope boundary documented in active docs.
- [x] Requirements-file cleanup completed according to the chosen compatibility decision.
- [x] Final stale-reference search results reviewed.
- [x] Final verification results recorded in the implementation notes or handover.

## Acceptance Criteria

- [x] `rg -n "python3 -m venv|pip install -r|requirements\\.txt|source \\.venv/bin/activate|source venv/bin/activate" README.md docs scripts mcp prepare_data Dockerfile` returns no unsupported active-workflow references.
- [x] `uv sync --all-groups` succeeds.
- [x] `PYTHONPATH=mcp uv run python scripts/verify_release.py` succeeds.
- [x] `PYTHONPATH=mcp uv run python scripts/verify_e2e.py` succeeds.
- [x] Docker verification from Phase 2 still succeeds after cleanup.
- [x] The repository has a clear single supported dependency workflow: uv.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| 1 | blocked-by | Requires uv project metadata and lockfile. |
| 2 | blocked-by | Requires final runtime, script, and Docker command surfaces. |

## Notes

Archived legacy docs can retain historical commands if they are intentionally archival. Active docs should not direct users to requirements-based installation after this phase.
