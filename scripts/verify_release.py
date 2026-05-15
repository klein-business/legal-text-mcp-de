#!/usr/bin/env python3
from __future__ import annotations

import os
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


def selected_tests() -> list[str]:
    if os.environ.get("SKIP_LIVE_SOURCE_MATRIX") != "true":
        return TESTS
    skipped = "mcp/tests/test_source_matrix_live.py"
    print(f"Skipping external live source probes in CI: {skipped}", flush=True)
    return [test for test in TESTS if test != skipped]


def check_docs_links() -> None:
    for path in Path("docs").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if re.search(r"\{\{[^}]+\}\}", text):
            raise SystemExit(f"Unresolved placeholder in {path}")


def check_no_stale_workflow_refs() -> None:
    scan_roots = [
        Path("README.md"),
        Path("docs"),
        Path("scripts"),
        Path("mcp"),
        Path("prepare_data"),
        Path("Dockerfile"),
    ]
    excluded_files = {
        Path("scripts/verify_release.py"),
        Path("scripts/verify_uv_runtime_docker.py"),
    }
    skipped_dirs = {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
    }
    stale_patterns = [
        re.compile(r"python3(?:\.\d+)? -m venv"),
        re.compile(r"pip install -r"),
        re.compile(r"requirements[.]txt"),
        re.compile(r"source [.]venv/bin/activate"),
        re.compile(r"source venv/bin/activate"),
        re.compile(r"PYTHONPATH=mcp python(?:\s|$)"),
    ]
    multiline_command_pattern = re.compile(r"PYTHONPATH=mcp\s+python(?:\s|$)")

    def iter_files(path: Path):
        if not path.exists():
            return
        if path.is_file():
            yield path
            return
        for child in path.rglob("*"):
            if child.is_dir() or any(part in skipped_dirs for part in child.parts):
                continue
            if child.is_file():
                yield child

    violations: list[str] = []
    for root in scan_roots:
        for path in iter_files(root):
            if path in excluded_files:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            logical_text = re.sub(r"\\\s*\n\s*", " ", text)
            if multiline_command_pattern.search(logical_text):
                violations.append(f"{path}: unsupported direct PYTHONPATH=mcp python command")
            for line_no, line in enumerate(text.splitlines(), start=1):
                if any(pattern.search(line) for pattern in stale_patterns):
                    violations.append(f"{path}:{line_no}: {line.strip()}")

    if violations:
        detail = "\n".join(violations)
        raise SystemExit(f"Unsupported active workflow references found:\n{detail}")


def main() -> int:
    check_docs_links()
    check_no_stale_workflow_refs()
    cmd = [sys.executable, "-m", "pytest", *selected_tests()]
    print("Running:", " ".join(cmd), flush=True)
    test_result = subprocess.call(cmd)
    if test_result != 0:
        return test_result
    e2e_cmd = [sys.executable, "scripts/verify_e2e.py"]
    print("Running:", " ".join(e2e_cmd), flush=True)
    return subprocess.call(e2e_cmd)


if __name__ == "__main__":
    raise SystemExit(main())
