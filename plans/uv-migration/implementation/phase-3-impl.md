---
type: planning
entity: implementation-plan
plan: "uv-migration"
phase: 3
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 3 - Documentation and Cleanup

> Implements [Phase 3](../phases/phase-3.md) of [uv-migration](../plan.md)

## Approach

Make the Phase 1 and Phase 2 uv workflows the only documented and maintained dependency/runtime path. This phase updates active README/docs references from venv/pip/direct Python commands to the canonical source-run uv commands, documents the Google ADK agent as an optional legacy demo outside the core uv-managed runtime, removes obsolete requirements files after Phase 2 has moved Docker and data-preparation off them, and extends release verification so stale active-workflow references are caught by the final release gate.

Preserve the prior implementation-plan decisions: the project remains `[tool.uv] package = false`, host execution keeps `PYTHONPATH=mcp`, Docker runs the MCP server from copied source using the uv-managed runtime environment, and the legacy data-preparation helper is validated through its uv `prepare-data` dry-run/no-network path. Do not change runtime behavior, legal text data, MCP tools, HTTP routes, source import semantics, Docker startup behavior, or E2E coverage in this phase.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | modify | Update active setup/run/test documentation to uv commands and extend release verification to reject stale venv/pip/requirements active-workflow references. |
| [container-runtime](../../../docs/modules/container-runtime.md) | modify | Update Docker documentation to describe the Phase 2 uv-managed image and external normalized dataset mount. |
| [data-preparation](../../../docs/modules/data-preparation.md) | modify | Update legacy helper documentation to describe uv `prepare-data` group execution and dry-run/no-network validation instead of nested venv/pip setup. |
| [google-adk-agent](../../../docs/modules/google-adk-agent.md) | modify | Explicitly document that `google-adk-agent/` remains an optional legacy demo outside the core uv-managed runtime and release gate. |

## Required Context

| File | Why |
|------|-----|
| `plans/uv-migration/plan.md` | Defines the global uv migration requirements, canonical `PYTHONPATH=mcp uv run ...` commands, Docker smoke criteria, and final documentation cleanup acceptance criteria. |
| `plans/uv-migration/phases/phase-3.md` | Gated Phase 3 scope, deliverables, acceptance criteria, and explicit exclusions. |
| `plans/uv-migration/implementation/phase-1-impl.md` | Pins `[tool.uv] package = false`, source-run app style, dependency groups, and the decision not to retire requirements files until Phase 3. |
| `plans/uv-migration/implementation/phase-2-impl.md` | Defines the final Docker command surface, data-preparation uv dry-run/no-network behavior, and focused runtime/Docker verification handoff. |
| `plans/uv-migration/todo.md` | Shows phase sequencing; Phase 3 implementation must wait until Phase 1 and Phase 2 are complete even if this implementation plan is authored earlier. |
| `README.md` | Primary user-facing setup, MCP/HTTP run, Docker, release, and E2E command documentation that must become uv-first. |
| `docs/overview.md` | Active project overview with setup/run/test commands that currently mirror README and must use uv. |
| `docs/modules/mcp-server.md` | Active module inventory and release-gate section that must describe `PYTHONPATH=mcp uv run python scripts/verify_release.py`. |
| `docs/modules/container-runtime.md` | Active Docker module documentation that must stop describing requirements-file installation after Phase 2. |
| `docs/modules/data-preparation.md` | Active legacy helper documentation that must stop describing `python3 -m venv` and `pip` as the maintained dependency path. |
| `docs/modules/google-adk-agent.md` | Active module documentation for the optional ADK demo; must state it is outside the core uv-managed runtime. |
| `docs/features/google-adk-agent-demo.md` | Active feature documentation for the optional ADK demo; must align with the same uv scope boundary. |
| `docs/features/*.md` | Feature docs inventory to scan for setup, packaging, runtime, verification, or ADK scope references that need uv cleanup. |
| `mcp/requirements.txt` | Obsolete Phase 1 dependency source to remove after `pyproject.toml` and `uv.lock` are authoritative. |
| `prepare_data/requirements.txt` | Obsolete legacy helper dependency source to remove after the Phase 2 helper uses the uv `prepare-data` group. |
| `Dockerfile` | Phase 2 output that should already use uv and must not be reverted to requirements-file installation during docs cleanup. |
| `prepare_data/prepare_gesetze_im_internet.sh` | Phase 2 output that should already use uv `--group prepare-data` and dry-run/no-network validation; stale venv/pip text must be absent. |
| `scripts/verify_release.py` | Final release gate to extend with active-doc stale-reference checks while preserving `TESTS`, `check_docs_links`, and the E2E subprocess call. |
| `scripts/verify_e2e.py` | E2E verifier that should remain behaviorally unchanged; release verification must continue to invoke it through the uv interpreter. |

