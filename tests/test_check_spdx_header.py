# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Unit tests for scripts/check_spdx_header.py."""

from __future__ import annotations

from pathlib import Path

from scripts import check_spdx_header as csh

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_python_file_with_header_passes(tmp_path: Path) -> None:
    p = tmp_path / "new_module.py"
    p.write_text(
        "# SPDX-License-Identifier: Apache-2.0\n# Copyright 2026 klein-business\ndef f() -> int:\n    return 1\n",
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
        "#!/usr/bin/env python3\n# SPDX-License-Identifier: Apache-2.0\n# Copyright 2026 klein-business\nprint('hi')\n",
        encoding="utf-8",
    )
    assert csh.file_has_spdx_header(p) is True


def test_python_file_with_docstring_before_header_passes(tmp_path: Path) -> None:
    p = tmp_path / "module.py"
    p.write_text(
        '"""Module doc."""\n# SPDX-License-Identifier: Apache-2.0\n# Copyright 2026 klein-business\nx = 1\n',
        encoding="utf-8",
    )
    assert csh.file_has_spdx_header(p) is True


def test_retrofitted_repo_file_has_header(tmp_path: Path, monkeypatch) -> None:
    """After Phase-1 retrofit all tracked files carry the SPDX header."""
    retrofitted_path = REPO_ROOT / "src" / "legal_text_mcp_de" / "server.py"
    # The Phase-1-era file was retrofitted in C-1; it now has the header.
    assert csh.file_has_spdx_header(retrofitted_path) is True
    # And check_files also passes (header present, no exemption needed).
    assert csh.check_files([retrofitted_path], REPO_ROOT) == 0


def test_main_rejects_new_file_without_header(tmp_path: Path) -> None:
    p = tmp_path / "new_thing.py"
    p.write_text("def x() -> int:\n    return 1\n", encoding="utf-8")
    rc = csh.check_files([p], REPO_ROOT)
    assert rc == 1
