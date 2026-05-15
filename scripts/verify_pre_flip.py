#!/usr/bin/env python3
"""Public-flip readiness gate for legal-text-mcp-de.

Verifies that the repository is in a state suitable for transitioning to
public visibility. Exits non-zero if any check fails.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

APACHE_2_0_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str


def check_license_apache_2_0(root: Path) -> CheckResult:
    path = root / "LICENSE"
    if not path.is_file():
        return CheckResult(
            name="LICENSE is Apache-2.0",
            passed=False,
            message=f"LICENSE missing at {path}",
        )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != APACHE_2_0_SHA256:
        return CheckResult(
            name="LICENSE is Apache-2.0",
            passed=False,
            message=(
                f"LICENSE sha256 mismatch: got {digest}, "
                f"expected {APACHE_2_0_SHA256}"
            ),
        )
    return CheckResult(name="LICENSE is Apache-2.0", passed=True, message="ok")


REQUIRED_FILES = (
    "NOTICE",
    "AUTHORS.md",
    "CHANGELOG.md",
    "licenses/MIT-floleuerer.txt",
)


def check_required_files(root: Path) -> CheckResult:
    missing = [p for p in REQUIRED_FILES if not (root / p).is_file()]
    if missing:
        return CheckResult(
            name="required files exist",
            passed=False,
            message=f"missing: {missing}",
        )
    return CheckResult(name="required files exist", passed=True, message="ok")


CHECKS = [
    check_license_apache_2_0,
    check_required_files,
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    results = [check(args.root) for check in CHECKS]
    for r in results:
        flag = "PASS" if r.passed else "FAIL"
        print(f"[{flag}] {r.name}: {r.message}")

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps([asdict(r) for r in results], indent=2, sort_keys=True),
            encoding="utf-8",
        )

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