## Implementation Steps

### Step 1: Confirm Phase 1 and Phase 2 outputs before cleanup

- **What**: Verify the repository has the Phase 1/2 uv surfaces before editing docs or removing compatibility files: `pyproject.toml` with `[tool.uv] package = false`, `uv.lock`, Phase 2 uv-managed `Dockerfile`, Phase 2 uv-managed `prepare_data/prepare_gesetze_im_internet.sh`, and Phase 2 verification script behavior.
- **Where**: `pyproject.toml`, `uv.lock`, `Dockerfile`, `prepare_data/prepare_gesetze_im_internet.sh`, `scripts/verify_uv_runtime_docker.py`, `plans/uv-migration/implementation/phase-1-impl.md`, `plans/uv-migration/implementation/phase-2-impl.md`.
- **Why**: Phase 3 must document and clean up the final command surfaces, not invent alternate uv commands or remove files that Phase 2 still needs.
- **Considerations**: If Phase 1/2 outputs are missing or still use requirements-file workflows, stop and complete those phases first. Do not change the pinned source-run model, Docker runtime dependency scope, or data-preparation dry-run design in this phase.

### Step 2: Update README to uv-first user workflows

- **What**: Replace active installation, MCP startup, HTTP startup, Docker, release, and E2E instructions with uv-first commands that match the plan and Phase 2 implementation decisions.
- **Where**: `README.md` sections `Installation`, `Run MCP`, `Run HTTP API`, `Docker`, and `Tests`.
- **Why**: README is the primary user workflow surface and Phase 3 requires a single maintained dependency workflow.
- **Considerations**: Use `uv sync --all-groups` for setup. Preserve host-side `PYTHONPATH=mcp` in the documented MCP, HTTP, release, and E2E commands. Document MCP startup as `DATASET_PATH=mcp/tests/fixtures/normalized STRICT_STARTUP=true PYTHONPATH=mcp uv run python mcp/server.py`, HTTP startup as `DATASET_PATH=mcp/tests/fixtures/normalized STRICT_STARTUP=true PYTHONPATH=mcp uv run uvicorn http_api:app --host 127.0.0.1 --port 8080`, release verification as `PYTHONPATH=mcp uv run python scripts/verify_release.py`, and E2E verification as `PYTHONPATH=mcp uv run python scripts/verify_e2e.py`. Keep Docker docs aligned with the Phase 2 uv-managed image and `/data/legal-texts` external dataset mount.

### Step 3: Update active docs to match final uv surfaces

- **What**: Rewrite active docs that describe dependency setup, runtime commands, Docker dependency installation, data-preparation dependencies, release verification, or ADK scope.
- **Where**: `docs/overview.md`, `docs/modules/mcp-server.md`, `docs/modules/container-runtime.md`, `docs/modules/data-preparation.md`, `docs/modules/google-adk-agent.md`, `docs/features/google-adk-agent-demo.md`, and any matching files under `docs/features/*.md`.
- **Why**: Active documentation must not keep parallel venv/pip/requirements instructions after uv is the maintained workflow.
- **Considerations**: Do not edit `docs-legacy/` unless a later primary decision explicitly requests archival notes. In `docs/modules/google-adk-agent.md` and `docs/features/google-adk-agent-demo.md`, state that `google-adk-agent/` is optional legacy demo code outside the core uv-managed runtime and outside release verification; do not add Google ADK dependencies to `pyproject.toml` in Phase 3.

### Step 4: Remove obsolete requirements files

- **What**: Delete `mcp/requirements.txt` and `prepare_data/requirements.txt` after confirming no maintained runtime, Docker, data-preparation, docs, or verification path still consumes them.
- **Where**: `mcp/requirements.txt`, `prepare_data/requirements.txt`, `pyproject.toml`, `uv.lock`, `Dockerfile`, `prepare_data/prepare_gesetze_im_internet.sh`.
- **Why**: Phase 1 moved dependency intent into `pyproject.toml` and `uv.lock`; Phase 2 moved Docker and the legacy helper off requirements files. Removing the obsolete files avoids reintroducing split dependency sources.
- **Considerations**: This is the chosen requirements-file compatibility decision for Phase 3: remove, not shim. If a stale command still needs either file, fix that command to use uv rather than keeping a compatibility path. Do not remove or weaken dependency entries from `pyproject.toml` or `uv.lock`.

### Step 5: Extend release verification with stale active-workflow checks

