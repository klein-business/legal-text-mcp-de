---
type: planning
entity: implementation-plan
plan: "uv-migration"
phase: 1
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 1 - uv Project Foundation

> Implements [Phase 1](../phases/phase-1.md) of [uv-migration](../plan.md)

## Approach

Create a repository-root uv project without packaging the local `mcp/` directory. The project remains a source-run application: commands continue to expose `mcp/` on `PYTHONPATH`, modules such as `server`, `http_api`, `config`, and `legal_texts.*` remain imported as top-level modules, and the external MCP SDK continues to resolve from the installed `mcp[cli]` distribution.

Phase 1 adds only dependency metadata and lock state: `pyproject.toml` and `uv.lock`. Runtime dependencies from `mcp/requirements.txt` become default project dependencies, except the MCP SDK pin is updated from `mcp[cli]==1.10` to `mcp[cli]==1.14.1` because the current source-run import path crashes during tool registration with `mcp[cli]==1.10`. Test and release-gate dependencies used by `mcp/tests/` and `scripts/` go in the `dev` dependency group. Legacy data-preparation dependencies from `prepare_data/requirements.txt` go in the `prepare-data` dependency group. Existing requirements files, Docker behavior, shell scripts, and docs remain unchanged for later phases.

The uv project decision is pinned for this phase: use `[tool.uv] package = false`. This avoids uv trying to install the repository-local `mcp/` directory as a package, which would increase the risk of shadowing the external `mcp.server.fastmcp` SDK import that `mcp/server.py` needs.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | create metadata | Add root dependency metadata for MCP, HTTP, test, and release-gate execution without changing `mcp/` source files. |
| [data-preparation](../../../docs/modules/data-preparation.md) | create metadata | Model the legacy `prepare_data/requirements.txt` dependencies in a separate `prepare-data` dependency group without changing the helper script. |
| [container-runtime](../../../docs/modules/container-runtime.md) | interface note | Preserve a default runtime dependency set that Phase 2 can install for Docker without pulling test or data-preparation groups. |

## Required Context

| File | Why |
|------|-----|
| `plans/uv-migration/plan.md` | Defines the global uv migration scope, canonical `PYTHONPATH=mcp uv run ...` command model, and deferred Docker/docs cleanup. |
| `plans/uv-migration/phases/phase-1.md` | Gated Phase 1 scope, deliverables, acceptance criteria, and explicit exclusions. |
| `plans/uv-migration/todo.md` | Tracks Phase 1 work items and confirms implementation-plan authoring is the current first task. |
| `docs/overview.md` | Documents current setup, run, and test commands that still use venv/pip and must not be rewritten in Phase 1. |
| `docs/modules/mcp-server.md` | Inventory of runtime dependencies, key symbols, test coverage, and current release-gate behavior. |
| `docs/modules/data-preparation.md` | Confirms `prepare_data/` is legacy and should be isolated in its own dependency group. |
| `docs/modules/container-runtime.md` | Confirms Docker currently installs `mcp/requirements.txt`; Docker migration is deferred but needs a runtime-only dependency boundary. |
| `mcp/requirements.txt` | Source of Phase 1 default runtime dependencies: `mcp[cli]==1.10`, `rapidfuzz`, `pydantic-settings`, `fastapi`, and `uvicorn`; MCP SDK is updated in uv metadata for compatibility. |
| `prepare_data/requirements.txt` | Source of Phase 1 `prepare-data` group dependencies, including duplicated `docopt~=0.6.2` that should be deduplicated in `pyproject.toml`. |
| `scripts/verify_release.py` | Shows release verification runs `sys.executable -m pytest` over explicit `mcp/tests/*` files, then invokes `scripts/verify_e2e.py`. |
| `scripts/verify_e2e.py` | Shows E2E subprocesses preserve `PYTHONPATH` with `ROOT / "mcp"` and need runtime dependencies plus external MCP client imports. |
| `mcp/server.py` | Contains the `FastMCP` import and fallback that prove the local `mcp/` tree must not become an installed package in this phase. |
| `mcp/http_api.py` | Uses top-level imports such as `config`, `http_models`, and `legal_texts.runtime`, confirming the `PYTHONPATH=mcp` source-run model. |
| `mcp/tests/test_mcp_tools.py` | Imports `create_mcp_app` from top-level `server`, confirming tests rely on `PYTHONPATH=mcp`. |
| `mcp/tests/test_http_api.py` | Imports top-level `http_api` and `fastapi.testclient.TestClient`, confirming test dependency needs. |
| `mcp/tests/test_error_contracts.py` | Also uses `fastapi.testclient.TestClient`, reinforcing the need for HTTP test-client support in the dev environment. |

