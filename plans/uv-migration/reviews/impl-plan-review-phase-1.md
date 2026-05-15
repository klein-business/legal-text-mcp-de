---
type: review
entity: implementation-plan-review
plan: "uv-migration"
phase: 1
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 1 - uv Project Foundation

> Reviewing [Phase 1 Implementation Plan](../implementation/phase-1-impl.md)
> Against [Phase 1 Scope](../phases/phase-1.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The plan is mostly executable and matches the current repository shape: `mcp/server.py` really does need the external `mcp.server.fastmcp` SDK while tests and app modules still rely on `PYTHONPATH=mcp` top-level imports. Dependency placement is also consistent with the existing requirements files and test imports. The main revision needed is to add the Phase 1 prerequisite baseline release-gate check before changing dependency metadata, because the current steps only collect post-migration evidence and therefore cannot reliably distinguish uv migration regressions from pre-existing failures.

## Scope Alignment

### Findings

- The implementation plan stays inside Phase 1's code-change boundary: it creates `pyproject.toml` and `uv.lock`, leaves `Dockerfile`, `prepare_data/prepare_gesetze_im_internet.sh`, README/docs rewrites, and requirements-file retirement for later phases, and preserves the source-run import model.
- **Major**: Phase 1 lists "Confirm the current release gate status before migration or capture any pre-existing failures" as a prerequisite, but the implementation steps do not run or record the current `PYTHONPATH=mcp python scripts/verify_release.py` baseline before adding uv metadata. This matters because the plan later allows documenting failures as pre-existing, but without a baseline run there is no evidence for that classification.

## Technical Feasibility

### Findings

- The non-package uv decision is technically sound for this codebase. `mcp/server.py` imports `FastMCP` from `mcp.server.fastmcp` and has fallback `sys.path` filtering because the local `mcp/` directory can shadow the installed SDK, while `mcp/http_api.py` and tests import `config`, `http_api`, `server`, and `legal_texts.*` as top-level modules.
- Dependency grouping is feasible. `mcp/requirements.txt` contains runtime dependencies only; `mcp/tests/` imports `pytest`; HTTP tests use `fastapi.testclient.TestClient`, making explicit `httpx` in `dev` reasonable; `prepare_data/requirements.txt` maps cleanly to a separate `prepare-data` group with duplicated `docopt` represented once.
- **Minor**: The FastMCP verification command prints `server.FastMCP.__module__` but does not assert it. For an implementation gate, the command should fail automatically if the module is not the expected external SDK module, for example by asserting the module name or inspecting the class file path.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Inventory dependencies into uv groups | Yes | Yes | Correctly references actual requirements files, release scripts, and HTTP tests. |
| 2 | Add root uv project metadata | Yes | Yes | Correctly specifies `[dependency-groups]`, Python 3.12 support, and `[tool.uv] package = false`. |
| 3 | Generate the lockfile and sync all groups | Yes | Yes | Command sequence is implied rather than shown here, but the Testing Plan supplies the concrete `uv lock --check`/`uv sync --all-groups` gate after lock generation. |
| 4 | Verify source-run imports through uv | Yes | Mostly | Missing pre-migration baseline release-gate evidence required by Phase 1 prerequisites; FastMCP check is print-only. |
| 5 | Record Phase 2 handoff constraints | Mostly | Mostly | "Phase 1 implementation completion notes" is not a concrete artifact path, but the dependency-boundary requirement is clear enough to execute. |

## Required Context Assessment

### Missing Context

- `README.md`: Not required for edits in Phase 1, but useful as context because it is an active user-facing source of current venv/pip and runtime commands. Omitting it is low risk because `docs/overview.md` covers the same command model and docs rewrites are deferred.

### Unnecessary Context

- None significant. `plans/uv-migration/todo.md` is not essential for dependency implementation, but it is harmless planning context.

## Testing Plan Assessment

### Test Integrity Check

The plan explicitly states that existing tests under `mcp/tests/` must not be disabled, deleted, renamed, skipped, or weakened; calls out `test_mcp_tools.py` and `test_http_api.py` as import-model checks; preserves `scripts/verify_release.py` and `scripts/verify_e2e.py`; and protects fixture data. That is adequate for test integrity.

### Test Gaps

- **Major**: There is no baseline release-gate command before the uv migration even though Phase 1 requires confirming the current release-gate status. Add a pre-change step to run `PYTHONPATH=mcp python scripts/verify_release.py` in the current environment, or document why it cannot be run and capture the exact existing failure evidence before creating `pyproject.toml`/`uv.lock`.
- **Minor**: The primary verify command should make the FastMCP import check self-validating rather than relying on a human to read printed output.

### Real-World Testing

No separate real local transport E2E run is planned in Phase 1. That is acceptable if intentional because Phase 1's acceptance criteria focus on dependency metadata, lock generation, import preservation, and `PYTHONPATH=mcp uv run pytest mcp/tests`; `scripts/verify_e2e.py` and direct server smoke commands are covered by later phases. The implementation plan should state that deferral explicitly so the absence of `PYTHONPATH=mcp uv run python scripts/verify_e2e.py` is a deliberate phase boundary, not an omitted verification.

## Reality Check Validation

### Findings

- The Reality Check accurately identifies the important code anchors. I verified `mcp/server.py` has the `FastMCP` import and shadowing fallback, `mcp/http_api.py` uses top-level imports, `scripts/verify_release.py` shells out to pytest and then `scripts/verify_e2e.py`, and `scripts/verify_e2e.py` deliberately removes local repo paths before importing the external MCP client.
- The noted dependency mismatches are real: `pytest` is absent from `mcp/requirements.txt`, `TestClient` is used in two HTTP test files, and `prepare_data/requirements.txt` duplicates `docopt`.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Scope / Testing | Phase 1 requires confirming current release-gate status before migration, but the implementation steps only run post-uv verification. | Add a pre-change baseline step for `PYTHONPATH=mcp python scripts/verify_release.py`, or record exact evidence if it cannot be run. |
| 2 | Minor | Verify Command | The FastMCP import check prints the module instead of failing automatically on an unexpected result. | Change the verification snippet to assert the expected external SDK module or inspect the class file path outside the repo. |
| 3 | Minor | Real-World Testing | The plan does not explicitly state that local transport E2E is deferred for Phase 1. | Add a short note that `scripts/verify_e2e.py` and direct server smoke tests are intentionally deferred to later phases unless used as supplemental evidence. |

## Recommendations

1. Add an explicit pre-migration release-gate baseline step before dependency metadata changes.
2. Make the FastMCP import verification command self-asserting.
3. Add a short Phase 1 testing note that real local E2E verification is deferred by scope, while preserving the existing `mcp/tests` uv gate.
