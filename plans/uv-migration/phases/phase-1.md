---
type: planning
entity: phase
plan: "uv-migration"
phase: 1
status: completed
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 1: uv Project Foundation

> Part of [uv-migration](../plan.md)

## Objective

Establish the repository as a uv-managed Python 3.12 project with centralized dependency metadata and a committed lockfile, while preserving the existing runnable import model.

## Scope

### Includes

- Add repository-level `pyproject.toml`.
- Configure uv as non-package/source-run app style, expected as `[tool.uv] package = false`.
- Model runtime dependencies from `mcp/requirements.txt`.
- Model test and release-gate dependencies needed by `mcp/tests/` and `scripts/` in a `dev` dependency group.
- Model data-preparation dependencies from `prepare_data/requirements.txt` in a separate `prepare-data` dependency group.
- Generate `uv.lock`.
- Verify core test execution through uv without changing runtime behavior.

### Excludes (deferred to later phases)

- Dockerfile changes.
- Data-preparation shell script changes.
- README and docs rewrites.
- Removing or retiring requirements files.
- Refactoring the `mcp/` source layout.
- Installing the local `mcp/` directory as a package.

## Prerequisites

- [x] Confirm `uv` is installed or document the bootstrap command used during implementation.
- [x] Confirm the current release gate status before migration or capture any pre-existing failures.
- [x] Review current requirements files and test imports for dependency coverage.
- [x] Preserve the canonical import model for this phase: direct uv commands continue to set `PYTHONPATH=mcp`.
- [x] Preserve external MCP SDK resolution by avoiding uv package mode for the local `mcp/` directory.

## Deliverables

- [x] `pyproject.toml` with project metadata, Python requirement, `[tool.uv] package = false`, default runtime dependencies, `dev` dependency group, and `prepare-data` dependency group.
- [x] `uv.lock` generated from the committed dependency metadata.
- [x] A verified uv command for tests, expected to be `PYTHONPATH=mcp uv run pytest mcp/tests`.
- [x] Notes in the implementation plan about how the existing `PYTHONPATH=mcp` behavior is preserved.

## Acceptance Criteria

- [x] `uv lock` succeeds.
- [x] `uv sync --all-groups` succeeds.
- [x] `PYTHONPATH=mcp uv run pytest mcp/tests` succeeds or any failure is documented as pre-existing with evidence.
- [x] `PYTHONPATH=mcp uv run python -c "import server; print(server.FastMCP.__module__)"` confirms `server.py` still resolves FastMCP from the external `mcp.server.fastmcp` SDK module.
- [x] The implementation plan records default-vs-group dependency placement and how Docker can sync runtime-only dependencies later.
- [x] No MCP, HTTP API, parser, normalizer, resolver, or dataset behavior is intentionally changed in this phase.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| 2 | blocks | Runtime, script, and Docker migration depends on the uv project foundation. |
| 3 | blocks | Documentation and cleanup depends on the final command model introduced here and in Phase 2. |

## Notes

The current server is run with `PYTHONPATH=mcp python mcp/server.py`, and `mcp/server.py` contains fallback logic because the local `mcp/` directory can shadow the external `mcp` package. This phase should avoid package-layout churn unless the implementation plan proves a small change is safer than preserving the current model.