## Implementation Steps

### Step 1: Capture the pre-migration release-gate baseline

- **What**: Before adding uv metadata, attempt the current release gate with the existing workflow and record whether it passes, fails, or cannot run because dependencies are absent in the current shell.
- **Where**: `scripts/verify_release.py`, current local Python environment.
- **Why**: Phase 1 prerequisites require confirming current release-gate status or capturing pre-existing failures before attributing any later failures to uv migration.
- **Considerations**: Use the current pre-uv command shape, `PYTHONPATH=mcp python scripts/verify_release.py`, only as a one-time baseline check. If it fails due to missing dependencies or an existing live-source/network issue, record the evidence in implementation notes and continue with uv migration; do not edit tests or runtime code to satisfy the baseline.

### Step 2: Inventory dependencies into uv groups

- **What**: Map existing requirements into a root project dependency model: default runtime dependencies from `mcp/requirements.txt`, `dev` dependencies for `mcp/tests/` and `scripts/verify_release.py`, and `prepare-data` dependencies from `prepare_data/requirements.txt`.
- **Where**: `mcp/requirements.txt`, `prepare_data/requirements.txt`, `scripts/verify_release.py`, `scripts/verify_e2e.py`, `mcp/tests/test_http_api.py`, `mcp/tests/test_error_contracts.py`.
- **Why**: Phase 1 centralizes dependency intent without changing runtime code or retiring legacy requirements files.
- **Considerations**: Update the MCP SDK default runtime dependency to `mcp[cli]==1.14.1` and record the reason: `mcp[cli]==1.10` reproduces a pre-existing import-time failure in `mcp/server.py` when FastMCP registers tools with future annotations. Add `pytest` to `dev` because tests import it directly. Add `httpx` to `dev` because `fastapi.testclient.TestClient` depends on it for the current HTTP tests; do not rely on an incidental transitive install.

### Step 3: Add root uv project metadata

- **What**: Create `pyproject.toml` with `[project]` metadata, Python 3.12 support, default runtime dependencies, `[dependency-groups]` entries for `dev` and `prepare-data`, and `[tool.uv] package = false`.
- **Where**: `pyproject.toml`.
- **Why**: uv needs a repository-level project definition and Phase 1 explicitly requires non-package/source-run app style.
- **Considerations**: Do not add package discovery, build-system metadata, console scripts, or editable-install assumptions. The local `mcp/` directory remains a source directory reached through `PYTHONPATH=mcp`, not an installed distribution.

### Step 4: Generate the lockfile and sync all groups

- **What**: Resolve the root metadata into `uv.lock`, then create the uv environment with all declared dependency groups so runtime, tests, release verification, and legacy data-preparation dependencies are represented.
- **Where**: `uv.lock`, `.venv` managed by uv.
- **Why**: Phase 1 acceptance requires successful dependency resolution and a committed lockfile that covers all in-scope groups.
- **Considerations**: Do not edit `mcp/requirements.txt` or `prepare_data/requirements.txt` in this phase. If resolution fails because of an incompatible transitive dependency, adjust only the new uv metadata and record the exact reason in implementation notes.

### Step 5: Verify source-run imports through uv

