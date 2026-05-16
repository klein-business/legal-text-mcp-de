#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Public-flip readiness gate for legal-text-mcp-de.

Verifies that the repository is in a state suitable for transitioning to
public visibility. Exits non-zero if any check fails.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal

try:
    import yaml as _yaml_module
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

REPO_ROOT = Path(__file__).resolve().parent.parent

APACHE_2_0_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"


CheckStatus = Literal["PASS", "FAIL", "SKIP"]


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str

    @property
    def passed(self) -> bool:
        """Backwards-compatible property: only PASS counts as passed."""
        return self.status == "PASS"

    @property
    def skipped(self) -> bool:
        return self.status == "SKIP"

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"


def check_license_apache_2_0(root: Path) -> CheckResult:
    path = root / "LICENSE"
    if not path.is_file():
        return CheckResult(
            name="LICENSE is Apache-2.0",
            status="FAIL",
            message=f"LICENSE missing at {path}",
        )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != APACHE_2_0_SHA256:
        return CheckResult(
            name="LICENSE is Apache-2.0",
            status="FAIL",
            message=(
                f"LICENSE sha256 mismatch: got {digest}, "
                f"expected {APACHE_2_0_SHA256}"
            ),
        )
    return CheckResult(name="LICENSE is Apache-2.0", status="PASS", message="ok")


REQUIRED_FILES = (
    "NOTICE",
    "AUTHORS.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SUPPORT.md",
    "GOVERNANCE.md",
    "ROADMAP.md",
    ".github/CODEOWNERS",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    "licenses/MIT-floleuerer.txt",
)


def check_required_files(root: Path) -> CheckResult:
    missing = [p for p in REQUIRED_FILES if not (root / p).is_file()]
    if missing:
        return CheckResult(
            name="required files exist",
            status="FAIL",
            message=f"missing: {missing}",
        )
    return CheckResult(name="required files exist", status="PASS", message="ok")


EXCLUDED_DIRS = {".git", ".venv", "__pycache__", "node_modules", "docs-legacy", "superpowers", "site"}
# verify_pre_flip.py and its test file legitimately contain the needle
# strings (as constants and test fixtures); skip them to avoid
# self-matching during the scan.
EXCLUDED_FILES = {"LICENSE", "verify_pre_flip.py", "test_verify_pre_flip.py", "CHANGELOG.md"}
PROPRIETARY_STRINGS = ("proprietary commercial", "All rights reserved.")


