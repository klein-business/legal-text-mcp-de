# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Unit tests for scripts/check_spdx_header.py."""

from __future__ import annotations

from pathlib import Path

from scripts import check_spdx_header as csh

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_python_file_with_header_passes(tmp_path: Path) -> None:
    p = tmp_path / "new_module.py"
    p.write_text(
        "# SPDX-License-Identifier: Apache-2.0\n"
        "# Copyright 2026 klein-business\n"
        "def f() -> int:\n    return 1\n",
        encoding="utf-8",
    )
    assert csh.file_has_spdx_header(p) is True


def test_python_file_missing_header_fails(tmp_path: Path) -> None:
    p = tmp_path / "new_module.py"
    p.write_text("def f() -> int:\n    return 1\n", encoding="utf-8")
    assert csh.file_has_spdx_header(p) is False


def test_python_file_with_shebang_before_header_passes(tmp_path: Path) -> None:
    p = tmp_path / "script.py"
    p.write_text(
        "#!/usr/bin/env python3\n"
        "# SPDX-License-Identifier: Apache-2.0\n"
        "# Copyright 2026 klein-business\n"
        "print('hi')\n",
        encoding="utf-8",
    )
    assert csh.file_has_spdx_header(p) is True


def test_python_file_with_docstring_before_header_passes(tmp_path: Path) -> None:
    p = tmp_path / "module.py"
    p.write_text(
        '"""Module doc."""\n'
        '# SPDX-License-Identifier: Apache-2.0\n'
        '# Copyright 2026 klein-business\n'
        'x = 1\n',
        encoding="utf-8",
    )
    assert csh.file_has_spdx_header(p) is True


def test_existing_repo_file_is_exempt(tmp_path: Path, monkeypatch) -> None:
    """Files tracked in the repo's exempt-list are not required to have the header."""
    exempt_path = REPO_ROOT / "mcp" / "server.py"
    # The existing repo file does not have an SPDX header (Phase 1 didn't retrofit).
    assert csh.file_has_spdx_header(exempt_path) is False
    # But it is in the exempt list, so check_files returns OK for it.
    assert csh.check_files([exempt_path], REPO_ROOT) == 0


def test_main_rejects_new_file_without_header(tmp_path: Path) -> None:
    p = tmp_path / "new_thing.py"
    p.write_text("def x() -> int:\n    return 1\n", encoding="utf-8")
    rc = csh.check_files([p], REPO_ROOT)
    assert rc == 1
