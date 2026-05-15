---
type: planning
entity: implementation-plan
plan: "uv-migration"
phase: 2
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 2 - Runtime, Scripts, and Docker

> Implements [Phase 2](../phases/phase-2.md) of [uv-migration](../plan.md)

## Approach

Move the supported runtime surfaces to the Phase 1 uv project without changing application behavior, source imports, legal text parsing, normalized fixtures, MCP tools, or HTTP contracts. Preserve the Phase 1 decisions: `[tool.uv] package = false`, source-run app style, and canonical commands that set `PYTHONPATH=mcp` for host-side execution.

Update the Docker image to install only the default runtime dependency set from `pyproject.toml` and `uv.lock`. The image should copy a pinned uv binary from `ghcr.io/astral-sh/uv:0.10.12`, copy root uv metadata before source files for cacheable dependency installation, run `uv sync --frozen --no-dev --no-group prepare-data --no-install-project`, copy `mcp/` as source, set `PYTHONPATH=/app/mcp`, and run the MCP server from source. The final container command should be `CMD ["uv", "run", "--frozen", "--no-sync", "python", "mcp/server.py"]`. The image must not sync the `dev` or `prepare-data` groups.

Update `prepare_data/prepare_gesetze_im_internet.sh` to stop creating or activating a helper-owned `venv` and stop running `pip install -r`. The script should run the legacy upstream helper commands through this repo's uv project with `--group prepare-data`, and it should add a no-network dry-run mode that validates the `prepare-data` dependency group via uv without cloning or executing upstream downloads.

Add one focused verification script, `scripts/verify_uv_runtime_docker.py`, as the single Phase 2 command surface for changed behavior. The script should first assert the helper script no longer contains the retired normal-path workflow strings (`python3 -m venv`, `source venv/bin/activate`, `pip install -r`, `requirements.txt`), run the data-preparation syntax and dry-run checks, verify release and E2E commands under uv, smoke the exact canonical MCP and HTTP `uv run` startup commands with fixture data, build the Docker image, start it with the fixture dataset mounted at `/data/legal-texts`, and perform a host-side MCP initialize/list-tools handshake against `http://127.0.0.1:8001/mcp`.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [container-runtime](../../../docs/modules/container-runtime.md) | modify | Replace requirements-file Docker installation with runtime-only uv sync and run `mcp/server.py` from source with `/data/legal-texts` mounted data. |
| [data-preparation](../../../docs/modules/data-preparation.md) | modify | Replace nested venv/pip orchestration in `prepare_data/prepare_gesetze_im_internet.sh` with uv `prepare-data` group execution and add dry-run/no-network validation. |
| [mcp-server](../../../docs/modules/mcp-server.md) | verify/create | Preserve existing MCP/HTTP runtime source behavior and add a focused Phase 2 verification script for uv runtime and Docker smoke checks. |

## Required Context

