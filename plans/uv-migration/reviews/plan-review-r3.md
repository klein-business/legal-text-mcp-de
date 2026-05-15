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

**Verdict**: Ready

The current plan is ready for execution. The revised artifacts now define the dependency groups, lock/sync gates, canonical `PYTHONPATH=mcp uv run ...` commands, fixture-backed HTTP readiness check, data-preparation dry-run validation, and Docker build/start criteria needed to execute the migration without changing runtime behavior. The remaining findings are minor execution-risk controls, not blockers.

## Requirement Coverage

| Requirement | Covered By | Gap? | Notes |
| ----------- | ---------- | ---- | ----- |
| Add repository-level `pyproject.toml` for Python 3.12 and current runtime/test/data-preparation dependencies. | Plan requirements; Phase 1 scope/deliverables | No | Runtime, `dev`, and `prepare-data` placement is explicit. |
| Use default runtime dependencies, a `dev` dependency group, and a `prepare-data` dependency group. | Plan requirements; Phase 1 scope/deliverables | No | Group names and intent are stated clearly enough for implementation. |
| Generate and commit `uv.lock` resolving all in-scope groups. | Plan requirements; Phase 1 deliverables/acceptance; DoD | No | `uv lock` and `uv sync --all-groups` are required. |
| Provide canonical uv command paths while preserving `PYTHONPATH=mcp`. | Plan requirements; Testing Strategy; Phase 1/2/3 acceptance | No | The command model is now consistent across plan and phase docs. |
| Update Docker build to install and run through uv-managed project environment. | Phase 2 scope/deliverables/acceptance | No | Docker strategy is explicitly deferred to the implementation plan and must be verified with a tagged build/run. |
| Update data-preparation helper to use uv instead of nested venv/pip. | Phase 2 scope/deliverables/acceptance | No | Syntax plus dry-run/no-network validation are required. |
| Add no-network or dry-run validation for data preparation. | Plan requirements; Phase 2 scope/acceptance | No | The plan requires the validation path to prove uv-managed dependency usage. |
| Update README and docs to uv commands. | Phase 3 scope/deliverables/acceptance | No | Active docs and README are covered by final stale-reference checks. |
| Remove or clearly retire obsolete requirements workflows. | Plan requirements; Phase 3 scope/acceptance | No | The accepted outcomes are remove, compatibility shim, or retired marker. |
| Preserve Python 3.12 behavior and current import model unless explicitly replaced. | Plan NFRs; Phase 1 notes; canonical commands | No | The plan keeps `PYTHONPATH=mcp` as the verified model. |
| Keep Docker behavior equivalent with `/data/legal-texts` and `STRICT_STARTUP=true`. | Plan NFRs; Phase 2 acceptance | No | The mount, env behavior, port, and startup smoke are specified. |

## Scope Clarity

### Findings

- No material scope gaps remain. The plan is clear that this is a dependency, command, Docker, helper-script, and documentation migration, not a package-layout or runtime-behavior refactor.
- **Minor**: Phase 1 says to preserve the source-run import model, but it does not explicitly tell the implementation plan to keep the uv project non-package/app-style or otherwise prevent accidental installation of the local `mcp/` directory as an importable project package. Because the runtime dependency is also named `mcp`, an accidental build-system/package-mode choice could reintroduce the external-package shadowing problem the plan is trying to avoid.

## Phase Structure Assessment

| Phase | Title | Verdict | Issue |
| ----- | ----- | ------- | ----- |
| 1 | uv Project Foundation | Sound | Minor package-mode risk should be pinned in the implementation plan. |
| 2 | Runtime, Scripts, and Docker | Sound | Docker smoke is objective, but an MCP protocol handshake would be a stronger container proof than port listening alone. |
| 3 | Documentation and Cleanup | Sound | Correctly waits for verified commands before rewriting docs and retiring requirements files. |

## Testing Strategy Assessment

### Test Coverage Gaps

- **Minor**: Docker verification requires the container to start and expose a listening port, but does not require an MCP client initialize/list-tools handshake against the container. Since MCP streamable HTTP is protocol-specific, a port check can miss a container image that starts but does not serve the expected MCP tool surface.

### Real-World Testing

Real-world testing is present. The plan includes direct fixture-backed MCP and HTTP startup checks, release verification, local network E2E, data-preparation dry-run/no-network validation, and a Docker build/run smoke test.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Minor | uv project mode | The plan does not explicitly require non-package/source-run uv project behavior, which matters because the repo has a local `mcp/` directory and depends on the external `mcp` package. | In the Phase 1 implementation plan, explicitly choose non-package/app-style uv configuration or add an acceptance check proving the external `mcp.server.fastmcp` import still resolves correctly under the selected project mode. |
| 2 | Minor | Docker smoke | The Docker smoke only requires a listening localhost port, not an MCP protocol check against the container. | Prefer a host-side MCP client initialize/list-tools smoke against the container, or explicitly document the port check as a minimal container startup smoke backed by the non-container E2E gate. |

## Recommendations

1. Proceed to implementation planning for Phase 1.
2. Pin the uv package/source-run decision before writing `pyproject.toml`.
3. Consider strengthening the Docker smoke to use a real MCP client handshake if it is practical within Phase 2.
