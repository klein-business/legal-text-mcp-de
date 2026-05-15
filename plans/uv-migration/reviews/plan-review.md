---
type: review
entity: plan-review
plan: "uv-migration"
status: final
reviewer: "general"
created: "2026-05-15"
---

# Plan Review: uv-migration

> Reviewing [uv-migration](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The plan identifies the right migration surfaces for a repository-wide move from venv/pip/requirements workflows to uv, and the phase order is broadly feasible. Revisions are needed before execution because two required paths are not concrete enough to verify: the canonical uv-backed runtime commands and the data-preparation helper migration. Without those details, an implementation could satisfy the broad checklist while leaving command drift or a broken helper workflow behind.

## Requirement Coverage

| Requirement | Covered By | Gap? | Notes |
| ----------- | ---------- | ---- | ----- |
| Add repository-level `pyproject.toml` for Python 3.12 and current runtime/test/data-preparation dependencies. | Phase 1 deliverables and acceptance criteria | Partial | Coverage exists, but dependency group names and default-vs-optional install behavior are still implicit. |
| Generate and commit `uv.lock` for all in-scope dependency groups. | Phase 1 deliverables; plan DoD | No | `uv lock` and `uv sync --all-groups` are explicit. |
| Provide `uv run` command paths for MCP server, HTTP API, release verification, and E2E verification. | Phase 2 deliverables; plan DoD for release/E2E | Yes | Release/E2E are explicit, but MCP and HTTP startup commands are not specified, and the import-path preservation model is deferred too far. |
| Update Docker build to install and run through uv-managed project environment. | Phase 2 scope and acceptance criteria | Partial | Docker migration is in scope, but the smoke-test criteria need a concrete startup/readiness check. |
| Update legacy data-preparation helper so dependencies are handled by uv. | Phase 2 scope and deliverables | Yes | The plan requires the edit but does not require a meaningful validation step for the updated helper. |
| Update README and project docs to supported uv setup/run/test/container commands. | Phase 3 scope and acceptance criteria | No | Active docs and README are covered by a stale-reference grep. |
| Remove or clearly retire obsolete requirements-file workflows. | Phase 3 scope and acceptance criteria | No | Final state choices are explicit. |
| Preserve Python 3.12 behavior and existing import model unless intentionally replaced. | Plan NFRs; Phase 1 notes | Partial | The risk is recognized, but canonical uv runtime commands are needed to make preservation objectively testable. |
| Keep each phase independently testable and runnable. | Plan NFRs; phase acceptance criteria | Partial | Phase 2 is not independently testable for the data-preparation helper. |
| Avoid broad unrelated runtime refactors. | Plan NFRs; phase excludes | No | Phase excludes are clear. |
| Keep Docker server behavior equivalent with `/data/legal-texts` and `STRICT_STARTUP=true`. | Plan NFRs; Phase 2 acceptance criteria | Partial | Environment values are covered, but expected container command/readiness proof is not precise. |
| Keep documentation consistent with verified commands. | Phase 3 scope and acceptance criteria | No | Phase 3 depends on Phase 2 command verification. |

## Scope Clarity

### Findings

- **Major**: The plan says uv-backed MCP and HTTP startup commands must exist, but does not define their expected form or where they should live. This matters because the current working model relies on `PYTHONPATH=mcp`, top-level imports like `http_api:create_http_app`, and explicit fallback logic in `mcp/server.py`.
- **Minor**: Dependency grouping is described by intent, but not by executable group names or install expectations. A maintainer cannot tell whether Docker should sync only default runtime dependencies, whether tests are in a `dev` group, or whether data preparation is a uv dependency group or an optional extra.
- **Note**: The optional Google ADK demo is reasonably out of core scope, but Phase 3 should explicitly document whether it remains unmanaged by uv or gets its own optional workflow. That keeps "full repository migration" from being interpreted inconsistently.

## Definition of Done Assessment

### Findings

- **Major**: The Definition of Done has no data-preparation validation even though the helper script migration is a functional requirement. A final `rg` check can prove old commands are gone, but it cannot prove the replacement command works.
- **Minor**: Docker completion says the image "starts" with a dataset, but does not define the observable proof: process still running, port listening, MCP endpoint reachable, or a specific health/readiness check. The release/E2E gates are much more concrete than the Docker gate.

## Phase Structure Assessment

| Phase | Title | Verdict | Issue |
| ----- | ----- | ------- | ----- |
| 1 | uv Project Foundation | Mostly sound | Good foundation phase, but should decide dependency group names and the exact import-path preservation mechanism before later phases depend on it. |
| 2 | Runtime, Scripts, and Docker | Needs revision | This phase carries the highest risk and needs exact MCP/HTTP uv commands plus a concrete validation path for the data-preparation helper and Docker runtime. |
| 3 | Documentation and Cleanup | Sound after Phase 2 revision | The cleanup phase is correctly last, but it depends on Phase 2 producing canonical commands rather than implementation notes alone. |

## Testing Strategy Assessment

### Test Coverage Gaps

- **Major**: No test or smoke step validates the migrated `prepare_data/prepare_gesetze_im_internet.sh` behavior under uv. At minimum, require `bash -n` plus a documented dry-run/smoke strategy, or explicitly waive the upstream clone/run with rationale and date.
- **Major**: No exact MCP/HTTP uv startup commands are named for verification. The E2E script currently spawns subprocesses through `sys.executable` and injects `PYTHONPATH`; the plan should state whether `uv run python scripts/verify_e2e.py` is sufficient proof or whether direct `uv run` server commands must also be tested.
- **Minor**: Docker testing should specify the image tag, mount path, port, and readiness assertion so the result is reproducible by a later reviewer.

### Real-World Testing

Real-world testing is present for the main server path: the plan requires `uv run python scripts/verify_e2e.py`, which starts real local HTTP and MCP server processes, and it requires a Docker build/start smoke test. Real-world testing is absent or underspecified for the data-preparation helper, which is the main uncovered workflow.

## Completeness Check

### Findings

- **Major**: Phase 2 delegates the "exact Docker install strategy" to a prerequisite but does not require that the selected strategy be reflected in acceptance criteria. That leaves open whether the project is installed, run from source, synced with all groups, or synced with runtime-only dependencies.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Runtime commands | Canonical uv-backed MCP and HTTP startup commands are not specified, despite being a functional requirement. | Add exact commands or pyproject scripts for MCP and HTTP startup, including how the current `PYTHONPATH=mcp` import model is preserved or replaced. |
| 2 | Major | Data preparation | The migrated data-preparation helper has no meaningful validation gate. | Add an acceptance criterion for `bash -n` and a uv-backed smoke/dry-run, or explicitly waive the upstream execution with rationale. |
| 3 | Major | Docker/runtime strategy | Phase 2 requires choosing a Docker install strategy but does not make the chosen strategy verifiable. | Require the implementation plan to record runtime-only vs all-group sync, package-install vs source-run behavior, and the exact Docker `CMD`/startup proof. |
| 4 | Minor | Dependency groups | Dependency group names and install expectations are implicit. | Define default runtime dependencies, test/dev group, and data-preparation group names before generating `uv.lock`. |
| 5 | Minor | Docker smoke test | Docker "starts successfully" is not an objective enough completion criterion. | Specify image tag, dataset mount, port mapping, and a concrete readiness or MCP endpoint assertion. |
| 6 | Note | Optional ADK demo | The plan excludes the Google ADK demo from core dependencies, but Phase 3 does not require documenting its unmanaged/optional status. | Add a documentation note so the uv migration boundary is explicit. |

## Recommendations

1. Revise Phase 2 to name the canonical uv commands for MCP and HTTP startup, not only release and E2E verification.
2. Add a data-preparation helper validation gate, even if the full upstream run is explicitly waived.
3. Make the Docker strategy and smoke test objective enough that another reviewer can reproduce the result.
4. Clarify dependency group names and sync expectations in Phase 1 before `uv.lock` is generated.