| File | Why |
|------|-----|
| `plans/uv-migration/plan.md` | Defines global uv migration requirements, canonical `PYTHONPATH=mcp uv run ...` commands, Docker smoke criteria, and Phase 3 documentation cleanup boundary. |
| `plans/uv-migration/phases/phase-2.md` | Gated Phase 2 scope, deliverables, acceptance criteria, and explicit exclusions. |
| `plans/uv-migration/implementation/phase-1-impl.md` | Pins `[tool.uv] package = false`, source-run app style, default runtime dependencies, `dev`, and `prepare-data` dependency groups. |
| `plans/uv-migration/todo.md` | Shows current plan sequencing and the expected handoff from Phase 1 to Phase 2. |
| `docs/overview.md` | Documents the current venv/pip and direct Python commands that Phase 2 must not rewrite in docs yet. |
| `docs/modules/mcp-server.md` | Inventories runtime symbols, canonical test coverage, `scripts/verify_release.py`, and `scripts/verify_e2e.py`. |
| `docs/modules/data-preparation.md` | Confirms `prepare_data/` is legacy and not part of production serving, which keeps dry-run validation bounded. |
| `docs/modules/container-runtime.md` | Documents current Docker behavior, `/data/legal-texts`, `STRICT_STARTUP=true`, and the requirements-file install that Phase 2 replaces. |
| `pyproject.toml` | Phase 1 output that must contain `[tool.uv] package = false`, default runtime dependencies, `dev`, and `prepare-data`. |
| `uv.lock` | Phase 1 output used by `uv sync --frozen` in Docker and by all uv-backed verification commands. |
| `Dockerfile` | Current image copies only `mcp/`, installs `mcp/requirements.txt` with pip, sets `DATASET_PATH`, and starts `python server.py`. |
| `prepare_data/prepare_gesetze_im_internet.sh` | Current helper creates `venv`, activates it, runs `pip install -r ../requirements.txt`, and executes upstream `lawde.py`/`lawdown.py`. |
| `prepare_data/requirements.txt` | Historical dependency source already modeled by Phase 1 as the `prepare-data` group; do not continue installing it directly. |
| `scripts/verify_release.py` | Existing release gate uses `sys.executable -m pytest` and then invokes `scripts/verify_e2e.py`, so it should work when called by `uv run`. |
| `scripts/verify_e2e.py` | Existing E2E helper starts HTTP/MCP subprocesses with fixture data and contains reusable MCP client handshake logic. |
| `mcp/server.py` | `create_mcp_app`, `mcp.run(transport="streamable-http")`, `settings.host`, and `settings.port` define direct and Docker MCP startup behavior. |
| `mcp/http_api.py` | `create_http_app` and `app = create_http_app()` define the canonical uvicorn target `http_api:app`. |
| `mcp/tests/test_release_gate.py` | Guards production files against bundled Bundestag data paths and `/app/gesetze` regressions; Docker edits must keep these tests meaningful. |
| `mcp/tests/test_mcp_tools.py` | Defines the expected MCP tool names used by the Docker client smoke: `list_laws`, `get_law`, `get_norm`, `resolve_citation`, `search_laws`, and `get_source_metadata`. |
| `mcp/tests/test_http_api.py` | Confirms `/ready` with fixture data must report `stage == "serving_dataset"` for HTTP startup verification. |
| `uv --version`, `uv sync --help`, `uv run --help` | Confirm local uv CLI support for `--all-groups`, `--group`, `--frozen`, `--offline`, `--project`, `--no-sync`, and `--no-install-project` before implementing the scripted command surfaces. |

## Implementation Steps

### Step 1: Confirm Phase 1 uv outputs before touching runtime files

- **What**: Verify `pyproject.toml` and `uv.lock` exist and that `pyproject.toml` preserves `[tool.uv] package = false`, default runtime dependencies, `dev`, and `prepare-data`.
- **Where**: `pyproject.toml`, `uv.lock`, `plans/uv-migration/implementation/phase-1-impl.md`.
- **Why**: Phase 2 Docker and script changes depend on Phase 1 dependency metadata and lock state.
- **Considerations**: If the files are missing or the group names differ, stop and resolve Phase 1 first; do not invent alternate group names or switch to package mode in Phase 2.

### Step 2: Migrate the Dockerfile to runtime-only uv sync

- **What**: Replace the current pip/requirements image with a uv-managed image that installs runtime dependencies only, then runs the server from source.
- **Where**: `Dockerfile`.
- **Why**: Phase 2 requires the container to use uv metadata while keeping runtime behavior equivalent.
- **Considerations**: Use `WORKDIR /app`; copy uv from the pinned official image with `COPY --from=ghcr.io/astral-sh/uv:0.10.12 /uv /uvx /bin/`; copy `pyproject.toml` and `uv.lock`; run `uv sync --frozen --no-dev --no-group prepare-data --no-install-project --compile-bytecode`; then copy `mcp/ ./mcp/`. Preserve `ENV DATASET_PATH=/data/legal-texts`, `ENV STRICT_STARTUP=true`, set `ENV PYTHONPATH=/app/mcp`, and keep `HOST=0.0.0.0`/`PORT=8001` behavior. The final command should be `CMD ["uv", "run", "--frozen", "--no-sync", "python", "mcp/server.py"]`. Do not install `dev` or `prepare-data` dependencies in the image.

