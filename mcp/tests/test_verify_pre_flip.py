"""Unit tests for scripts/verify_pre_flip.py."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from scripts import verify_pre_flip as vpf

REPO_ROOT = Path(__file__).resolve().parents[2]
APACHE_2_0_FIXTURE = (
    REPO_ROOT / "mcp" / "tests" / "fixtures" / "legal" / "apache-2.0-canonical.txt"
)


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
    assert "MIT-floleuerer.txt" in result.message


def test_no_proprietary_strings_passes_when_absent(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Apache 2.0 project", encoding="utf-8")
    result = vpf.check_no_proprietary_strings(tmp_path)
    assert result.passed is True, result.message


def test_no_proprietary_strings_fails_on_proprietary_commercial(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text(
        "This is proprietary commercial software.", encoding="utf-8"
    )
    result = vpf.check_no_proprietary_strings(tmp_path)
    assert result.passed is False
    assert "README.md" in result.message
    assert "proprietary" in result.message.lower()


def test_no_proprietary_strings_ignores_docs_legacy(tmp_path: Path) -> None:
    (tmp_path / "docs-legacy").mkdir()
    (tmp_path / "docs-legacy" / "old.md").write_text(
        "This was proprietary commercial.", encoding="utf-8"
    )
    result = vpf.check_no_proprietary_strings(tmp_path)
    assert result.passed is True, result.message


def test_no_proprietary_strings_ignores_license_file(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").write_text(
        "Copyright (c) 2025 X. All rights reserved.", encoding="utf-8"
    )
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
    (tmp_path / "pyproject.toml").write_text(
        PYPROJECT_INVALID_LICENSE, encoding="utf-8"
    )
    result = vpf.check_pyproject_metadata(tmp_path)
    assert result.passed is False
    assert "license" in result.message.lower()


def test_pyproject_metadata_fails_on_missing_url(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        PYPROJECT_MISSING_URL, encoding="utf-8"
    )
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
    real_root = Path(__file__).resolve().parents[2]
    result = vpf.check_no_unaudited_secrets(real_root)
    assert result.passed is True, result.message