- **What**: Run the primary Phase 1 pytest command through uv with `PYTHONPATH=mcp` set, then inspect the resulting behavior for dependency or import-model regressions.
- **Where**: `mcp/tests/`, `mcp/server.py`, `mcp/http_api.py`.
- **Why**: The changed behavior is dependency/environment orchestration, not application logic; the existing tests are the regression boundary for preserving runtime behavior.
- **Considerations**: Do not change MCP tools, HTTP routes, parser behavior, normalizer behavior, resolver behavior, search behavior, fixture data, or tests to make the dependency migration pass. If FastMCP import resolution breaks, keep `[tool.uv] package = false` and fix dependency placement rather than converting `mcp/` into an installed local package.

### Step 6: Record Phase 2 handoff constraints

- **What**: Ensure the final Phase 1 notes identify default dependencies as the future Docker runtime boundary and identify `dev` plus `prepare-data` as non-runtime groups.
- **Where**: `pyproject.toml`, `uv.lock`, Phase 1 implementation completion notes.
- **Why**: Phase 2 will migrate Docker and scripts, so Phase 1 must leave a clear dependency boundary without doing the Docker/script work early.
- **Considerations**: Do not modify `Dockerfile`, `prepare_data/prepare_gesetze_im_internet.sh`, README, or docs in Phase 1.

## Testing Plan

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Primary verification | Run `uv lock --check && uv sync --all-groups && PYTHONPATH=mcp uv run python -c "import server, inspect; assert server.FastMCP.__module__.startswith('mcp.server.fastmcp'), server.FastMCP.__module__; assert '/site-packages/mcp/server/fastmcp/' in inspect.getfile(server.FastMCP), inspect.getfile(server.FastMCP)" && PYTHONPATH=mcp uv run pytest mcp/tests` from the repository root. | The lockfile matches metadata, all dependency groups sync, `server.py` still resolves `FastMCP` from the external MCP SDK distribution instead of the local source tree, and the existing test suite passes under uv while preserving top-level imports from `PYTHONPATH=mcp`. |

### Test Integrity Constraints

- Existing tests under `mcp/tests/` must not be disabled, deleted, renamed, skipped, or weakened to make the uv migration pass.
- `mcp/tests/test_mcp_tools.py` and `mcp/tests/test_http_api.py` must remain source-run import checks for top-level `server` and `http_api` modules.
- `scripts/verify_release.py` and `scripts/verify_e2e.py` must not be changed in Phase 1; any future command migration belongs to Phase 2.
- Fixture data under `mcp/tests/fixtures/` must remain unchanged; dependency migration must not alter dataset behavior.
- If a test fails because of a pre-existing network or source availability issue, capture evidence separately instead of changing the test contract in this phase.
- Real local HTTP/MCP transport E2E is intentionally deferred to Phase 2, where `PYTHONPATH=mcp uv run python scripts/verify_e2e.py` and the focused Docker/runtime verification script exercise those server processes.

## Rollback Strategy

