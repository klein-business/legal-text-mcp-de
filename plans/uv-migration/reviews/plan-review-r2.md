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

The revised plan is substantially more executable than the prior version: it now names dependency groups, canonical uv runtime commands, Docker smoke criteria, and a dry-run path for the data-preparation helper. One material inconsistency remains before execution: several phase gates still use bare `uv run` commands even though the repository's current tests and scripts rely on `PYTHONPATH=mcp`; following those gates literally can either fail Phase 1/3 or push implementers into an unplanned package-layout change. There is also a smaller HTTP smoke-test gap where the direct command only has to serve `/health`, which does not prove the fixture dataset was loaded.

## Requirement Coverage

| Requirement | Covered By | Gap? | Notes |
| ----------- | ---------- | ---- | ----- |
| Add repository-level `pyproject.toml` for Python 3.12 and current runtime/test/data-preparation dependencies. | Phase 1 deliverables and acceptance criteria | No | Dependency placement and group names are explicit enough for planning. |
| Use default runtime dependencies, `dev`, and `prepare-data` dependency groups. | Plan requirements; Phase 1 scope/deliverables | No | The revised plan names the groups. |
| Generate and commit `uv.lock` for all in-scope groups. | Phase 1 deliverables; plan DoD/testing | No | `uv lock` and `uv sync --all-groups` are explicit. |
| Provide canonical uv command paths while preserving `PYTHONPATH=mcp`. | Plan requirements; Phase 2 scope/acceptance | Partial | Runtime, release, and E2E commands include `PYTHONPATH=mcp`, but Phase 1 and Phase 3 still require bare commands that conflict with this model. |
| Update Docker build to install and run through uv-managed environment. | Phase 2 scope/deliverables/acceptance | No | Docker install strategy is required in the implementation plan and runtime verification is concrete. |
| Update data-preparation helper to use uv instead of nested venv/pip. | Phase 2 scope/deliverables/acceptance | No | Dry-run/no-network validation is now required. |
| Update README and active docs to uv commands. | Phase 3 scope/acceptance | No | Active docs cleanup is explicitly scoped. |
| Remove or clearly retire obsolete requirements-file workflows. | Phase 3 scope/acceptance | No | The final state options are explicit. |
| Preserve Python 3.12 behavior and current import model unless intentionally replaced. | Plan NFRs; Phase 1 notes; Phase 2 commands | Partial | The bare test/release commands are inconsistent with the stated import model. |
| Keep phases independently testable and runnable. | Plan NFRs; phase acceptance criteria | Partial | Phase 1's stated test command is likely not runnable as written under the current import layout. |
| Avoid broad unrelated runtime refactors. | Plan NFRs; phase excludes | No | Scope boundaries are clear. |
| Keep Docker behavior equivalent with `/data/legal-texts` and `STRICT_STARTUP=true`. | Plan NFRs; Phase 2 acceptance | No | Docker smoke criteria are objective enough for the plan stage. |
| Keep documentation consistent with verified commands. | Phase 3 scope/acceptance | Partial | Phase 3 verification commands omit `PYTHONPATH=mcp`, unlike the canonical commands in the main plan. |

## Scope Clarity

### Findings

- **Major**: The plan says the migration preserves the current `PYTHONPATH=mcp` import model, but Phase 1 expects `uv run pytest mcp/tests`, the overall testing strategy repeats that command, and Phase 3 expects bare `uv run python scripts/verify_release.py` and `uv run python scripts/verify_e2e.py`. Current tests import top-level modules such as `legal_texts`, `http_api`, and `server`, and `python -c "import legal_texts"` fails from the repository root unless `PYTHONPATH=mcp` is set. The plan should either make every verification command consistently use `PYTHONPATH=mcp` or explicitly add a scoped packaging change that makes the bare commands valid.

## Definition of Done Assessment

### Findings

- **Major**: The Definition of Done and Phase 3 acceptance criteria disagree on the final release/E2E commands. The main DoD requires `PYTHONPATH=mcp uv run python scripts/verify_release.py` and `PYTHONPATH=mcp uv run python scripts/verify_e2e.py`, while Phase 3 drops `PYTHONPATH=mcp`. This creates an ambiguous final gate and can invalidate the "documentation matches verified commands" requirement.

## Phase Structure Assessment

| Phase | Title | Verdict | Issue |
| ----- | ----- | ------- | ----- |
| 1 | uv Project Foundation | Needs revision | The phase's expected test command omits `PYTHONPATH=mcp`, despite the phase explicitly preserving that import model. |
| 2 | Runtime, Scripts, and Docker | Mostly sound | Runtime commands, Docker strategy, and data-preparation validation are now concrete; the HTTP direct smoke should prove readiness, not only `/health`. |
| 3 | Documentation and Cleanup | Needs revision | Final verification commands do not match the canonical command set from the main plan. |

## Testing Strategy Assessment

### Test Coverage Gaps

- **Major**: Unit/integration and final release gates are not consistently specified with the import path they need. The repository currently has no root package layout that makes bare `uv run pytest mcp/tests` or bare `uv run python scripts/verify_release.py` obviously valid.
- **Minor**: Phase 2's direct HTTP startup acceptance only requires `/health`. In this codebase `/health` is independent of dataset readiness, so that check can pass even when the fixture dataset path or strict startup semantics are wrong. The direct HTTP smoke should hit `/ready` or one fixture-backed endpoint, while `/health` can remain a basic liveness check.

### Real-World Testing

Real-world testing is present. The plan requires local network E2E through `scripts/verify_e2e.py`, direct MCP/HTTP startup smoke tests, Docker build/run smoke testing, and a no-network validation mode for the data-preparation helper. The main remaining limitation is command consistency, not absence of integration coverage.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Command model | Several acceptance gates omit `PYTHONPATH=mcp` even though the plan says to preserve that import model and current tests/scripts import top-level modules from `mcp/`. | Change Phase 1, Testing Strategy, and Phase 3 gates to use `PYTHONPATH=mcp uv run ...`, or explicitly scope and test a packaging change that makes bare commands valid. |
| 2 | Minor | HTTP smoke test | The direct HTTP smoke only needs `/health`, which does not prove fixture dataset loading or readiness. | Require `/ready` or a fixture-backed endpoint for the direct HTTP uv command smoke test. |

## Recommendations

1. Normalize every planned verification command around the selected import model before implementation starts.
2. If the goal is to remove `PYTHONPATH=mcp`, add that as an explicit Phase 1 packaging deliverable with acceptance tests; otherwise keep `PYTHONPATH=mcp` in the test, release, E2E, and documentation gates.
3. Strengthen the direct HTTP smoke criterion from `/health` to `/ready` or another fixture-backed endpoint.
