"""Unit tests for scripts/verify_pre_flip.py."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
APACHE_2_0_FIXTURE = (
    REPO_ROOT / "mcp" / "tests" / "fixtures" / "legal" / "apache-2.0-canonical.txt"
)

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import verify_pre_flip as vpf  # noqa: E402


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
