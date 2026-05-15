#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
MEGALINTER_CONFIG = ROOT / ".mega-linter.yml"

CHECKOUT_REF = "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd"
SETUP_UV_REF = "astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b"
MEGALINTER_REF = "oxsecurity/megalinter/flavors/python@8fbdead70d1409964ab3d5afa885e18ee85388bb"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AssertionError(f"Missing required file: {path.relative_to(ROOT)}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path.relative_to(ROOT)} must contain a YAML mapping")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def steps(job: dict[str, Any], job_name: str) -> list[dict[str, Any]]:
    value = job.get("steps")
    require(isinstance(value, list), f"{job_name} must define a steps list")
    for step in value:
        require(isinstance(step, dict), f"{job_name} contains a non-mapping step")
    return value


def step_uses(job_steps: list[dict[str, Any]], ref: str) -> bool:
    return any(step.get("uses") == ref for step in job_steps)


def step_runs(job_steps: list[dict[str, Any]], expected: str) -> bool:
    return any(expected in str(step.get("run", "")) for step in job_steps)


def verify_ci_workflow() -> None:
    workflow = load_yaml(WORKFLOW)

    require(workflow.get("name") == "CI", "workflow name must be CI")
    require(workflow.get("permissions") == {"contents": "read"}, "workflow permissions must be contents: read")

    triggers = workflow.get(True) or workflow.get("on")
    require(isinstance(triggers, dict), "workflow must define on: mapping")
    require("pull_request" in triggers, "workflow must run on pull_request")
    require(triggers.get("push", {}).get("branches") == ["main"], "workflow push trigger must be limited to main")

    jobs = workflow.get("jobs")
    require(isinstance(jobs, dict), "workflow must define jobs")
    require(set(jobs) == {"tests", "megalinter"}, "workflow must contain exactly tests and megalinter jobs")

    test_job = jobs["tests"]
    require(test_job.get("runs-on") == "ubuntu-latest", "tests job must run on ubuntu-latest")
    require(
        test_job.get("env", {}).get("SKIP_LIVE_SOURCE_MATRIX") == "true",
        "tests job must skip external live source probes",
    )
    test_steps = steps(test_job, "tests")
    require(step_uses(test_steps, CHECKOUT_REF), "tests job must pin actions/checkout v6 by SHA")
    require(step_uses(test_steps, SETUP_UV_REF), "tests job must pin astral-sh/setup-uv v8.1.0 by SHA")
    setup_uv = next(step for step in test_steps if step.get("uses") == SETUP_UV_REF)
    require(setup_uv.get("with", {}).get("version") == "0.10.12", "tests job must pin uv 0.10.12")
    require(setup_uv.get("with", {}).get("enable-cache") is True, "tests job must enable uv cache")
    require(step_runs(test_steps, "uv sync --locked --all-groups"), "tests job must sync locked dependencies")
    require(step_runs(test_steps, "scripts/verify_ci_workflow.py"), "tests job must verify CI workflow shape")
    require(
        step_runs(test_steps, "scripts/verify_uv_runtime_docker.py"),
        "tests job must run the uv runtime and Docker verifier",
    )

    lint_job = jobs["megalinter"]
    require(lint_job.get("runs-on") == "ubuntu-latest", "megalinter job must run on ubuntu-latest")
    lint_steps = steps(lint_job, "megalinter")
    require(step_uses(lint_steps, CHECKOUT_REF), "megalinter job must pin actions/checkout v6 by SHA")
    require(step_uses(lint_steps, MEGALINTER_REF), "megalinter job must pin MegaLinter python v9.4.0 by SHA")
    mega_step = next(step for step in lint_steps if step.get("uses") == MEGALINTER_REF)
    env = mega_step.get("env", {})
    require(env.get("VALIDATE_ALL_CODEBASE") is True, "MegaLinter must validate the full codebase")


def verify_megalinter_config() -> None:
    config = load_yaml(MEGALINTER_CONFIG)
    require(config.get("APPLY_FIXES") == "none", "MegaLinter must not auto-apply fixes")
    require(config.get("DEFAULT_BRANCH") == "main", "MegaLinter default branch must be main")
    require(config.get("ENABLE_LINTERS") == ["PYTHON_RUFF", "BASH_SHELLCHECK", "YAML_PRETTIER"], "unexpected linters")
    require(config.get("PYTHON_RUFF_CONFIG_FILE") == "pyproject.toml", "MegaLinter ruff config must use pyproject.toml")


def main() -> int:
    verify_ci_workflow()
    verify_megalinter_config()
    print("CI workflow verification OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
