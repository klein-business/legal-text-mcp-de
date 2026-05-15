---
type: review
entity: implementation-plan-review
plan: "uv-migration"
phase: 3
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 3 - Documentation and Cleanup

> Reviewing [Phase 3 Implementation Plan](../implementation/phase-3-impl.md)
> Against [Phase 3 Scope](../phases/phase-3.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The implementation plan is mostly aligned with Phase 3 scope and is concrete enough for the README/docs cleanup, ADK boundary documentation, and requirements-file removal decision. However, the final verification design has two material execution risks: it does not preserve the Phase 2 prerequisite that makes the offline prepare-data/Docker verifier self-contained, and the stale-reference scan can flag the very verification scripts that must contain retired workflow strings as test fixtures or pattern definitions.

## Scope Alignment

### Findings

- No material scope creep. The plan stays focused on active README/docs cleanup, requirements-file removal, release-gate stale-reference coverage, and preserving Phase 2 Docker/runtime behavior.
- The ADK boundary is aligned with the global plan: document `google-adk-agent/` as optional legacy demo code outside the core uv-managed runtime, without adding ADK dependencies to `pyproject.toml`.

## Technical Feasibility

### Findings

- **Major**: The proposed stale-reference check scans `scripts`, but Phase 2's `scripts/verify_uv_runtime_docker.py` is explicitly expected to contain retired workflow strings such as `python3 -m venv`, `pip install -r`, and `requirements.txt` so it can assert they are absent from `prepare_data/prepare_gesetze_im_internet.sh`. If Phase 3 adds the same stale-pattern literals to `scripts/verify_release.py`, that checker can also match itself. Without an explicit allowlist or non-self-matching pattern construction, the release gate can fail because of verifier implementation details rather than unsupported active workflow documentation.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Confirm Phase 1 and Phase 2 outputs before cleanup | Yes | Yes | None. |
| 2 | Update README to uv-first user workflows | Yes | Yes | None. |
| 3 | Update active docs to match final uv surfaces | Yes | Yes | None. |
| 4 | Remove obsolete requirements files | Yes | Yes | Safe only after Step 1 confirms Phase 2 no longer consumes them. |
| 5 | Extend release verification with stale active-workflow checks | Partly | Partly | Needs explicit handling for verifier self-matches and Phase 2 verifier literals. |
| 6 | Review stale-reference results and avoid runtime edits | Yes | Yes | None. |

## Required Context Assessment

### Missing Context

- None material. The plan lists the active docs, README, Phase 1/2 implementation plans, Dockerfile, data-prep helper, release verifier, and E2E verifier needed to execute Phase 3.

### Unnecessary Context

- None material.

## Testing Plan Assessment

### Test Integrity Check

The plan preserves existing tests, keeps `scripts/verify_release.py` additive rather than substitutive, keeps `scripts/verify_e2e.py` behavior intact, and explicitly forbids weakening tests to accept stale venv/pip/requirements workflows. That is adequate.

### Test Gaps

- **Major**: The primary verification command is `PYTHONPATH=mcp uv run python scripts/verify_release.py && PYTHONPATH=mcp uv run --group dev python scripts/verify_uv_runtime_docker.py`, but it omits the Phase 3 acceptance criterion `uv sync --all-groups` and also drops the Phase 2 verifier's required prelude `uv sync --all-groups`. That prelude matters because Phase 2's dry-run/no-network path is designed to use `uv run --frozen --offline --group prepare-data`; on a clean checkout, the offline prepare-data probe may fail if all groups were not synced first.

### Real-World Testing

Real-world integration testing is planned: the release gate runs tests plus local HTTP/MCP E2E, and the Phase 2 verifier is expected to recheck data-preparation dry-run, direct uv MCP/HTTP startup, Docker build, container startup, and MCP initialize/list-tools against the container. The missing `uv sync --all-groups` prelude prevents this from being a reliable clean-checkout gate.

## Reality Check Validation

### Findings

- The plan accurately records current pre-Phase-1/2 reality: `Dockerfile` still installs `requirements.txt`, the data-prep helper still creates and activates `venv`, active docs still document pip/direct Python commands, and `mcp/requirements.txt` plus `prepare_data/requirements.txt` still exist. It correctly blocks Phase 3 execution until Phase 1 and Phase 2 outputs are present.
- Requirements-file removal is materially safe if Step 1 is enforced: current active consumers are Docker, data-prep helper, README/docs, and stale references; Phase 2 is supposed to remove the Docker/helper consumers before Phase 3 deletes the files.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Testing Plan | Final verification omits `uv sync --all-groups`, which is both a Phase 3 acceptance criterion and the Phase 2 precondition for the offline prepare-data verifier. | Change the primary verification command to start with `uv sync --all-groups && ...`, preserving the release gate and Phase 2 runtime/Docker verifier afterward. |
| 2 | Major | Technical Feasibility | The stale-reference scan can self-match or match Phase 2 verifier pattern literals when scanning `scripts`. | Specify an allowlist for verifier files/lines or require non-self-matching pattern construction, while still scanning active user-facing scripts and maintained workflow text. |

## Recommendations

1. Revise the primary verification command to include `uv sync --all-groups` before `PYTHONPATH=mcp uv run python scripts/verify_release.py && PYTHONPATH=mcp uv run --group dev python scripts/verify_uv_runtime_docker.py`.
2. Revise Step 5 to define how stale-reference scanning avoids false positives in `scripts/verify_release.py` and `scripts/verify_uv_runtime_docker.py` without allowing unsupported active workflow instructions back into README, docs, Dockerfile, `mcp`, or `prepare_data`.
