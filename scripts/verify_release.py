#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import re
from pathlib import Path


TESTS = [
    "mcp/tests/test_fixture_coverage.py",
    "mcp/tests/test_error_contracts.py",
    "mcp/tests/test_release_gate.py",
    "mcp/tests/test_source_matrix_live.py",
    "mcp/tests/test_http_api.py",
    "mcp/tests/test_mcp_tools.py",
    "mcp/tests/test_search.py",
    "mcp/tests/test_resolver.py",
    "mcp/tests/test_normalizer_gii.py",
    "mcp/tests/test_normalizer_eurlex.py",
    "mcp/tests/test_dataset_validation.py",
    "mcp/tests/test_registry.py",
    "mcp/tests/test_source_import.py",
    "mcp/tests/test_source_matrix.py",
    "mcp/tests/test_parser.py",
    "mcp/tests/test_library.py",
]


def check_docs_links() -> None:
    for path in Path("docs").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if re.search(r"\{\{[^}]+\}\}", text):
            raise SystemExit(f"Unresolved placeholder in {path}")


def main() -> int:
    check_docs_links()
    cmd = [sys.executable, "-m", "pytest", *TESTS]
    print("Running:", " ".join(cmd), flush=True)
    test_result = subprocess.call(cmd)
    if test_result != 0:
        return test_result
    e2e_cmd = [sys.executable, "scripts/verify_e2e.py"]
    print("Running:", " ".join(e2e_cmd), flush=True)
    return subprocess.call(e2e_cmd)


if __name__ == "__main__":
    raise SystemExit(main())