### Step 3: Migrate the data-preparation helper to uv with dry-run validation

- **What**: Replace helper-owned venv creation, activation, and `pip install -r` with uv project execution, and add a no-network validation mode.
- **Where**: `prepare_data/prepare_gesetze_im_internet.sh`.
- **Why**: The plan requires dependency installation/invocation through uv and a validation path that does not run the full upstream import.
- **Considerations**: Add `set -euo pipefail`, derive `SCRIPT_DIR` and `ROOT_DIR`, and accept `--dry-run` plus `--no-network` as aliases. In dry-run/no-network mode, do not run `git clone`, `lawde.py loadall`, or `lawdown.py convert`; instead run a uv-managed import probe from `ROOT_DIR`, for example `uv run --frozen --offline --group prepare-data --no-dev python -c "import git, yaml, docopt, lxml, cssselect, requests, bs4, roman_numbers"`. In normal mode, keep the upstream clone/check directory behavior and execute from `prepare_data/gesetze-tools` so `lawde.py`, `lawdown.py`, `laws`, and `laws_md` resolve as before; while that directory is the current working directory, run `uv run --project "$ROOT_DIR" --frozen --group prepare-data --no-dev python lawde.py loadall` and `uv run --project "$ROOT_DIR" --frozen --group prepare-data --no-dev python lawdown.py convert laws laws_md`.

### Step 4: Preserve release and E2E scripts unless uv execution proves a defect

- **What**: Run `scripts/verify_release.py` and `scripts/verify_e2e.py` through uv and change them only if they fail because of a Phase 2 command-assumption issue.
- **Where**: `scripts/verify_release.py`, `scripts/verify_e2e.py`.
- **Why**: Both scripts already use `sys.executable` and explicit environment construction, so the expected path is to preserve behavior while invoking them from uv.
- **Considerations**: Keep `PYTHONPATH=mcp` as the host-side command model. Do not rewrite tests, fixture data, MCP tools, HTTP routes, source import semantics, or legal-text runtime behavior. If changes are required, keep them limited to subprocess command construction or shared helper reuse for uv/Docker verification.

### Step 5: Add the focused Phase 2 verification script

- **What**: Create `scripts/verify_uv_runtime_docker.py` as the single primary Phase 2 verification command.
- **Where**: `scripts/verify_uv_runtime_docker.py`, with reuse of helper logic from `scripts/verify_e2e.py` where practical.
- **Why**: Phase 2 has multiple long-running surfaces; a focused script gives one repeatable command that exercises changed runtime, script, and Docker behavior.
- **Considerations**: The script should statically fail if `prepare_data/prepare_gesetze_im_internet.sh` still contains the retired workflow strings `python3 -m venv`, `source venv/bin/activate`, `pip install -r`, or `requirements.txt`; run `bash -n` on the helper; run the helper dry-run/no-network mode; run `scripts/verify_release.py` under uv with `PYTHONPATH=mcp`; smoke direct MCP startup by launching the exact command shape `uv run python mcp/server.py` with environment variables `DATASET_PATH=mcp/tests/fixtures/normalized`, `STRICT_STARTUP=true`, `PYTHONPATH=mcp`, `HOST=127.0.0.1`, and a free `PORT`; smoke direct HTTP startup by launching the exact command shape `uv run uvicorn http_api:app --host 127.0.0.1 --port <free-port>` with `DATASET_PATH=mcp/tests/fixtures/normalized`, `STRICT_STARTUP=true`, and `PYTHONPATH=mcp`, then request `/ready`; build `legal-text-mcp-de:uv-migration`; run the container with `-p 8001:8001 -v "$PWD/mcp/tests/fixtures/normalized:/data/legal-texts:ro"`; perform the same MCP initialize/list-tools assertion against `http://127.0.0.1:8001/mcp`; and always tear down subprocesses/containers it starts.

### Step 6: Keep Phase 3 cleanup out of this phase

