---
type: review
entity: implementation-review
plan: "uv-migration"
phase: 2
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Review: Phase 2 - Runtime, Scripts, and Docker

> Reviewing implementation of [Phase 2](../phases/phase-2.md)
> Against [Implementation Plan](../implementation/phase-2-impl.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Accepted

The implementation satisfies the Phase 2 Definition of Done for the changed runtime surfaces. Docker now installs and runs from the uv-managed project environment, the data-preparation helper uses the `prepare-data` group without a nested venv/pip path, and the Phase 2 verifier exercises the host uv commands, dry-run script path, release/E2E gates, Docker build, and MCP initialize/list-tools handshake. I found no blocking or follow-up findings.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Normal environment variables work; `uv run --env-file` is not required. | Yes | `scripts/verify_uv_runtime_docker.py` passes explicit `DATASET_PATH`, `STRICT_STARTUP`, and `PYTHONPATH` in `env_for_server()` and starts both uv runtime commands; local verifier exited 0. | None |
| 2 | `DATASET_PATH=mcp/tests/fixtures/normalized STRICT_STARTUP=true PYTHONPATH=mcp uv run python mcp/server.py` starts the MCP server with fixture data. | Yes | `verify_direct_mcp_startup()` starts `["uv", "run", "python", "mcp/server.py"]` with fixture env, waits for the port, and performs MCP initialize/list-tools; local verifier exited 0. | None |
| 3 | `DATASET_PATH=mcp/tests/fixtures/normalized STRICT_STARTUP=true PYTHONPATH=mcp uv run uvicorn http_api:app --host 127.0.0.1 --port 8080` serves `/ready` or another fixture-backed endpoint. | Yes | `verify_direct_http_startup()` starts uvicorn with `http_api:app`, fixture env, and `--host 127.0.0.1`, then asserts `/ready` has `stage == "serving_dataset"`; local verifier exited 0. It uses a free port instead of hard-coded 8080 to avoid collisions, without changing the uvicorn target or readiness behavior. | None |
| 4 | `PYTHONPATH=mcp uv run python scripts/verify_release.py` succeeds. | Yes | `verify_release_and_e2e()` runs release through `uv run --group dev`; output showed 52 pytest cases passed and the release script's E2E invocation succeeded. | None |
| 5 | `PYTHONPATH=mcp uv run python scripts/verify_e2e.py` succeeds. | Yes | `verify_release_and_e2e()` runs E2E through `uv run --group dev`; output showed `HTTP CLI E2E OK` and `MCP streamable HTTP E2E OK`. | None |
| 6 | `bash -n prepare_data/prepare_gesetze_im_internet.sh` succeeds. | Yes | `verify_prepare_data_script()` runs `bash -n`; local verifier exited 0. | None |
| 7 | Data-preparation dry-run/no-network command succeeds and proves uv-managed dependencies. | Yes | The helper's dry-run path runs `uv run --project "$ROOT_DIR" --frozen --offline --group prepare-data --no-dev python -c ...`; the verifier ran both `--dry-run` and `--no-network` successfully. | None |
| 8 | `docker build -t legal-text-mcp-de:uv-migration .` succeeds. | Yes | `verify_docker_runtime()` builds the exact image tag; local Docker build completed and named `legal-text-mcp-de:uv-migration`. | None |
| 9 | Docker run with mounted fixture data starts MCP and host-side client can initialize/list expected tools through `/mcp`. | Yes | `verify_docker_runtime()` runs the container with `/data/legal-texts:ro`, maps host to container port 8001, and calls the same initialize/list-tools assertion used for direct MCP. Local verifier exited 0. | None |
| 10 | Data-preparation helper no longer creates or activates its own `venv`. | Yes | Helper contains only uv execution for dependency-managed commands; `rg` found the retired normal-path strings only inside the verifier's negative assertions, not in the helper. | None |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Confirm Phase 1 uv outputs. | `pyproject.toml` and `uv.lock` exist; `pyproject.toml` has `[tool.uv] package = false`, default runtime dependencies, `dev`, and `prepare-data`. | No | Satisfies the prerequisite for runtime and Docker work. |
| 2 | Migrate Dockerfile to runtime-only uv sync. | Dockerfile copies pinned uv, root uv metadata, runs `uv sync --frozen --no-dev --no-group prepare-data --no-install-project --compile-bytecode`, copies `mcp/`, sets runtime env, and runs `uv run --frozen --no-sync python mcp/server.py`. | No | Matches the planned Docker uv strategy and avoids dev/prepare-data groups in the image. |
| 3 | Migrate data-preparation helper to uv with dry-run. | Helper uses `set -euo pipefail`, derives root paths, supports `--dry-run`/`--no-network`, validates imports with offline uv, and runs upstream helper commands through `uv run --project "$ROOT_DIR" --group prepare-data`. | No | Normal and dry-run paths align with the implementation plan. |
| 4 | Preserve release and E2E scripts unless uv defects appear. | Existing release/E2E scripts were not modified; the new verifier invokes them through uv. | No | Scope is respected and behavioral coverage is preserved. |
| 5 | Add focused Phase 2 verification script. | `scripts/verify_uv_runtime_docker.py` covers static contracts, helper syntax/dry-run, release/E2E, direct MCP/HTTP starts, Docker build/run, and MCP protocol handshake. | No material deviation | The script uses free host ports for repeatability while preserving command targets and container internal port 8001. |
| 6 | Keep Phase 3 cleanup out of this phase. | README/docs and requirements-file retirement are unchanged. | No | Correctly deferred to Phase 3. |

## Code Quality Assessment

### Findings

No findings.

The Dockerfile is minimal and cache-friendly for uv: metadata is copied before source, only runtime dependencies are installed, `PYTHONPATH=/app/mcp` preserves the source-run model, and the final command avoids runtime sync. The shell helper is simple and fails closed with `set -euo pipefail`; unsupported arguments exit non-zero, dry-run avoids clone/download work, and normal execution keeps the upstream working directory semantics while using this repo's uv project.

## Testing Assessment

### Verify Command Result

- **Command**: `uv sync --all-groups && PYTHONPATH=mcp uv run --group dev python scripts/verify_uv_runtime_docker.py`
- **Exit Code**: 0
- **Result**: Passed locally on 2026-05-15.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `verify_static_files()` | Docker uv contract, helper uv contract, and absence of retired venv/pip workflow strings. | Yes | Static string checks are intentionally narrow, but backed by behavioral smoke tests. |
| `verify_prepare_data_script()` | Shell syntax plus dry-run and no-network dependency validation. | Yes | Does not run the full upstream import, which is appropriate for the dry-run requirement. |
| `verify_release_and_e2e()` | Existing release gate and direct E2E under uv. | Yes | Preserves the existing broad test suite and startup checks. |
| `verify_direct_mcp_startup()` | Direct uv-backed MCP server startup and protocol initialize/list-tools. | Yes | Verifies behavior rather than only checking that a process starts. |
| `verify_direct_http_startup()` | Direct uv-backed HTTP startup and fixture-backed `/ready`. | Yes | Catches dataset readiness regressions. |
| `verify_docker_runtime()` | Docker build, mounted fixture dataset, exposed streamable HTTP MCP endpoint, and expected tool registry. | Yes | Strong integration coverage for the container surface. |

### Real-World Testing

Performed. The verifier executed real host subprocesses, made real HTTP requests against direct uvicorn and MCP servers, built the Docker image, ran the container, and completed a host-side MCP initialize/list-tools handshake against the container endpoint. The data-preparation full upstream import was not performed; that is consistent with the phase's bounded dry-run/no-network acceptance criterion.

## Scope Compliance

### Findings

No findings.

The implementation touches the intended Phase 2 runtime files: `Dockerfile`, `prepare_data/prepare_gesetze_im_internet.sh`, and the new Phase 2 verifier. Existing MCP runtime behavior, HTTP routes, normalized fixtures, and documentation cleanup are left out of scope as planned.

## Regression Risk

### Test Integrity Check

- [x] No existing tests were deleted.
- [x] No existing tests were disabled.
- [x] No existing assertions were weakened.
- [x] All pre-existing tests still pass through the release gate.

### Findings

No findings.

`git diff -- mcp/tests scripts/verify_release.py scripts/verify_e2e.py` is empty, so the existing tests and release/E2E scripts were not weakened to make Phase 2 pass. The local verifier output shows the release gate ran 52 tests successfully before the E2E and Docker smoke checks.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| - | - | - | No findings. | No action required. |

## Recommendations

1. Proceed to Phase 3 documentation and cleanup, where the now-verified uv commands can be reflected in README/docs and obsolete requirements-file workflows can be retired or marked explicitly.