- **What**: Add a stale-reference check to the release gate so the final verification fails if active docs or maintained scripts reintroduce unsupported venv/pip/requirements workflows.
- **Where**: `scripts/verify_release.py`, near `check_docs_links`, with a small helper such as `check_no_stale_workflow_refs`.
- **Why**: Phase 3 acceptance includes stale-reference cleanup, and the single final verify command should exercise both release behavior and documentation/cleanup behavior.
- **Considerations**: Keep `TESTS`, `cmd = [sys.executable, "-m", "pytest", *TESTS]`, and `e2e_cmd = [sys.executable, "scripts/verify_e2e.py"]` behavior intact. Scope the stale scan to active paths from the Phase 3 acceptance criteria: `README.md`, `docs`, `scripts`, `mcp`, `prepare_data`, and `Dockerfile`. Exclude `docs-legacy/` by not scanning it. Avoid verifier self-matches by either excluding `scripts/verify_release.py` and `scripts/verify_uv_runtime_docker.py` from the generic text scan or by using non-self-matching pattern construction; those verifier files may contain retired workflow strings only as pattern literals or assertions, not as user-facing active workflow instructions. Still scan all other maintained scripts and active docs for unsupported patterns equivalent to `python3 -m venv`, `pip install -r`, `requirements\\.txt`, `source .venv/bin/activate`, `source venv/bin/activate`, and direct maintained `PYTHONPATH=mcp python` command examples.

### Step 6: Review stale-reference results and avoid runtime edits

- **What**: Reconcile every stale active-workflow hit found by the release gate by updating active docs or cleanup references, then leave runtime code unchanged.
- **Where**: `README.md`, `docs/**`, `scripts/verify_release.py`, `Dockerfile`, `prepare_data/prepare_gesetze_im_internet.sh`, `mcp/`, `prepare_data/`.
- **Why**: The phase objective is documentation and cleanup, with final verification, not runtime refactoring.
- **Considerations**: Feature docs unrelated to setup, packaging, runtime, verification, or ADK scope should remain untouched. `scripts/verify_e2e.py` should remain unchanged unless a stale comment or command string directly conflicts with the uv workflow; its network behavior and assertions must not be narrowed.

## Testing Plan

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Primary verification | Run `uv sync --all-groups && PYTHONPATH=mcp uv run python scripts/verify_release.py && PYTHONPATH=mcp uv run --group dev python scripts/verify_uv_runtime_docker.py` from the repository root after docs cleanup and requirements-file removal. | All dependency groups sync from the final metadata, the release gate passes through uv, rejects stale active-workflow references without self-matching verifier pattern literals, runs the existing test matrix, invokes local HTTP/MCP E2E through `scripts/verify_e2e.py`, and confirms the Phase 2 runtime/Docker/data-preparation checks still pass after cleanup. |

### Test Integrity Constraints

- Existing tests under `mcp/tests/` must not be disabled, deleted, renamed, skipped, or weakened to make docs cleanup pass.
- `scripts/verify_release.py` must continue to run `check_docs_links`, every path in `TESTS`, and `scripts/verify_e2e.py`; the stale-reference check is additive coverage, not a replacement for tests or E2E.
- `scripts/verify_e2e.py` network behavior, fixture dataset usage, MCP initialize/list-tools assertions, and HTTP `/ready` assertions must remain unchanged unless Phase 2 already required a uv-compatible subprocess fix.
- `mcp/tests/test_release_gate.py` must remain an active scope guard; do not loosen production-file exclusions or expected path checks to accommodate docs cleanup.
- Fixture data under `mcp/tests/fixtures/normalized/` must remain unchanged.
- No test should be updated to accept active `pip install -r`, requirements-file, venv activation, or direct maintained `PYTHONPATH=mcp python` workflow instructions.

## Rollback Strategy