Remove `pyproject.toml` and `uv.lock`, then return to the existing venv/pip workflow using `mcp/requirements.txt` and `prepare_data/requirements.txt`. Because Phase 1 does not modify runtime code, scripts, Dockerfile, docs, requirements files, or fixtures, rollback is limited to deleting the new uv project metadata and lockfile.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| uv project mode | Package install; non-package/source-run | Non-package/source-run with `[tool.uv] package = false` | Current code imports `server`, `http_api`, `config`, and `legal_texts.*` from `PYTHONPATH=mcp`, while `mcp/server.py` must still reach the external `mcp.server.fastmcp` SDK. |
| Runtime dependency placement | Put all dependencies in default; split runtime/test/data-preparation | Default runtime dependencies only; `dev` for tests/release gate; `prepare-data` for legacy helper dependencies | Keeps Phase 2 Docker able to install runtime dependencies without test or legacy data-preparation packages. |
| MCP SDK version | Preserve `mcp[cli]==1.10`; update to a verified compatible pin | Update to `mcp[cli]==1.14.1` | Isolated reproduction shows `mcp[cli]==1.10` crashes on current `mcp/server.py` tool registration with `TypeError: issubclass() arg 1 must be a class`; `1.14.1` resolves the import and passes the existing tests. |
| Python version metadata | Broad Python 3 range; Python 3.12-focused range | Python 3.12 support matching docs and Docker base image | The project docs, plan, and container module all identify Python 3.12 as the supported runtime. |
| Requirements files | Remove now; keep unchanged; convert to shims | Keep unchanged in Phase 1 | Removing or retiring requirements files is explicitly deferred to Phase 3. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/server.py` | `from mcp.server.fastmcp import FastMCP` | Confirms the app depends on the installed external MCP SDK package named `mcp`. |
| `mcp/server.py` | `except ModuleNotFoundError` fallback and `sys.path` filtering | Shows current code already handles local `mcp/` shadowing and should not be made more complex by installing local package mode. |
| `mcp/server.py` | `from config import settings` and `from legal_texts.runtime import LegalTextRuntime` | Confirms source files expect `mcp/` itself on `PYTHONPATH`, not package-qualified local imports. |
| `mcp/http_api.py` | `create_http_app` and top-level imports from `config`, `http_models`, `legal_texts.runtime` | Confirms HTTP tests and uvicorn startup depend on the same source-run import model. |
| `scripts/verify_release.py` | `TESTS` and `cmd = [sys.executable, "-m", "pytest", *TESTS]` | Shows release verification depends on pytest being installed in the active uv environment. |
| `scripts/verify_e2e.py` | `env_for_server` | Shows E2E subprocesses explicitly prepend `ROOT / "mcp"` to `PYTHONPATH` and set fixture-backed dataset startup variables. |
| `scripts/verify_e2e.py` | `import_external_mcp_client` | Confirms the E2E client intentionally removes local repo paths so imports come from the external MCP SDK package. |
| `mcp/tests/test_mcp_tools.py` | `from server import create_mcp_app` | Confirms tests exercise the top-level `server` import through `PYTHONPATH=mcp`. |
| `mcp/tests/test_http_api.py` | `from fastapi.testclient import TestClient` and `from http_api import create_http_app` | Confirms the dev group must support HTTP test-client imports and preserve top-level `http_api`. |
| `mcp/tests/test_error_contracts.py` | `from fastapi.testclient import TestClient` | Confirms HTTP test-client support is used in more than one existing test file. |
| `mcp/requirements.txt` | Runtime dependency list | Defines the default dependency baseline for Phase 1. |
| `prepare_data/requirements.txt` | Legacy helper dependency list | Defines the `prepare-data` group and includes a duplicated `docopt` line that should be represented once. |
| `docs/modules/container-runtime.md` | `RUN pip install --no-cache-dir -r requirements.txt` | Confirms Docker still uses pip/requirements today and must be left for Phase 2. |

### Mismatches / Notes

- `mcp/requirements.txt` pins `mcp[cli]==1.10`, but `PYTHONPATH=/Users/Martin/git/legal-text-mcp-de/mcp uv run --no-project --python 3.12 --with 'mcp[cli]==1.10' ... import server` reproduces `TypeError: issubclass() arg 1 must be a class` during FastMCP tool registration. Phase 1 should use `mcp[cli]==1.14.1`, which resolves `FastMCP` from `site-packages/mcp/server/fastmcp/server.py` and allows the test suite to pass.
- `mcp/requirements.txt` does not include `pytest`, but `scripts/verify_release.py` and many files under `mcp/tests/` require pytest. Phase 1 should add pytest to the `dev` group only.
- The HTTP tests import `fastapi.testclient.TestClient`; add `httpx` explicitly to the `dev` group rather than relying on an incidental transitive install.
- `docs/overview.md` and `docs/modules/container-runtime.md` still document venv/pip and Docker requirements-file workflows. This is expected drift during Phase 1 because README/docs rewrites and Docker migration are explicitly deferred.
- `prepare_data/requirements.txt` lists `docopt~=0.6.2` twice. Represent it once in the `prepare-data` group; do not edit the requirements file in Phase 1.
- No code reality was found that justifies switching away from `[tool.uv] package = false`; the current import model supports the pinned non-package/source-run decision.
- The Phase 1 baseline release-gate check is a pre-change diagnostic. It may expose missing local dependencies in the current shell; the uv-managed post-change verification is the acceptance gate for this phase.
