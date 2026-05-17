# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Unit tests for scripts/verify_pre_flip.py."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import verify_pre_flip as vpf

REPO_ROOT = Path(__file__).resolve().parents[1]
APACHE_2_0_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "legal" / "apache-2.0-canonical.txt"


def _materialise_apache_license(target_dir: Path) -> Path:
    target = target_dir / "LICENSE"
    target.write_text(APACHE_2_0_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def test_check_license_apache_2_0_passes_for_canonical_text(tmp_path: Path) -> None:
    _materialise_apache_license(tmp_path)
    result = vpf.check_license_apache_2_0(tmp_path)
    assert result.passed is True, result.message


def test_check_license_apache_2_0_fails_for_wrong_text(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").write_text("not Apache 2.0", encoding="utf-8")
    result = vpf.check_license_apache_2_0(tmp_path)
    assert result.passed is False
    assert "Apache" in result.message or "sha256" in result.message


def test_check_license_apache_2_0_fails_when_missing(tmp_path: Path) -> None:
    result = vpf.check_license_apache_2_0(tmp_path)
    assert result.passed is False
    assert "LICENSE" in result.message


def test_required_files_passes_when_all_present(tmp_path: Path) -> None:
    (tmp_path / "NOTICE").write_text("notice", encoding="utf-8")
    (tmp_path / "AUTHORS.md").write_text("authors", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("changelog", encoding="utf-8")
    (tmp_path / "SECURITY.md").write_text("security", encoding="utf-8")
    (tmp_path / "CONTRIBUTING.md").write_text("c", encoding="utf-8")
    (tmp_path / "CODE_OF_CONDUCT.md").write_text("c", encoding="utf-8")
    (tmp_path / "SUPPORT.md").write_text("s", encoding="utf-8")
    (tmp_path / "GOVERNANCE.md").write_text("g", encoding="utf-8")
    (tmp_path / "ROADMAP.md").write_text("r", encoding="utf-8")
    (tmp_path / ".github").mkdir(exist_ok=True)
    (tmp_path / ".github" / "CODEOWNERS").write_text("*", encoding="utf-8")
    (tmp_path / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text("p", encoding="utf-8")
    (tmp_path / ".github" / "ISSUE_TEMPLATE").mkdir(exist_ok=True)
    (tmp_path / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").write_text("y", encoding="utf-8")
    (tmp_path / "licenses").mkdir()
    (tmp_path / "licenses" / "MIT-floleuerer.txt").write_text("mit", encoding="utf-8")

    result = vpf.check_required_files(tmp_path)
    assert result.passed is True, result.message


def test_required_files_fails_when_any_missing(tmp_path: Path) -> None:
    (tmp_path / "NOTICE").write_text("notice", encoding="utf-8")
    result = vpf.check_required_files(tmp_path)
    assert result.passed is False
    assert "AUTHORS.md" in result.message
    assert "CHANGELOG.md" in result.message
    assert "SECURITY.md" in result.message
    assert "MIT-floleuerer.txt" in result.message


def test_no_proprietary_strings_passes_when_absent(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Apache 2.0 project", encoding="utf-8")
    result = vpf.check_no_proprietary_strings(tmp_path)
    assert result.passed is True, result.message


def test_no_proprietary_strings_fails_on_proprietary_commercial(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("This is proprietary commercial software.", encoding="utf-8")
    result = vpf.check_no_proprietary_strings(tmp_path)
    assert result.passed is False
    assert "README.md" in result.message
    assert "proprietary" in result.message.lower()


def test_no_proprietary_strings_ignores_docs_legacy(tmp_path: Path) -> None:
    (tmp_path / "docs-legacy").mkdir()
    (tmp_path / "docs-legacy" / "old.md").write_text("This was proprietary commercial.", encoding="utf-8")
    result = vpf.check_no_proprietary_strings(tmp_path)
    assert result.passed is True, result.message


def test_no_proprietary_strings_ignores_license_file(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").write_text("Copyright (c) 2025 X. All rights reserved.", encoding="utf-8")
    result = vpf.check_no_proprietary_strings(tmp_path)
    assert result.passed is True, result.message


def test_no_proprietary_strings_skips_verify_pre_flip_sources(tmp_path: Path) -> None:
    """The script and its test file may legitimately contain the needles.

    They MUST be skipped, otherwise the gate flags its own sources.
    """
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "verify_pre_flip.py").write_text(
        "PROPRIETARY_STRINGS = ('proprietary commercial',)\n",
        encoding="utf-8",
    )
    (tmp_path / "mcp" / "tests").mkdir(parents=True)
    (tmp_path / "mcp" / "tests" / "test_verify_pre_flip.py").write_text(
        "x = 'proprietary commercial'\n",
        encoding="utf-8",
    )
    result = vpf.check_no_proprietary_strings(tmp_path)
    assert result.passed is True, result.message


def test_no_proprietary_strings_skips_changelog(tmp_path: Path) -> None:
    """CHANGELOG.md may contain 'proprietary commercial' as a historical note.

    It MUST be skipped so the transition entry does not trigger the gate.
    """
    (tmp_path / "CHANGELOG.md").write_text(
        "- Re-licensed from proprietary commercial to Apache License 2.0.\n",
        encoding="utf-8",
    )
    result = vpf.check_no_proprietary_strings(tmp_path)
    assert result.passed is True, result.message


PYPROJECT_VALID = """\
[project]
name = "legal-text-mcp-de"
version = "0.1.0"
description = "x"
license = "Apache-2.0"
requires-python = ">=3.12"

[project.urls]
Homepage = "https://example.test"
Repository = "https://example.test/repo"
Issues = "https://example.test/issues"
Changelog = "https://example.test/changelog"
"""

PYPROJECT_INVALID_LICENSE = """\
[project]
name = "x"
version = "0.1.0"
description = "x"
license = "MIT"
requires-python = ">=3.12"

[project.urls]
Homepage = "https://example.test"
Repository = "https://example.test/repo"
Issues = "https://example.test/issues"
Changelog = "https://example.test/changelog"
"""

PYPROJECT_MISSING_URL = """\
[project]
name = "x"
version = "0.1.0"
description = "x"
license = "Apache-2.0"
requires-python = ">=3.12"

[project.urls]
Homepage = "https://example.test"
"""


def test_pyproject_metadata_passes_for_valid(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(PYPROJECT_VALID, encoding="utf-8")
    result = vpf.check_pyproject_metadata(tmp_path)
    assert result.passed is True, result.message


def test_pyproject_metadata_fails_on_wrong_license(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(PYPROJECT_INVALID_LICENSE, encoding="utf-8")
    result = vpf.check_pyproject_metadata(tmp_path)
    assert result.passed is False
    assert "license" in result.message.lower()


def test_pyproject_metadata_fails_on_missing_url(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(PYPROJECT_MISSING_URL, encoding="utf-8")
    result = vpf.check_pyproject_metadata(tmp_path)
    assert result.passed is False
    assert "Repository" in result.message


def test_pyproject_metadata_fails_when_missing(tmp_path: Path) -> None:
    result = vpf.check_pyproject_metadata(tmp_path)
    assert result.passed is False
    assert "pyproject.toml" in result.message


def test_secrets_scan_fails_when_baseline_missing(tmp_path: Path) -> None:
    result = vpf.check_no_unaudited_secrets(tmp_path)
    assert result.passed is False
    assert ".secrets.baseline" in result.message


@pytest.mark.skipif(
    shutil.which("detect-secrets-hook") is None,
    reason="detect-secrets-hook not on PATH; run via uv run --group dev",
)
def test_secrets_scan_passes_on_real_repo() -> None:
    real_root = Path(__file__).resolve().parents[1]
    result = vpf.check_no_unaudited_secrets(real_root)
    assert result.passed is True, result.message


def _populate_passing_repo(root: Path) -> None:
    """Populate `root` with the artefacts needed for all checks to pass."""
    _materialise_apache_license(root)
    (root / "NOTICE").write_text("notice", encoding="utf-8")
    (root / "AUTHORS.md").write_text("authors", encoding="utf-8")
    (root / "CHANGELOG.md").write_text("changelog", encoding="utf-8")
    (root / "SECURITY.md").write_text("security", encoding="utf-8")
    (root / "CONTRIBUTING.md").write_text("c", encoding="utf-8")
    (root / "CODE_OF_CONDUCT.md").write_text("c", encoding="utf-8")
    (root / "SUPPORT.md").write_text("s", encoding="utf-8")
    (root / "GOVERNANCE.md").write_text("g", encoding="utf-8")
    (root / "ROADMAP.md").write_text("r", encoding="utf-8")
    (root / ".github").mkdir(exist_ok=True)
    (root / ".github" / "CODEOWNERS").write_text("*", encoding="utf-8")
    (root / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text("p", encoding="utf-8")
    (root / ".github" / "ISSUE_TEMPLATE").mkdir(exist_ok=True)
    (root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").write_text("y", encoding="utf-8")
    (root / "licenses").mkdir()
    (root / "licenses" / "MIT-floleuerer.txt").write_text("mit", encoding="utf-8")
    (root / "pyproject.toml").write_text(PYPROJECT_VALID, encoding="utf-8")
    (root / ".secrets.baseline").write_text(
        '{"version": "1.5.0", "results": {}}',
        encoding="utf-8",
    )


def test_main_writes_json_report(tmp_path: Path) -> None:
    _populate_passing_repo(tmp_path)
    output = tmp_path / "report.json"
    vpf.main(["--root", str(tmp_path), "--output", str(output)])
    assert output.is_file()
    payload = json.loads(output.read_text())
    assert isinstance(payload, list)
    assert {r["name"] for r in payload} >= {
        "LICENSE is Apache-2.0",
        "required files exist",
        "no proprietary strings",
        "pyproject.toml metadata",
        "no unaudited secrets",
    }


def test_main_returns_nonzero_when_license_wrong(tmp_path: Path) -> None:
    _populate_passing_repo(tmp_path)
    (tmp_path / "LICENSE").write_text("not apache", encoding="utf-8")
    rc = vpf.main(["--root", str(tmp_path)])
    assert rc == 1


def test_check_result_supports_skipped_status() -> None:
    """SKIPPED is a valid third status value."""
    skipped = vpf.CheckResult(name="x", status="SKIP", message="reason")
    assert skipped.status == "SKIP"
    assert skipped.passed is False  # backwards-compat property
    assert skipped.skipped is True


def test_secrets_scan_skips_when_tool_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When detect-secrets-hook is not on PATH, return SKIPPED, not FAIL."""
    (tmp_path / ".secrets.baseline").write_text('{"version": "1.5.0", "results": {}}', encoding="utf-8")
    monkeypatch.setattr(vpf.shutil, "which", lambda name: None)
    result = vpf.check_no_unaudited_secrets(tmp_path)
    assert result.status == "SKIP", result.message
    assert "detect-secrets-hook" in result.message


def test_aggregate_exit_code_returns_zero_for_pass_and_skip() -> None:
    skipped = vpf.CheckResult(name="x", status="SKIP", message="m")
    passed = vpf.CheckResult(name="y", status="PASS", message="ok")
    assert vpf._aggregate_exit_code([skipped, passed]) == 0


def test_aggregate_exit_code_returns_nonzero_when_any_fail() -> None:
    failed = vpf.CheckResult(name="x", status="FAIL", message="m")
    passed = vpf.CheckResult(name="y", status="PASS", message="ok")
    skipped = vpf.CheckResult(name="z", status="SKIP", message="m")
    assert vpf._aggregate_exit_code([passed, skipped, failed]) == 1


EXPECTED_WORKFLOWS = {
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
    "research-topic-smoke.yml",
    "trivy.yml",
}


def test_workflow_set_passes_when_complete(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    for name in EXPECTED_WORKFLOWS:
        (wf / name).write_text("name: x\non: push", encoding="utf-8")
    result = vpf.check_workflow_set(tmp_path)
    assert result.status == "PASS", result.message


def test_workflow_set_fails_when_missing(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text("name: x", encoding="utf-8")
    result = vpf.check_workflow_set(tmp_path)
    assert result.status == "FAIL"
    assert "missing" in result.message.lower()
    assert "codeql.yml" in result.message


def test_workflow_set_fails_when_extra(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    for name in EXPECTED_WORKFLOWS:
        (wf / name).write_text("x", encoding="utf-8")
    (wf / "rogue.yml").write_text("x", encoding="utf-8")
    result = vpf.check_workflow_set(tmp_path)
    assert result.status == "FAIL"
    assert "unexpected" in result.message.lower()
    assert "rogue.yml" in result.message


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


def test_required_status_checks_skips_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VERIFY_GITHUB_TOKEN", raising=False)
    result = vpf.check_required_status_checks(Path("/tmp"))
    assert result.status == "SKIP"
    assert "VERIFY_GITHUB_TOKEN" in result.message


def test_required_status_checks_passes_when_all_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERIFY_GITHUB_TOKEN", "fake-token")
    payload = {
        "required_status_checks": {
            "contexts": list(EXPECTED_REQUIRED_CHECKS),
        }
    }
    with patch.object(vpf, "_fetch_github_json", return_value=payload):
        result = vpf.check_required_status_checks(Path("/tmp"))
    assert result.status == "PASS", result.message


def test_required_status_checks_fails_when_any_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERIFY_GITHUB_TOKEN", "fake-token")
    payload = {
        "required_status_checks": {
            "contexts": ["Lint (ruff)"],
        }
    }
    with patch.object(vpf, "_fetch_github_json", return_value=payload):
        result = vpf.check_required_status_checks(Path("/tmp"))
    assert result.status == "FAIL"
    assert "missing" in result.message.lower()


def test_branch_protection_skips_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VERIFY_GITHUB_TOKEN", raising=False)
    result = vpf.check_branch_protection(Path("/tmp"))
    assert result.status == "SKIP"


def test_branch_protection_passes_when_strict(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERIFY_GITHUB_TOKEN", "fake")
    payload = {
        "enforce_admins": {"enabled": True},
        "required_linear_history": {"enabled": True},
        "allow_force_pushes": {"enabled": False},
        "required_signatures": {"enabled": True},
    }
    with patch.object(vpf, "_fetch_github_json", return_value=payload):
        result = vpf.check_branch_protection(Path("/tmp"))
    assert result.status == "PASS", result.message


def test_branch_protection_fails_when_admins_not_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERIFY_GITHUB_TOKEN", "fake")
    payload = {
        "enforce_admins": {"enabled": False},
        "required_linear_history": {"enabled": True},
        "allow_force_pushes": {"enabled": False},
        "required_signatures": {"enabled": True},
    }
    with patch.object(vpf, "_fetch_github_json", return_value=payload):
        result = vpf.check_branch_protection(Path("/tmp"))
    assert result.status == "FAIL"
    assert "enforce_admins" in result.message


EXPECTED_RELEASE_JOBS = {
    "build-python",
    "slsa-python",
    "publish-pypi",
    "build-image",
    "slsa-oci",
    "cosign-sign-image",
    "github-release",
}


def test_release_workflow_passes_when_jobs_present(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    job_block = "\n".join(f"  {j}:\n    runs-on: ubuntu-latest" for j in EXPECTED_RELEASE_JOBS)
    (wf / "release.yml").write_text(
        f"name: Release\non:\n  push:\n    tags: ['v*.*.*']\njobs:\n{job_block}\n",
        encoding="utf-8",
    )
    result = vpf.check_release_workflow_present(tmp_path)
    assert result.status == "PASS", result.message


def test_release_workflow_fails_when_missing(tmp_path: Path) -> None:
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    result = vpf.check_release_workflow_present(tmp_path)
    assert result.status == "FAIL"
    assert "release.yml" in result.message


def test_release_workflow_fails_when_jobs_missing(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "release.yml").write_text(
        "name: Release\non:\n  push:\n    tags: ['v*.*.*']\njobs:\n  build-python:\n    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )
    result = vpf.check_release_workflow_present(tmp_path)
    assert result.status == "FAIL"
    assert "missing" in result.message.lower()


def test_pypi_name_reserved_passes_on_200(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def __init__(self, code: int) -> None:
            self.status = code
            self.code = code

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *a: object) -> bool:
            return False

    def fake_urlopen(req: object, timeout: int = 10) -> FakeResponse:
        return FakeResponse(200)

    monkeypatch.setattr(vpf.urllib.request, "urlopen", fake_urlopen)
    result = vpf.check_pypi_name_reserved(Path("/tmp"))
    assert result.status == "PASS", result.message


def test_pypi_name_reserved_fails_on_404(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req: object, timeout: int = 10) -> None:
        import urllib.error

        raise urllib.error.HTTPError(
            "https://pypi.org/pypi/legal-text-mcp-de/json",
            404,
            "Not Found",
            {},
            None,  # type: ignore[arg-type]
        )

    monkeypatch.setattr(vpf.urllib.request, "urlopen", fake_urlopen)
    result = vpf.check_pypi_name_reserved(Path("/tmp"))
    assert result.status == "FAIL"
    assert "404" in result.message or "not reserved" in result.message.lower()


def test_pypi_name_reserved_skips_on_other_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req: object, timeout: int = 10) -> None:
        raise OSError("network unreachable")

    monkeypatch.setattr(vpf.urllib.request, "urlopen", fake_urlopen)
    result = vpf.check_pypi_name_reserved(Path("/tmp"))
    assert result.status == "SKIP"


def test_security_settings_skips_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VERIFY_GITHUB_TOKEN", raising=False)
    result = vpf.check_security_settings(Path("/tmp"))
    assert result.status == "SKIP"


def test_security_settings_passes_when_all_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERIFY_GITHUB_TOKEN", "fake")
    payload = {
        "security_and_analysis": {
            "secret_scanning": {"status": "enabled"},
            "secret_scanning_push_protection": {"status": "enabled"},
        },
        "private_vulnerability_reporting": {"status": "enabled"},
    }
    with patch.object(vpf, "_fetch_github_json", return_value=payload):
        result = vpf.check_security_settings(Path("/tmp"))
    assert result.status == "PASS", result.message


def test_security_settings_fails_when_any_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERIFY_GITHUB_TOKEN", "fake")
    payload = {
        "security_and_analysis": {
            "secret_scanning": {"status": "disabled"},
            "secret_scanning_push_protection": {"status": "enabled"},
        },
        "private_vulnerability_reporting": {"status": "enabled"},
    }
    with patch.object(vpf, "_fetch_github_json", return_value=payload):
        result = vpf.check_security_settings(Path("/tmp"))
    assert result.status == "FAIL"
    assert "secret_scanning" in result.message