- **What**: Leave README, active docs, `mcp/requirements.txt`, and `prepare_data/requirements.txt` cleanup for Phase 3.
- **Where**: `README.md`, `docs/`, `mcp/requirements.txt`, `prepare_data/requirements.txt`.
- **Why**: Phase 2 verifies the final runtime and Docker command surfaces before documentation and retirement cleanup.
- **Considerations**: Do not update docs to uv-first commands yet, and do not remove or mark requirements files as retired in this phase.

## Testing Plan

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Primary verification | Run `uv sync --all-groups && PYTHONPATH=mcp uv run --group dev python scripts/verify_uv_runtime_docker.py` from the repository root after Phase 1 is complete. | The command makes the offline `prepare-data` dry-run self-contained, validates retired workflow strings are absent from the helper, checks the data-preparation dry-run/no-network path, release and E2E uv execution, exact canonical direct MCP and HTTP `uv run` startup commands, Docker image build, container startup with mounted fixture data, and host-side MCP initialize/list-tools smoke against the container. |

### Test Integrity Constraints

- Existing tests under `mcp/tests/` must not be disabled, deleted, renamed, skipped, or weakened to make Docker or uv command checks pass.
- `mcp/tests/test_release_gate.py` must remain an active guard against bundled Bundestag data paths, `/app/gesetze`, and unrelated SaaS scope in production files.
- `mcp/tests/test_mcp_tools.py` expected tool names must remain unchanged; Docker smoke verification should assert the same tool set rather than introduce a separate expected contract.
- `mcp/tests/test_http_api.py` and `mcp/tests/test_error_contracts.py` must remain unchanged because Phase 2 should not alter HTTP routes or error payloads.
- `scripts/verify_release.py` and `scripts/verify_e2e.py` may only be adjusted for uv-compatible subprocess invocation if needed; their behavioral coverage must not be narrowed.
- Fixture data under `mcp/tests/fixtures/normalized/` must remain unchanged; startup checks must use existing fixture data.

## Rollback Strategy

