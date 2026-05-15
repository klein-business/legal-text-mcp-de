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

**Verdict**: Ready

The Phase 2 implementation plan is concrete enough to execute without material guessing. It stays within the gated runtime/script/Docker scope, reflects the current codebase accurately, and resolves the prior review's execution-risk findings: pinned Docker uv acquisition, self-contained offline data-prep dry-run setup, canonical uv startup command proof, static stale venv/pip checks, and explicit upstream-helper cwd handling.

## Scope Alignment

### Findings

- No scope findings. The plan targets `Dockerfile`, `prepare_data/prepare_gesetze_im_internet.sh`, optional uv-compatible adjustments to existing verification scripts, and one focused Phase 2 verifier. It correctly defers README/docs cleanup and requirements-file retirement to Phase 3.

## Technical Feasibility

### Findings

- No technical feasibility findings. The Docker strategy is now exact: copy `/uv` and `/uvx` from pinned `ghcr.io/astral-sh/uv:0.10.12`, sync runtime dependencies only with `[tool.uv] package = false`, preserve `PYTHONPATH=/app/mcp`, and run `uv run --frozen --no-sync python mcp/server.py`.
- The data-prep plan is feasible against the current helper: dry-run avoids `git clone`, `lawde.py loadall`, and `lawdown.py convert`; normal mode runs from `prepare_data/gesetze-tools` while using `uv run --project "$ROOT_DIR"`.
- Local `uv 0.10.12` help confirms the plan's required flags exist, including `--all-groups`, `--group`, `--no-group`, `--no-dev`, `--frozen`, `--offline`, `--project`, `--no-sync`, and `--no-install-project`.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Confirm Phase 1 uv outputs before touching runtime files | Yes | Yes | None. |
| 2 | Migrate the Dockerfile to runtime-only uv sync | Yes | Yes | None. |
| 3 | Migrate the data-preparation helper to uv with dry-run validation | Yes | Yes | None. |
| 4 | Preserve release and E2E scripts unless uv execution proves a defect | Yes | Yes | None. |
| 5 | Add the focused Phase 2 verification script | Yes | Yes | None. |
| 6 | Keep Phase 3 cleanup out of this phase | Yes | Yes | None. |

## Required Context Assessment

### Missing Context

- None.

### Unnecessary Context

- None material.

## Testing Plan Assessment

### Test Integrity Check

The plan explicitly preserves existing `mcp/tests/` coverage, forbids disabling or weakening tests, keeps fixture data unchanged, and limits changes to `scripts/verify_release.py` and `scripts/verify_e2e.py` to uv-compatible subprocess invocation only if verification exposes a defect. This is adequate.

### Test Gaps

- None.

### Real-World Testing

Real-world integration testing is planned and appropriate: release and E2E gates under uv, direct MCP and HTTP startup through uv with fixture data, Docker image build, container startup with mounted fixture data, and host-side MCP initialize/list-tools smoke against `http://127.0.0.1:8001/mcp`.

## Reality Check Validation

### Findings

- No reality-check findings. The current `Dockerfile` still uses `pip install -r requirements.txt`; the current data-prep helper still creates/activates `venv` and runs `pip install -r`; `scripts/verify_release.py` and `scripts/verify_e2e.py` use `sys.executable`; `mcp/server.py` serves streamable HTTP; and `mcp/http_api.py` exposes `http_api:app`.
- The plan honestly records that `pyproject.toml` and `uv.lock` are absent in the current checkout and treats Phase 2 as blocked until Phase 1 outputs exist.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| - | - | - | No findings. | Proceed when Phase 1 outputs are present. |

## Recommendations

1. Proceed with Phase 2 execution after Phase 1 has produced `pyproject.toml`, `uv.lock`, and a passing `uv sync --all-groups`.
