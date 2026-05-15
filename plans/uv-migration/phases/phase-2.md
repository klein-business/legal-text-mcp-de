---
type: planning
entity: phase
plan: "uv-migration"
phase: 2
status: completed
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 2: Runtime, Scripts, and Docker

> Part of [uv-migration](../plan.md)

## Objective

Move supported runtime surfaces from direct Python, pip, and hand-managed virtualenv workflows to uv-backed commands and container installation.

## Scope

### Includes

- Update `Dockerfile` to install dependencies through uv-managed metadata and run the server with equivalent runtime environment variables.
- Update `prepare_data/prepare_gesetze_im_internet.sh` so this repo's preparation dependencies are installed or invoked through uv rather than nested `venv` activation plus `pip install -r`.
- Add a dry-run or no-network validation mode for `prepare_data/prepare_gesetze_im_internet.sh`.
- Update release and E2E command assumptions where necessary so they run under `uv run`.
- Verify the canonical MCP startup command through uv against the fixture dataset: `DATASET_PATH=mcp/tests/fixtures/normalized STRICT_STARTUP=true PYTHONPATH=mcp uv run python mcp/server.py`.
- Verify the canonical HTTP startup command through uv against the fixture dataset: `DATASET_PATH=mcp/tests/fixtures/normalized STRICT_STARTUP=true PYTHONPATH=mcp uv run uvicorn http_api:app --host 127.0.0.1 --port 8080`.
- Verify Docker build and startup with a concrete tag, dataset mount, and host-side MCP client initialize/list-tools smoke check.

### Excludes (deferred to later phases)

- Broad documentation rewrites.
- Removing retired requirement files.
- Changing source import, normalization, or API behavior.
- Adding provider-specific CI configuration.

## Prerequisites

- [x] Phase 1 is complete.
- [x] `uv sync --all-groups` succeeds.
- [x] The implementation plan identifies the exact Docker install strategy, including runtime-only vs all-group sync, project-install vs source-run behavior, and the final Docker `CMD`.

## Deliverables

- [x] Updated `Dockerfile`.
- [x] Updated `prepare_data/prepare_gesetze_im_internet.sh`.
- [x] Verified uv-backed commands for MCP, HTTP API, release gate, and E2E.
- [x] Verified syntax and dry-run/no-network command for the data-preparation helper.
- [x] Docker build and MCP client smoke-test evidence using image tag `legal-text-mcp-de:uv-migration`.

## Acceptance Criteria

- [x] `DATASET_PATH=mcp/tests/fixtures/normalized STRICT_STARTUP=true uv run --env-file` is not required; normal environment variable prefixes work with uv-backed server commands.
- [x] `DATASET_PATH=mcp/tests/fixtures/normalized STRICT_STARTUP=true PYTHONPATH=mcp uv run python mcp/server.py` starts the MCP server with the fixture dataset.
- [x] `DATASET_PATH=mcp/tests/fixtures/normalized STRICT_STARTUP=true PYTHONPATH=mcp uv run uvicorn http_api:app --host 127.0.0.1 --port 8080` serves `/ready` or another fixture-backed endpoint successfully.
- [x] `PYTHONPATH=mcp uv run python scripts/verify_release.py` succeeds.
- [x] `PYTHONPATH=mcp uv run python scripts/verify_e2e.py` succeeds.
- [x] `bash -n prepare_data/prepare_gesetze_im_internet.sh` succeeds.
- [x] The implemented data-preparation dry-run/no-network command succeeds and proves the script uses uv-managed dependencies.
- [x] `docker build -t legal-text-mcp-de:uv-migration .` succeeds.
- [x] `docker run --rm -p 8001:8001 -v "$PWD/mcp/tests/fixtures/normalized:/data/legal-texts:ro" legal-text-mcp-de:uv-migration` starts the MCP server and a host-side MCP client can initialize and list the expected tools through `http://127.0.0.1:8001/mcp` before teardown.
- [x] The data-preparation helper no longer creates or activates its own `venv` for this repo's dependencies.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| 1 | blocked-by | Requires the uv dependency model and lockfile. |
| 3 | blocks | Documentation and cleanup should reflect the commands verified here. |

## Notes

The Dockerfile currently copies only `mcp/` into `/app` and installs `mcp/requirements.txt`. A uv-based Dockerfile should copy `pyproject.toml`, `uv.lock`, and the runtime source needed to run from source. Runtime dependencies should be installed without `dev` or `prepare-data` groups unless the implementation plan records a verified reason to include them. Container verification should use an MCP protocol handshake rather than only checking that a TCP port is open.
