---
type: planning
entity: plan
plan: "uv-migration"
status: completed
created: "2026-05-15"
updated: "2026-05-15"
---

# Plan: uv-migration

## Objective

Migrate the repository from ad hoc `venv`/`pip`/`requirements.txt` workflows to a reproducible `uv`-managed Python project for local development, tests, data preparation, and container builds.

## Motivation

The repository currently has dependency and execution entry points spread across `mcp/requirements.txt`, `prepare_data/requirements.txt`, README commands, docs, shell scripts, verification scripts, and the Dockerfile. Moving to `uv` centralizes dependency metadata, produces a lockfile for reproducible installs, makes release verification easier to run consistently, and removes drift between local, CI-like, and container workflows.

## Requirements

### Functional

- [x] Add a repository-level `pyproject.toml` that captures Python 3.12 support and the runtime/test/data-preparation dependencies currently represented by the existing requirements files.
- [x] Configure the uv project as non-package/source-run app style, expected as `[tool.uv] package = false`, unless an implementation plan explicitly proves a different mode keeps the external `mcp` dependency importable.
- [x] Use default project dependencies for the MCP/HTTP runtime, a `dev` dependency group for tests and release verification, and a `prepare-data` dependency group for the legacy data-preparation helper.
- [x] Generate and commit a `uv.lock` that resolves all in-scope dependency groups.
- [x] Provide and verify these canonical uv command paths while preserving the current `PYTHONPATH=mcp` import model:
  - MCP server: `DATASET_PATH=mcp/tests/fixtures/normalized STRICT_STARTUP=true PYTHONPATH=mcp uv run python mcp/server.py`
  - HTTP API: `DATASET_PATH=mcp/tests/fixtures/normalized STRICT_STARTUP=true PYTHONPATH=mcp uv run uvicorn http_api:app --host 127.0.0.1 --port 8080`
  - Release verification: `PYTHONPATH=mcp uv run python scripts/verify_release.py`
  - E2E verification: `PYTHONPATH=mcp uv run python scripts/verify_e2e.py`
- [x] Update the Docker build to install and run through the uv-managed project environment.
- [x] Update the legacy data-preparation helper script so dependency installation is handled by `uv`, not a nested manually activated virtualenv plus `pip`.
- [x] Add a no-network or dry-run validation path for the data-preparation helper so the uv migration can be checked without running the full upstream import.
- [x] Update README and project docs so all supported setup, run, test, and container commands use `uv`.
- [x] Remove or clearly retire obsolete requirements-file workflows after the uv paths are validated.

### Non-Functional

- [x] Preserve current Python 3.12 behavior and the existing import model unless a phase explicitly replaces it with a tested package layout.
- [x] Keep every phase independently testable and leave the repository in a runnable state.
- [x] Avoid broad runtime refactors unrelated to dependency and command migration.
- [x] Keep Docker image behavior equivalent: server process starts with `/data/legal-texts` as `DATASET_PATH` and `STRICT_STARTUP=true`.
- [x] Ensure documentation remains consistent with the actual commands verified during the migration.

## Scope

### In Scope

- Repository-level uv project metadata, lockfile, and dependency groups.
- Migration of `mcp/requirements.txt` and `prepare_data/requirements.txt` dependency intent into `pyproject.toml`.
- Updates to `Dockerfile`, `prepare_data/prepare_gesetze_im_internet.sh`, README, and docs that reference pip/venv/requirements workflows.
- Verification commands in `scripts/verify_release.py` and `scripts/verify_e2e.py` as needed to work cleanly through `uv run`.
- Cleanup or compatibility handling for old requirements files.
- A documentation note that the optional `google-adk-agent/` demo is outside the core uv-managed runtime unless a later explicit requirement brings it into scope.

### Out of Scope

- Changing legal text parsing, source import semantics, MCP tool contracts, HTTP API behavior, or normalized fixture data.
- Reworking the optional Google ADK demo beyond documenting or preserving its current relationship to the uv-managed project.
- Adding CI provider configuration unless it is already present and directly references pip/requirements.
- Publishing packages to PyPI or changing repository licensing.

## Definition of Done

