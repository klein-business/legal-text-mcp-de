---
type: review
entity: implementation-plan-review
plan: "uv-migration"
phase: 2
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 2 - Runtime, Scripts, and Docker

> Reviewing [Phase 2 Implementation Plan](../implementation/phase-2-impl.md)
> Against [Phase 2 Scope](../phases/phase-2.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The implementation plan is directionally aligned with Phase 2 and most referenced code anchors match the current repository reality. However, it leaves several material execution risks unresolved: the Docker uv acquisition strategy is not exact enough for the phase prerequisite, the no-network data-prep validation is not self-contained under the single primary verify command, and the verifier requirements can pass without proving all acceptance-critical command paths.

## Scope Alignment

### Findings

- The plan stays within Phase 2 boundaries: it targets `Dockerfile`, `prepare_data/prepare_gesetze_im_internet.sh`, existing verification scripts only if needed, and a new focused runtime/Docker verifier. It correctly defers README/docs cleanup and requirements-file retirement to Phase 3.
- The current checkout does not contain `pyproject.toml` or `uv.lock`; the Phase 2 plan correctly treats that as a prerequisite and records the block in its Reality Check rather than expanding Phase 2 scope.

## Technical Feasibility

### Findings

- **Major**: The Docker plan does not identify the exact uv installation/acquisition strategy. Phase 2 prerequisites require the implementation plan to identify the exact Docker install strategy, but Step 2 only says to "install or copy a uv executable." Since `python:3.12-slim` does not include `uv`, the implementer still has to choose between a pinned official uv image copy, installer script, pip install, or another mechanism. That choice affects reproducibility, cache behavior, and whether `uv sync --frozen` is available at build time.
- **Major**: The data-preparation dry-run is not reliably self-contained under the proposed single verify command. The primary verifier is invoked as `PYTHONPATH=mcp uv run --group dev python scripts/verify_uv_runtime_docker.py`, but the dry-run path is supposed to execute `uv run --frozen --offline --group prepare-data --no-dev ...`. On a clean environment where the `prepare-data` group has not already been installed or cached, the offline probe can fail before proving script behavior. The plan relies on the prerequisite that `uv sync --all-groups` succeeds, but the single verification command does not explicitly establish that state.
- **Minor**: The normal data-preparation path is feasible with `uv run --project "$ROOT_DIR" --frozen --group prepare-data --no-dev ...` from the upstream helper checkout, but the plan should make the intended working directory explicit. The command needs to execute while the shell is still in `prepare_data/gesetze-tools` so `lawde.py`, `lawdown.py`, `laws`, and `laws_md` resolve as before.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Confirm Phase 1 uv outputs before touching runtime files | Yes | Yes | No material issue. |
| 2 | Migrate the Dockerfile to runtime-only uv sync | Partial | Partial | Leaves uv binary acquisition unspecified despite the phase prerequisite for an exact Docker strategy. |
| 3 | Migrate the data-preparation helper to uv with dry-run validation | Partial | Partial | Dry-run command is concrete, but offline feasibility depends on prior group installation/cache state not guaranteed by the single verifier. |
| 4 | Preserve release and E2E scripts unless uv execution proves a defect | Yes | Yes | Existing `scripts/verify_release.py` and `scripts/verify_e2e.py` are consistent with this assumption because they use `sys.executable` and explicit subprocess environments. |
| 5 | Add the focused Phase 2 verification script | Partial | Partial | Does not explicitly require the script to launch the canonical host commands via `uv run`; also does not require static checks proving the data-prep normal path no longer contains venv/pip commands. |
| 6 | Keep Phase 3 cleanup out of this phase | Yes | Yes | No material issue. |

## Required Context Assessment

### Missing Context

- `uv sync --help` / `uv run --help` semantics, or an equivalent pinned uv version note: needed because the plan depends on group flags, `--offline`, `--project`, `--no-sync`, and `--no-install-project` behavior.

### Unnecessary Context

- No material unnecessary context found for the requested execution-risk review.

## Testing Plan Assessment

### Test Integrity Check

The plan explicitly says existing tests under `mcp/tests/` must not be disabled, deleted, renamed, skipped, or weakened. It also preserves `test_release_gate.py`, `test_mcp_tools.py`, HTTP tests, error-contract tests, and fixture data. That is adequate for test integrity.

### Test Gaps

- **Major**: The primary verifier can be implemented in a way that does not prove the canonical host startup commands required by Phase 2. Step 5 says to smoke direct HTTP and MCP startup, but it does not pin subprocess argv to `DATASET_PATH=... STRICT_STARTUP=true PYTHONPATH=mcp uv run python mcp/server.py` and `DATASET_PATH=... STRICT_STARTUP=true PYTHONPATH=mcp uv run uvicorn http_api:app --host 127.0.0.1 --port 8080`. If the verifier reuses `scripts/verify_e2e.py` with `sys.executable`, it tests the uv environment but not the documented `uv run` command surfaces.
- **Major**: The data-prep verifier checks `bash -n` and dry-run behavior, but the plan does not require a static assertion that the normal path no longer contains `python3 -m venv`, `source venv/bin/activate`, or `pip install -r`. The dry-run branch can pass while stale venv/pip commands remain reachable in the normal branch, which would miss a Phase 2 acceptance criterion.

### Real-World Testing

Real-world integration testing is planned: direct HTTP `/ready`, direct MCP initialize/list-tools, Docker image build, container startup with mounted fixture data, and host-side MCP initialize/list-tools against `http://127.0.0.1:8001/mcp`. The coverage is appropriate, but the command-shape gaps above need to be closed so the integration checks prove the exact accepted runtime surfaces.

## Reality Check Validation

### Findings

- The referenced code reality is accurate for the reviewed files: `Dockerfile` currently copies only `mcp/` and installs `mcp/requirements.txt`; `prepare_data/prepare_gesetze_im_internet.sh` currently creates and activates `venv` and runs `pip install -r`; `scripts/verify_release.py` and `scripts/verify_e2e.py` are interpreter-driven; `mcp/server.py` exposes streamable HTTP through `mcp.run(transport="streamable-http")`; and `mcp/config.py` defaults to host `0.0.0.0` and port `8001`.
- The Reality Check honestly notes that `pyproject.toml` and `uv.lock` are absent in the current checkout. That is not a Phase 2 implementation-plan defect as long as Phase 2 remains blocked until Phase 1 actually lands.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Docker uv strategy | Docker migration leaves uv binary acquisition unspecified, despite the phase prerequisite requiring an exact Docker install strategy. | Specify a concrete, pinned mechanism, such as copying `/uv` and `/uvx` from a pinned `ghcr.io/astral-sh/uv` image or another reproducible equivalent. |
| 2 | Major | Data-prep dry-run/no-network | The offline `prepare-data` dry-run can fail on a clean env/cache because the single primary verifier only syncs the `dev` group before invoking the script. | Make the verifier establish the needed state before the offline probe, or make the primary verify command include an explicit `uv sync --frozen --all-groups` prerequisite step. |
| 3 | Major | Verify command actionability | The verifier can pass without proving the canonical `uv run` MCP and HTTP startup command shapes required by Phase 2 acceptance criteria. | Require exact subprocess argv for the canonical MCP and HTTP uv commands inside `scripts/verify_uv_runtime_docker.py`. |
| 4 | Major | Data-prep verification | Dry-run plus `bash -n` does not prove the normal script path removed venv activation and `pip install -r`. | Add static assertions or shared command construction so the verifier fails if the script still contains or reaches the retired venv/pip workflow. |
| 5 | Minor | Data-prep normal mode | The uv normal-mode command depends on remaining in the upstream checkout working directory while using this repo as the uv project. | State the required cwd explicitly in Step 3 to avoid accidentally running `lawde.py` from the repo root. |

## Recommendations

1. Revise Step 2 to name the exact Docker uv installation mechanism and versioning strategy.
2. Revise the verification plan so `scripts/verify_uv_runtime_docker.py` explicitly runs the two canonical host startup commands through `uv run`.
3. Make the single verification command self-contained for the offline `prepare-data` probe, either by syncing all groups first or by documenting and enforcing a separate prerequisite command.
4. Add verifier checks that fail if `prepare_data/prepare_gesetze_im_internet.sh` still contains the retired venv/pip workflow in any reachable normal path.
5. Clarify that normal data-prep uv commands execute from `prepare_data/gesetze-tools` while using `--project "$ROOT_DIR"` for dependencies.