Restore `mcp/requirements.txt` and `prepare_data/requirements.txt` from the previous commit only if a Phase 2 command still depends on them, then revert the stale-reference check in `scripts/verify_release.py` while keeping Phase 1/2 uv runtime changes intact. Revert README/docs command edits to the last known Phase 2-compatible documentation only as a temporary rollback; the target state remains uv-first documentation with no maintained requirements-file workflow.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Requirements-file final state | Keep as compatibility shims; mark as retired docs; remove | Remove `mcp/requirements.txt` and `prepare_data/requirements.txt` | Phase 1 moved dependency intent into `pyproject.toml`/`uv.lock`, Phase 2 removes consumers, and deletion prevents split dependency sources. |
| Final verification command | Separate grep plus release gate; Phase 2 Docker script; all-groups sync followed by release gate and Phase 2 runtime/Docker script | `uv sync --all-groups && PYTHONPATH=mcp uv run python scripts/verify_release.py && PYTHONPATH=mcp uv run --group dev python scripts/verify_uv_runtime_docker.py` | One primary shell command verifies final dependency sync, exercises docs cleanup, test coverage, E2E release behavior, and verifies the Phase 2 Docker/runtime/data-preparation surfaces still pass after cleanup. |
| Google ADK dependency handling | Add to core uv groups; add optional uv extra; document as legacy outside core | Document as optional legacy outside core uv-managed runtime | The plan explicitly keeps ADK outside core dependencies unless a future task adds explicit ADK dependency management. |
| Archived docs cleanup | Rewrite `docs-legacy/`; add archival note; leave untouched | Leave untouched | Phase 3 excludes archived documentation unless a later implementation plan explicitly decides otherwise. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `README.md` | `Installation`, `Run MCP`, `Run HTTP API`, `Tests` | Current active user docs contain `python3.12 -m venv`, `pip install -r mcp/requirements.txt`, direct `python mcp/server.py`, and `PYTHONPATH=mcp python scripts/...` examples that Phase 3 must replace. |
| `docs/overview.md` | `Development` section | Mirrors README setup/run/test commands and currently contains venv, pip, direct server, and direct release/E2E commands. |
| `docs/modules/mcp-server.md` | `Test Coverage` | Documents the release gate as `PYTHONPATH=mcp python scripts/verify_release.py`; must become the canonical uv command. |
| `docs/modules/container-runtime.md` | `Dependencies` and `Key Symbols` | Currently describes `mcp/requirements.txt` and `RUN pip install --no-cache-dir -r requirements.txt`; after Phase 2 it must describe uv-managed runtime dependencies. |
| `docs/modules/data-preparation.md` | `Dependencies` and `Structure` | Currently documents `python3 -m venv`, `pip`, and `prepare_data/requirements.txt`; after Phase 2 it must describe uv `prepare-data` group execution and dry-run validation. |
| `docs/modules/google-adk-agent.md` | `Overview`, `Dependencies`, `Inventory Notes` | Already identifies the module as optional legacy demo code, but does not explicitly tie it to the core uv-managed runtime boundary. |
| `docs/features/google-adk-agent-demo.md` | `Summary` and `Edge Cases & Limitations` | Already says the demo is not release-gated; must align with the explicit Phase 3 ADK uv-scope note. |
| `mcp/requirements.txt` | Runtime dependency list | Historical dependency source that Phase 1 moved into default `pyproject.toml` dependencies and Phase 3 removes. |
| `prepare_data/requirements.txt` | Legacy helper dependency list | Historical dependency source that Phase 1 moved into the `prepare-data` group and Phase 3 removes. |
| `Dockerfile` | `RUN pip install --no-cache-dir -r requirements.txt` and `CMD ["python", "server.py"]` in the current checkout | Shows the pre-Phase 2 Docker state; Phase 3 must only run after this has been replaced by the Phase 2 uv-managed image. |
| `prepare_data/prepare_gesetze_im_internet.sh` | `python3 -m venv venv`, `source venv/bin/activate`, `pip install -r ../requirements.txt` in the current checkout | Shows the pre-Phase 2 helper state; Phase 3 must only run after this has been replaced by uv `prepare-data` execution. |
| `scripts/verify_release.py` | `check_docs_links` | Existing docs-oriented release gate hook where the stale active-workflow check should be added. |
| `scripts/verify_release.py` | `TESTS`, `cmd = [sys.executable, "-m", "pytest", *TESTS]`, `e2e_cmd = [sys.executable, "scripts/verify_e2e.py"]` | Confirms release verification can be extended without replacing pytest or E2E coverage. |
| `scripts/verify_e2e.py` | `env_for_server`, `run_http_e2e`, `run_mcp_e2e` | Confirms E2E already sets `PYTHONPATH`, uses the fixture dataset, validates `/ready`, and performs MCP initialize/list-tools checks that Phase 3 must preserve. |

### Mismatches / Notes

- The current checkout still shows pre-Phase 1/2 state in `Dockerfile`, `prepare_data/prepare_gesetze_im_internet.sh`, `mcp/requirements.txt`, and `prepare_data/requirements.txt`; this Phase 3 plan assumes Phase 1 and Phase 2 are implemented before execution.
- `plans/uv-migration/todo.md` still lists Phase 1 as the active phase. That is consistent with authoring Phase 3 ahead of execution, but Phase 3 implementation should not begin until the primary advances the plan state and verifies Phase 1/2 completion.
- Current active docs do not yet mention `uv`; that is expected drift before Phase 3 and is the main cleanup target.
- `google-adk-agent/` is already documented as optional legacy demo code, but the docs need a sharper statement that its dependencies are not part of the core uv-managed runtime or final release gate.