- [x] `uv sync --all-groups` succeeds from a clean checkout.
- [x] `PYTHONPATH=mcp uv run pytest mcp/tests` succeeds, or the documented release gate supersedes it with an equivalent tested command.
- [x] `PYTHONPATH=mcp uv run python scripts/verify_release.py` succeeds.
- [x] `PYTHONPATH=mcp uv run python scripts/verify_e2e.py` succeeds.
- [x] Direct uv-backed MCP and HTTP startup commands are smoke-tested with the fixture dataset.
- [x] Data-preparation helper syntax and dry-run/no-network validation succeed.
- [x] Docker image `legal-text-mcp-de:uv-migration` builds successfully and starts the MCP server with `-p 8001:8001 -v "$PWD/mcp/tests/fixtures/normalized:/data/legal-texts:ro"`; a host-side MCP client initialize/list-tools smoke check succeeds against the container.
- [x] README and docs no longer instruct supported users to create a venv or install project dependencies with `pip install -r`.
- [x] Obsolete requirements files are removed, converted to documented compatibility shims, or explicitly marked as retired.

## Testing Strategy

- [x] Run dependency resolution with `uv lock` and environment creation with `uv sync --all-groups`.
- [x] Run unit and integration tests through uv: `PYTHONPATH=mcp uv run pytest mcp/tests`.
- [x] Run the release gate through uv: `PYTHONPATH=mcp uv run python scripts/verify_release.py`.
- [x] Run local network E2E through uv: `PYTHONPATH=mcp uv run python scripts/verify_e2e.py`.
- [x] Smoke-test direct server commands:
  - `DATASET_PATH=mcp/tests/fixtures/normalized STRICT_STARTUP=true PYTHONPATH=mcp uv run python mcp/server.py`
  - `DATASET_PATH=mcp/tests/fixtures/normalized STRICT_STARTUP=true PYTHONPATH=mcp uv run uvicorn http_api:app --host 127.0.0.1 --port 8080`, then request `/ready` or a fixture-backed endpoint.
- [x] Validate the data-preparation helper with `bash -n prepare_data/prepare_gesetze_im_internet.sh` and the implemented dry-run/no-network command.
- [x] Build `legal-text-mcp-de:uv-migration` and smoke-test server startup against `mcp/tests/fixtures/normalized` with an explicit port/mount command plus MCP client initialize/list-tools check.
- [x] Grep documentation and scripts for stale `venv`, `pip install -r`, and `requirements.txt` instructions before completion.

## Phases

| Phase | Title | Scope | Status |
|-------|-------|-------|--------|
| 1 | uv Project Foundation | [Detail](phases/phase-1.md) | completed |
| 2 | Runtime, Scripts, and Docker | [Detail](phases/phase-2.md) | completed |
| 3 | Documentation and Cleanup | [Detail](phases/phase-3.md) | completed |

## Risks & Open Questions

| Risk/Question | Impact | Mitigation/Answer |
|---------------|--------|-------------------|
| The repository-local `mcp/` directory can shadow the installed `mcp` package. | Naive package-layout changes could break current imports or the FastMCP fallback logic. | Phase 1 should preserve the current `PYTHONPATH=mcp` execution model unless a verified implementation plan intentionally changes it. |
| Existing requirements are loosely pinned except for `mcp[cli]==1.10` and several preparation dependencies. | `uv.lock` may resolve newer transitive versions than the current local environment. | Treat the generated lockfile as the reproducibility boundary and run the full release gate before accepting it. |
| `prepare_data/prepare_gesetze_im_internet.sh` checks out a separate upstream repository. | It may need dependencies installed into the helper checkout while still using this repo's uv metadata. | Keep this phase bounded to dependency orchestration and smoke-check script syntax; do not rewrite the upstream tool workflow. |
| Docker may require a different layout once dependencies are centralized at repo root. | Incorrect copy/install order can break runtime import paths or cache efficiency. | Update Docker in its own phase and verify with a build plus MCP client initialize/list-tools smoke test. |
| Optional Google ADK demo dependencies are not represented in current requirements files. | Pulling them into the core uv environment could expand install size and resolution complexity. | Keep ADK out of core dependencies unless implementation discovery shows it is part of supported verification. |

## Changelog

### 2026-05-15

- Plan completed after Phase 3 implementation and second-pass implementation review reported Accepted with zero findings.
- Phase 2 completed after runtime, data-preparation, Docker, and MCP client smoke verification; Phase 3 started.
- Phase 1 completed after resolving the MCP SDK compatibility issue; Phase 2 started.
- Plan review gate passed after four review iterations with zero remaining findings.
- Revised after third plan review: pinned non-package/source-run uv project mode and strengthened Docker smoke testing to an MCP client initialize/list-tools check.
- Revised after second plan review: normalized all test and release gates to `PYTHONPATH=mcp uv run ...` and strengthened the HTTP direct smoke check to prove dataset readiness.
- Revised after plan review: added canonical uv runtime commands, dependency group names, data-preparation dry-run validation, objective Docker smoke criteria, and explicit Google ADK scope boundary.

### 2026-05-15

- Plan created.
