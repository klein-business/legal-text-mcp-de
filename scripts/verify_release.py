#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import os
import subprocess
import sys
import re
from collections.abc import Generator
from pathlib import Path
from urllib.parse import unquote, urlsplit


TESTS = [
    "tests/test_fixture_coverage.py",
    "tests/test_error_contracts.py",
    "tests/test_release_gate.py",
    "tests/test_http_api.py",
    "tests/test_mcp_tools.py",
    "tests/test_runtime_coverage_relationships.py",
    "tests/test_operational_corpus_gates.py",
    "tests/test_search_scaling.py",
    "tests/test_search.py",
    "tests/test_resolver.py",
    "tests/test_normalizer_gii.py",
    "tests/test_normalizer_eurlex.py",
    "tests/test_corpus_manifest.py",
    "tests/test_generated_package.py",
    "tests/test_gii_toc_discovery.py",
    "tests/test_gii_bulk_normalization.py",
    "tests/test_dsgvo_full_counts.py",
    "tests/test_scope_graph_policy.py",
    "tests/test_relationship_records.py",
    "tests/test_eu_neighbor_acts.py",
    "tests/test_state_law_inventory.py",
    "tests/test_state_law_adapters.py",
    "tests/test_state_law_coverage.py",
    "tests/test_state_law_pdf_and_limitations.py",
    "tests/test_dataset_validation.py",
    "tests/test_registry.py",
    "tests/test_source_import.py",
    "tests/test_source_matrix.py",
    "tests/test_parser.py",
    "tests/test_library.py",
]
LIVE_TESTS = ["tests/test_source_matrix_live.py"]
DOC_CHECK_ROOTS = [
    Path("README.md"),
    Path("docs"),
    Path("docs-legacy"),
    Path("plans"),
]
# Internal design/plan documents that reference spec-forward file paths that may not
# exist yet or resolve relative to the repo root rather than the document's directory.
DOC_CHECK_EXCLUDED_DIRS: frozenset[str] = frozenset({"superpowers"})
STALE_WORKFLOW_CHECK_ROOTS = [
    Path("README.md"),
    Path("docs"),
    Path("docs-legacy"),
    Path("plans"),
    Path("scripts"),
    Path("src"),
    Path("tests"),
    Path("prepare_data"),
    Path("Dockerfile"),
]
REMOTE_SCHEMES = {"http", "https", "mailto", "tel"}
MARKDOWN_LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)]+)\)")
HTML_IMG_RE = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}|(?:TODO|TBD|FIXME)_PLACEHOLDER|REPLACE_ME")
DIRECT_PYTHON_WITH_PYTHONPATH_RE = re.compile(r"PYTHONPATH=mcp\s+python(?:3(?:\.\d+)?)?(?:\s|$)")


def selected_tests() -> list[str]:
    if os.environ.get("RUN_LIVE_SOURCE_MATRIX") == "true":
        print(f"Including explicit live source probes: {', '.join(LIVE_TESTS)}", flush=True)
        return [*TESTS, *LIVE_TESTS]
    return TESTS


def check_docs_links(roots: list[Path] | None = None) -> None:
    violations: list[str] = []
    for path in _iter_markdown_files(roots or DOC_CHECK_ROOTS):
        text = path.read_text(encoding="utf-8")
        if PLACEHOLDER_RE.search(text):
            violations.append(f"{path}: unresolved placeholder")
        for is_image, target in _markdown_targets(text):
            violations.extend(_validate_local_target(path, target, "Markdown image" if is_image else "Markdown link"))
        for target in HTML_IMG_RE.findall(text):
            violations.extend(_validate_local_target(path, target, "HTML image"))

    if violations:
        detail = "\n".join(violations)
        raise SystemExit(f"Documentation link/image check failed:\n{detail}")


def _iter_markdown_files(roots: list[Path]) -> Generator[Path, None, None]:
    for root in roots:
        if not root.exists():
            continue
        if root.is_file() and root.suffix.lower() == ".md":
            yield root
            continue
        if root.is_dir():
            yield from sorted(
                path
                for path in root.rglob("*.md")
                if path.is_file() and not DOC_CHECK_EXCLUDED_DIRS.intersection(path.parts)
            )


def _markdown_targets(text: str) -> Generator[tuple[bool, str], None, None]:
    for match in MARKDOWN_LINK_RE.finditer(text):
        raw_target = match.group(3).strip()
        if not raw_target:
            continue
        if raw_target.startswith("<") and raw_target.endswith(">"):
            raw_target = raw_target[1:-1].strip()
        yield bool(match.group(1)), raw_target


def _validate_local_target(source_path: Path, target: str, target_kind: str) -> list[str]:
    parsed = urlsplit(target)
    if parsed.scheme in REMOTE_SCHEMES:
        return []
    if parsed.scheme and parsed.scheme not in {"file"}:
        return []
    if target.startswith("#"):
        target_path = source_path
        fragment = target[1:]
    else:
        local_path = unquote(parsed.path)
        if not local_path:
            return []
        target_path = (source_path.parent / local_path).resolve()
        fragment = parsed.fragment
    if not target_path.exists():
        return [f"{source_path}: broken local {target_kind} target {target}"]
    if fragment and target_path.suffix.lower() == ".md":
        anchors = _markdown_anchors(target_path)
        if fragment not in anchors:
            return [f"{source_path}: broken local {target_kind} anchor {target}"]
    return []


def _markdown_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        base = _github_anchor(match.group(1))
        count = counts.get(base, 0)
        counts[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def _github_anchor(heading: str) -> str:
    heading = re.sub(r"`([^`]+)`", r"\1", heading)
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading)
    heading = heading.strip().casefold()
    heading = re.sub(r"[^\w\s-]", "", heading, flags=re.UNICODE)
    heading = re.sub(r"\s+", "-", heading)
    heading = re.sub(r"-+", "-", heading).strip("-")
    return heading


def check_no_stale_workflow_refs(roots: list[Path] | None = None) -> None:
    scan_roots = roots or STALE_WORKFLOW_CHECK_ROOTS
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
        DIRECT_PYTHON_WITH_PYTHONPATH_RE,
    ]

    def iter_files(path: Path) -> Generator[Path, None, None]:
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
            if "plans" in path.parts and "reviews" in path.parts:
                # Review artifacts can quote previous failing commands as evidence.
                continue
            if "superpowers" in path.parts:
                # Internal agent-authored planning docs are not operational guides.
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            logical_text = re.sub(r"\\\s*\n\s*", " ", text)
            if DIRECT_PYTHON_WITH_PYTHONPATH_RE.search(logical_text):
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
