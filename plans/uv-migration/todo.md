---
type: planning
entity: todo
plan: "uv-migration"
updated: "2026-05-15"
---

# Todo: uv-migration

> Tracking [uv-migration](plan.md)

## Plan Completed

### Phase Context

- **Scope**: [Phase 3](phases/phase-3.md)
- **Implementation**: [Phase 3 Plan](implementation/phase-3-impl.md)
- **Latest Handover**: None yet
- **Relevant Docs**:
  - [Project overview](../../docs/overview.md)
  - [MCP/server module](../../docs/modules/mcp-server.md)
  - [Container runtime](../../docs/modules/container-runtime.md)
  - [Data preparation](../../docs/modules/data-preparation.md)

### Pending

### In Progress

### Completed

- [x] Inventory runtime, test, release, and data-preparation dependencies. <!-- completed: 2026-05-15 -->
- [x] Add repository-level `pyproject.toml`. <!-- completed: 2026-05-15 -->
- [x] Generate `uv.lock`. <!-- completed: 2026-05-15 -->
- [x] Run `uv sync --all-groups`. <!-- completed: 2026-05-15 -->
- [x] Run `PYTHONPATH=mcp uv run pytest mcp/tests`. <!-- completed: 2026-05-15 -->
- [x] Preserve and document canonical `PYTHONPATH=mcp` uv command behavior for Phase 2. <!-- completed: 2026-05-15 -->
- [x] Pin non-package/source-run uv project mode and verify external MCP SDK resolution. <!-- completed: 2026-05-15 -->
- [x] Update `Dockerfile` to use pinned uv binary and runtime-only uv sync. <!-- completed: 2026-05-15 -->
- [x] Update `prepare_data/prepare_gesetze_im_internet.sh` to use uv `prepare-data` group and dry-run/no-network validation. <!-- completed: 2026-05-15 -->
- [x] Add `scripts/verify_uv_runtime_docker.py`. <!-- completed: 2026-05-15 -->
- [x] Run `uv sync --all-groups && PYTHONPATH=mcp uv run --group dev python scripts/verify_uv_runtime_docker.py`. <!-- completed: 2026-05-15 -->
- [x] Review Phase 1 and Phase 2 implementations until zero findings remain. <!-- completed: 2026-05-15 -->
- [x] Update README to uv-first setup, run, Docker, release, and E2E commands. <!-- completed: 2026-05-15 -->
- [x] Update active docs under `docs/` to uv-first commands and ADK boundary. <!-- completed: 2026-05-15 -->
- [x] Remove obsolete `mcp/requirements.txt` and `prepare_data/requirements.txt`. <!-- completed: 2026-05-15 -->
- [x] Extend `scripts/verify_release.py` with stale active-workflow checks. <!-- completed: 2026-05-15 -->
- [x] Run `uv sync --all-groups && PYTHONPATH=mcp uv run python scripts/verify_release.py && PYTHONPATH=mcp uv run --group dev python scripts/verify_uv_runtime_docker.py`. <!-- completed: 2026-05-15 -->
- [x] Review Phase 3 implementation until zero findings remain. <!-- completed: 2026-05-15 -->
- [x] Review initial plan and incorporate Major findings into plan scope and acceptance criteria. <!-- completed: 2026-05-15 -->
- [x] Re-review plan until zero findings remain. <!-- completed: 2026-05-15 -->
- [x] Author implementation plans for Phases 1, 2, and 3. <!-- completed: 2026-05-15 -->
- [x] Review implementation plans until zero findings remain for all phases. <!-- completed: 2026-05-15 -->

### Blocked

## Changelog

### 2026-05-15

- Plan completed after all phases passed implementation review with zero findings and final verification succeeded.
- Phase 2 completed: verified data-preparation dry-run/no-network, direct uv MCP/HTTP startup, release/E2E, Docker build/run, and container MCP initialize/list-tools; Phase 3 started.
- Phase 1 completed: created `pyproject.toml` and `uv.lock`, verified all groups sync, external FastMCP SDK resolution, and `52 passed` under `PYTHONPATH=mcp uv run pytest mcp/tests`; Phase 2 started.
- Phase 1 execution exposed that `mcp[cli]==1.10` crashes during current FastMCP tool registration; revised Phase 1 implementation plan to use `mcp[cli]==1.14.1` and assert external SDK resolution by package path/module prefix.
- Implementation-plan gate passed for all phases: Phase 1, Phase 2, and Phase 3 reviews report Ready with zero findings after revision loops.
- Plan review gate passed: `plans/uv-migration/reviews/plan-review-r4.md` reports Ready with zero findings.
- Updated plan after third plan review: added `[tool.uv] package = false` expectation and strengthened Docker validation to an MCP client initialize/list-tools smoke check.
- Updated plan after second plan review: normalized test/release commands to `PYTHONPATH=mcp uv run ...` and changed HTTP smoke criteria from `/health` to `/ready` or fixture-backed endpoint.
- Updated plan after first plan review: clarified dependency groups, canonical uv commands, data-preparation dry-run validation, Docker smoke evidence, and Google ADK scope boundary.
- Plan created with three phases for uv migration.