Revert `Dockerfile`, `prepare_data/prepare_gesetze_im_internet.sh`, and `scripts/verify_uv_runtime_docker.py` to the pre-Phase 2 state. Keep Phase 1 `pyproject.toml` and `uv.lock` intact, because Phase 2 is layered on top of the uv project foundation. If Docker is broken but host uv commands still work, temporarily use the Phase 1 host commands while restoring the previous requirements-file Dockerfile.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Docker dependency scope | Runtime default only; all groups; dev plus runtime | Runtime default only with `uv sync --frozen --no-dev --no-group prepare-data --no-install-project` | The image serves MCP only and must not include test or legacy data-preparation dependencies. |
| Docker uv binary source | Install with pip; run installer script; copy from pinned official uv image | Copy `/uv` and `/uvx` from `ghcr.io/astral-sh/uv:0.10.12` | Provides a reproducible Docker build-time uv binary without reintroducing pip-based dependency management. |
| Docker execution style | Install local package; run from copied source; copy only `mcp/` as `/app` | Run from copied source with `PYTHONPATH=/app/mcp` | Preserves Phase 1 source-run model and avoids installing the local `mcp/` directory as a package. |
| Docker final command | `python server.py`; `.venv/bin/python mcp/server.py`; `uv run --no-sync python mcp/server.py` | `CMD ["uv", "run", "--frozen", "--no-sync", "python", "mcp/server.py"]` | Runs through the uv-managed project environment while avoiding runtime re-sync after the image build. |
| Data-preparation validation | Full upstream import; shell syntax only; no-network uv dependency probe | No-network uv dependency probe plus shell syntax | Proves uv-managed `prepare-data` dependencies without cloning or downloading upstream data. |
| Docker smoke mechanism | Port check; HTTP probe; MCP protocol initialize/list-tools | Host-side MCP protocol initialize/list-tools | Streamable HTTP is protocol-specific; the smoke should verify the tool surface, not only that a port is open. |
| Verification command shape | Several manual commands; reuse release gate only; focused Phase 2 script | `uv sync --all-groups && PYTHONPATH=mcp uv run --group dev python scripts/verify_uv_runtime_docker.py` | A single primary shell command establishes all groups for offline probes, then orchestrates script, runtime, release, E2E, Docker build/run, and MCP client smoke checks. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `Dockerfile` | `COPY mcp/ .` and `RUN pip install --no-cache-dir -r requirements.txt` | Shows the current image is not uv-managed and lacks root metadata, so Phase 2 must restructure copy/install order. |
| `Dockerfile` | `ENV DATASET_PATH=/data/legal-texts`, `ENV STRICT_STARTUP=true`, `CMD ["python", "server.py"]` | Defines the runtime behavior that must remain equivalent after changing to source-run uv execution. |
| `prepare_data/prepare_gesetze_im_internet.sh` | `python3 -m venv venv`, `source venv/bin/activate`, `pip install -r ../requirements.txt` | Exact nested venv/pip workflow Phase 2 must remove. |
| `prepare_data/prepare_gesetze_im_internet.sh` | `git clone "$REPO_URL"`, `python lawde.py loadall`, `python lawdown.py convert laws laws_md` | Identifies the network/full-import operations that dry-run/no-network mode must avoid. |
| `prepare_data/requirements.txt` | `GitPython`, `PyYAML`, `docopt`, `lxml`, `cssselect`, `requests`, `beautifulsoup4`, `roman-numbers` | Defines the dependency import probe for uv-managed `prepare-data` validation. |
| `scripts/verify_release.py` | `cmd = [sys.executable, "-m", "pytest", *TESTS]` and `e2e_cmd = [sys.executable, "scripts/verify_e2e.py"]` | Confirms the release gate should inherit the uv interpreter when run through `uv run`. |
| `scripts/verify_e2e.py` | `env_for_server` | Confirms fixture-backed startup variables and `PYTHONPATH` handling for subprocess smoke checks. |
| `scripts/verify_e2e.py` | `run_mcp_e2e` and `session.list_tools()` | Provides the exact host-side MCP initialize/list-tools behavior to reuse for Docker smoke verification. |
| `scripts/verify_e2e.py` | `run_http_e2e` and `/ready` assertions | Confirms HTTP startup verification should prove dataset readiness, not only `/health`. |
| `mcp/server.py` | `create_mcp_app`, `settings.host`, `settings.port`, `mcp.run(transport="streamable-http")` | Defines the MCP server entry point and transport the Docker container must expose. |
| `mcp/http_api.py` | `app = create_http_app()` | Confirms the uvicorn target `http_api:app` used by canonical HTTP startup. |
| `mcp/tests/test_release_gate.py` | `test_no_default_app_gesetze_serving_path` | Keeps Docker edits from reintroducing a bundled `/app/gesetze` serving path. |
| `mcp/tests/test_mcp_tools.py` | `test_tool_registry_has_only_supported_tools` | Defines the expected MCP tool names for host and container smoke checks. |
| `mcp/tests/test_http_api.py` | `test_health_and_ready` | Confirms `/ready` should report a fixture-backed serving dataset. |

### Mismatches / Notes

- The current checkout does not contain `pyproject.toml` or `uv.lock` yet, so Phase 2 is blocked until Phase 1 has actually produced those files. This implementation plan assumes the Phase 1 decisions in `plans/uv-migration/implementation/phase-1-impl.md` are implemented before Phase 2 starts.
- `plans/uv-migration/todo.md` still lists Phase 1 as the active phase. That is consistent with writing this Phase 2 implementation plan ahead of execution, but Phase 2 implementation should not start until the primary advances the plan state.
- `scripts/verify_release.py` and `scripts/verify_e2e.py` already appear uv-compatible because they use `sys.executable` and explicit subprocess environments. The expected implementation is to leave them unchanged unless verification exposes a concrete uv-specific failure.
- Active README/docs still contain venv, pip, and direct Python commands. That drift is expected during Phase 2 because documentation cleanup is explicitly deferred to Phase 3.