def check_no_proprietary_strings(root: Path) -> CheckResult:
    hits: list[tuple[str, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if rel.name in EXCLUDED_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for needle in PROPRIETARY_STRINGS:
            if needle in text:
                hits.append((str(rel), needle))
    if hits:
        return CheckResult(
            name="no proprietary strings",
            status="FAIL",
            message=f"hits: {hits}",
        )
    return CheckResult(name="no proprietary strings", status="PASS", message="ok")


REQUIRED_URLS = ("Homepage", "Repository", "Issues", "Changelog")


def check_pyproject_metadata(root: Path) -> CheckResult:
    path = root / "pyproject.toml"
    if not path.is_file():
        return CheckResult(
            name="pyproject.toml metadata",
            status="FAIL",
            message="pyproject.toml missing",
        )
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project") or {}
    failures: list[str] = []
    license_field = project.get("license")
    if license_field != "Apache-2.0":
        failures.append(f"license != 'Apache-2.0' (got {license_field!r})")
    requires_python = project.get("requires-python")
    if requires_python != ">=3.12":
        failures.append(
            f"requires-python != '>=3.12' (got {requires_python!r})"
        )
    urls = project.get("urls") or {}
    for required_url in REQUIRED_URLS:
        if required_url not in urls:
            failures.append(f"urls.{required_url} missing")
    if failures:
        return CheckResult(
            name="pyproject.toml metadata",
            status="FAIL",
            message="; ".join(failures),
        )
    return CheckResult(name="pyproject.toml metadata", status="PASS", message="ok")


def check_no_unaudited_secrets(root: Path) -> CheckResult:
    baseline = root / ".secrets.baseline"
    if not baseline.is_file():
        return CheckResult(
            name="no unaudited secrets",
            status="FAIL",
            message=(
                ".secrets.baseline missing; create via: "
                "uv run --group dev detect-secrets scan > .secrets.baseline"
            ),
        )
    detect_secrets_hook = shutil.which("detect-secrets-hook")
    if detect_secrets_hook is None:
        return CheckResult(
            name="no unaudited secrets",
            status="SKIP",
            message="detect-secrets-hook not on PATH; run via 'uv run --group dev'",
        )
    try:
        tracked = subprocess.check_output(
            ["git", "ls-files"], cwd=root, text=True
        ).splitlines()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        return CheckResult(
            name="no unaudited secrets",
            status="FAIL",
            message=f"git ls-files failed: {exc}",
        )
    # Drop noise files that are tracked but should not be scanned.
    excluded_prefixes = ("tests/fixtures/",)
    excluded_exact = {"uv.lock", ".secrets.baseline"}
    files = [
        f for f in tracked
        if f not in excluded_exact
        and not any(f.startswith(p) for p in excluded_prefixes)
    ]
    if not files:
        return CheckResult(
            name="no unaudited secrets",
            status="PASS",
            message="ok (no files to scan)",
        )
    proc = subprocess.run(
        [detect_secrets_hook, "--baseline", str(baseline), *files],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return CheckResult(
            name="no unaudited secrets",
            status="FAIL",
            message=(
                f"detect-secrets-hook exit {proc.returncode}: "
                f"{proc.stdout.strip() or proc.stderr.strip()}"
            ),
        )
    return CheckResult(name="no unaudited secrets", status="PASS", message="ok")


GITHUB_API_BASE = "https://api.github.com"
GITHUB_REPO_SLUG = "klein-business/legal-text-mcp-de"
GITHUB_DEFAULT_BRANCH = "main"

EXPECTED_REQUIRED_CHECKS = {
    "Lint (ruff)",
    "Mypy strict (scripts)",
    "Test (py3.12)",
    "Test (py3.13)",
    "Lockfile integrity",
    "Build (sdist + wheel)",
    "MegaLinter",
    "Release gate (fixture-backed)",
    "uv runtime and Docker",
    "CodeQL analysis (python)",
    "Dependency review",
    "PR title (Conventional Commits)",
    "DCO sign-off check",
}


def _fetch_github_json(path: str, token: str) -> dict[str, object]:
    url = f"{GITHUB_API_BASE}/{path.lstrip('/')}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))  # type: ignore[no-any-return]


def check_required_status_checks(root: Path) -> CheckResult:
    token = os.environ.get("VERIFY_GITHUB_TOKEN")
    if not token:
        return CheckResult(
            name="required status checks",
            status="SKIP",
            message="VERIFY_GITHUB_TOKEN not set; cannot query branch protection",
        )
    try:
        payload = _fetch_github_json(
            f"/repos/{GITHUB_REPO_SLUG}/branches/{GITHUB_DEFAULT_BRANCH}/protection",
            token,
        )
    except urllib.error.HTTPError as exc:
        return CheckResult(
            name="required status checks",
            status="FAIL",
            message=f"GitHub API {exc.code}: {exc.reason}",
        )
    rsc = payload.get("required_status_checks")
    rsc_dict = rsc if isinstance(rsc, dict) else {}
    contexts_raw = rsc_dict.get("contexts")
    contexts = set(contexts_raw if isinstance(contexts_raw, list) else [])
    missing = sorted(EXPECTED_REQUIRED_CHECKS - contexts)
    if missing:
        return CheckResult(
            name="required status checks",
            status="FAIL",
            message=f"missing required contexts: {', '.join(missing)}",
        )
    return CheckResult(name="required status checks", status="PASS", message="ok")


EXPECTED_PROTECTION_RULES = (
    ("enforce_admins", True),
    ("required_linear_history", True),
    ("allow_force_pushes", False),
    ("required_signatures", True),
)


def check_branch_protection(root: Path) -> CheckResult:
    token = os.environ.get("VERIFY_GITHUB_TOKEN")
    if not token:
        return CheckResult(
            name="branch protection",
            status="SKIP",
            message="VERIFY_GITHUB_TOKEN not set; cannot query branch protection",
        )
    try:
        payload = _fetch_github_json(
            f"/repos/{GITHUB_REPO_SLUG}/branches/{GITHUB_DEFAULT_BRANCH}/protection",
            token,
        )
    except urllib.error.HTTPError as exc:
        return CheckResult(
            name="branch protection",
            status="FAIL",
            message=f"GitHub API {exc.code}: {exc.reason}",
        )
    failures: list[str] = []
    for rule, want in EXPECTED_PROTECTION_RULES:
        block = payload.get(rule)
        block_dict = block if isinstance(block, dict) else {}
        got = bool(block_dict.get("enabled"))
        if got != want:
            failures.append(f"{rule}: expected {want}, got {got}")
    if failures:
        return CheckResult(
            name="branch protection",
            status="FAIL",
            message="; ".join(failures),
        )
    return CheckResult(name="branch protection", status="PASS", message="ok")


EXPECTED_WORKFLOWS = (
    "ci.yml",
    "e2e.yml",
    "codeql.yml",
    "scorecard.yml",
    "dependency-review.yml",
    "commitlint.yml",
    "dco.yml",
    "megalinter.yml",
    "docs.yml",
    "gitleaks.yml",
    "release.yml",
    "release-please.yml",
    "trivy.yml",
)


def check_workflow_set(root: Path) -> CheckResult:
    wf_dir = root / ".github" / "workflows"
    if not wf_dir.is_dir():
        return CheckResult(
            name="workflow set",
            status="FAIL",
            message=f"{wf_dir} does not exist",
        )
    present = {
        p.name
        for p in wf_dir.iterdir()
        if p.is_file() and p.suffix in {".yml", ".yaml"}
    }
    expected = set(EXPECTED_WORKFLOWS)
    missing = sorted(expected - present)
    extra = sorted(present - expected)
    problems: list[str] = []
    if missing:
        problems.append(f"missing: {', '.join(missing)}")
    if extra:
        problems.append(f"unexpected: {', '.join(extra)}")
    if problems:
        return CheckResult(
            name="workflow set",
            status="FAIL",
            message="; ".join(problems),
        )
    return CheckResult(name="workflow set", status="PASS", message="ok")


EXPECTED_RELEASE_JOBS = {
    "build-python",
    "slsa-python",
    "publish-pypi",
    "build-image",
    "slsa-oci",
    "cosign-sign-image",
    "github-release",
}


def check_release_workflow_present(root: Path) -> CheckResult:
    path = root / ".github" / "workflows" / "release.yml"
    if not path.is_file():
        return CheckResult(
            name="release workflow present",
            status="FAIL",
            message=f"release.yml missing at {path}",
        )
    if not _YAML_AVAILABLE:
        return CheckResult(
            name="release workflow present",
            status="SKIP",
            message="pyyaml not available; cannot parse release.yml",
        )
    try:
        data = _yaml_module.safe_load(path.read_text(encoding="utf-8"))
    except _yaml_module.YAMLError as exc:
        return CheckResult(
            name="release workflow present",
            status="FAIL",
            message=f"release.yml YAML parse error: {exc}",
        )
    jobs = (data or {}).get("jobs") or {}
    missing = sorted(EXPECTED_RELEASE_JOBS - set(jobs.keys()))
    if missing:
        return CheckResult(
            name="release workflow present",
            status="FAIL",
            message=f"missing required jobs: {', '.join(missing)}",
        )
    return CheckResult(name="release workflow present", status="PASS", message="ok")


def check_pypi_name_reserved(root: Path) -> CheckResult:
    url = "https://pypi.org/pypi/legal-text-mcp-de/json"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                return CheckResult(
                    name="PyPI name reserved",
                    status="PASS",
                    message="ok (200 from pypi.org)",
                )
            return CheckResult(
                name="PyPI name reserved",
                status="FAIL",
                message=f"PyPI returned {resp.status}; expected 200",
            )
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return CheckResult(
                name="PyPI name reserved",
                status="FAIL",
                message="404 from pypi.org — package name not reserved",
            )
        return CheckResult(
            name="PyPI name reserved",
            status="FAIL",
            message=f"HTTP {exc.code}: {exc.reason}",
        )
    except OSError as exc:
        return CheckResult(
            name="PyPI name reserved",
            status="SKIP",
            message=f"cannot reach pypi.org: {exc}",
        )


CHECKS = [
    check_license_apache_2_0,
    check_required_files,
    check_no_proprietary_strings,
    check_pyproject_metadata,
    check_no_unaudited_secrets,
    check_workflow_set,
    check_required_status_checks,
    check_branch_protection,
    check_release_workflow_present,
    check_pypi_name_reserved,
]


def _aggregate_exit_code(results: list[CheckResult]) -> int:
    """Return 0 if no FAIL, else 1. SKIP counts as success."""
    return 0 if not any(r.failed for r in results) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    results = [check(args.root) for check in CHECKS]
    for r in results:
        print(f"[{r.status}] {r.name}: {r.message}")

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps([asdict(r) for r in results], indent=2, sort_keys=True),
            encoding="utf-8",
        )

    return _aggregate_exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
