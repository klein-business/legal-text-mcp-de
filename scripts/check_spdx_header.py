#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Pre-commit hook: ensure new Python files carry the SPDX header.

Files that existed before Phase 2 are exempt via the EXEMPT_PATHS list,
loaded from .github/spdx-header-exempt.txt at runtime. Files not on the
exempt list must contain both lines:

  # SPDX-License-Identifier: Apache-2.0
  # Copyright 2026 klein-business

within the first 10 lines (after an optional shebang and/or docstring).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SPDX_LINE = "# SPDX-License-Identifier: Apache-2.0"
COPYRIGHT_LINE = "# Copyright 2026 klein-business"
SCAN_LINES = 10


def _load_exempt_list(repo_root: Path) -> set[Path]:
    exempt_file = repo_root / ".github" / "spdx-header-exempt.txt"
    if not exempt_file.is_file():
        return set()
    paths: set[Path] = set()
    for line in exempt_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        paths.add((repo_root / line).resolve())
    return paths


def file_has_spdx_header(path: Path) -> bool:
    """True iff both SPDX_LINE and COPYRIGHT_LINE appear in the first SCAN_LINES."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    head = text.splitlines()[:SCAN_LINES]
    return SPDX_LINE in head and COPYRIGHT_LINE in head


def check_files(paths: list[Path], repo_root: Path) -> int:
    exempt = _load_exempt_list(repo_root)
    failures: list[Path] = []
    for p in paths:
        if not p.exists() or not p.is_file():
            continue
        if p.suffix != ".py":
            continue
        resolved = p.resolve()
        if resolved in exempt:
            continue
        if not file_has_spdx_header(p):
            failures.append(p)
    for f in failures:
        print(
            f"missing SPDX header: {f}\n"
            f"  expected first 10 lines to contain:\n"
            f"    {SPDX_LINE}\n"
            f"    {COPYRIGHT_LINE}\n",
            file=sys.stderr,
        )
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    paths = [Path(a) for a in args]
    return check_files(paths, REPO_ROOT)


if __name__ == "__main__":
    sys.exit(main())
