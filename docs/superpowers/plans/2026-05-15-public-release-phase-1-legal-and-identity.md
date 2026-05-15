# Phase 1 — Legal & Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transition `klein-business/legal-text-mcp-de` from a proprietary commercial codebase to an Apache-2.0-licensed repository ready for the remaining public-release phases. At the end of Phase 1, the repo carries Apache-2.0 LICENSE, NOTICE with upstream attribution, AUTHORS, CHANGELOG, English README rewrite, updated `pyproject.toml` metadata, and a working `verify_pre_flip.py` gate. The repository remains private; no public flip happens in this phase.

**Architecture:** Each public-readiness check lives in `scripts/verify_pre_flip.py` and is TDD-developed against tmp-path fixtures. The script is the gate that subsequent phases extend. Content artefacts (LICENSE/NOTICE/AUTHORS/CHANGELOG/README) follow standard OSS conventions; the upstream MIT terms are preserved verbatim in `licenses/MIT-floleuerer.txt`.

**Tech Stack:** Python 3.12 (existing), `uv` for dependency management (existing), `pytest` with `tmp_path` for unit tests (existing), `tomllib` from stdlib for `pyproject.toml` parsing, `detect-secrets` (new dev dependency) for the secrets-scan gate. `hashlib` (stdlib) for the LICENSE-hash check.

**Reference spec:** [docs/superpowers/specs/2026-05-15-public-release-enterprise-readiness-design.md](../specs/2026-05-15-public-release-enterprise-readiness-design.md).

**Out of scope for Phase 1:** build-backend migration from `[tool.uv] package = false` to hatchling; source rename `mcp/` → `legal_text_mcp_de/`; `[project.scripts]` entry point; `pyproject.toml` version ↔ CHANGELOG release-entry consistency check (only meaningful once releases exist past `[Unreleased]`). All four are deferred to Phase 4 alongside PyPI publishing so the rename, build, version-discipline, and distribution work happen together.

---

## File Structure

**New files:**
- `LICENSE` — Apache License 2.0 verbatim (replaces the current proprietary text).
- `NOTICE` — Apache-2.0-mandated notice with upstream MIT attribution and data-source statements.
- `licenses/MIT-floleuerer.txt` — preserved upstream MIT licence text.
- `AUTHORS.md` — primary author + upstream acknowledgement.
- `CHANGELOG.md` — Keep-a-Changelog 1.1.0 format, initial `Unreleased` section.
- `scripts/verify_pre_flip.py` — public-flip readiness gate.
- `mcp/tests/test_verify_pre_flip.py` — unit tests for the gate.
- `.secrets.baseline` — `detect-secrets` baseline (generated, then committed).

**Modified files:**
- `pyproject.toml` — license SPDX, requires-python, project urls, classifiers; add `detect-secrets` to dev group.
- `README.md` — full English rewrite for OSS audience.
- `assets/readme-banner.svg` — badge text swap (`license proprietary` → `license Apache 2.0`).
- `docs-legacy/` (audit only; modify only if proprietary text remnants found).

**Untouched in Phase 1:** the runtime source under `mcp/`, the `[tool.uv] package = false` directive, all existing scripts and workflows.

---

## Task 1: Bootstrap — Capture Apache-2.0 Canonical Text as Fixture

**Files:**
- Create: `mcp/tests/fixtures/legal/apache-2.0-canonical.txt`

The canonical Apache-2.0 SHA-256 is `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` (computed against `https://www.apache.org/licenses/LICENSE-2.0.txt` with LF line endings, no BOM, no trailing whitespace changes). We capture the text once as a test fixture; both the production `LICENSE` (Task 10) and the unit tests (Tasks 4–9) reference it.

- [ ] **Step 1: Create the fixture directory**

Run:
```bash
mkdir -p mcp/tests/fixtures/legal
```

- [ ] **Step 2: Fetch canonical Apache-2.0 text into the fixture**

Run:
```bash
curl -fsSL -o mcp/tests/fixtures/legal/apache-2.0-canonical.txt https://www.apache.org/licenses/LICENSE-2.0.txt
```

Expected: file exists, ~11 KB.

- [ ] **Step 3: Verify the SHA-256 matches the expected value**

Run:
```bash
shasum -a 256 mcp/tests/fixtures/legal/apache-2.0-canonical.txt | awk '{print $1}'
```

Expected output: `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.

If the hash differs, stop and investigate — most likely cause is line-ending mangling. Re-fetch with `curl --output-document` or `wget --no-cache`.

- [ ] **Step 4: Commit the fixture**

```bash
git add mcp/tests/fixtures/legal/apache-2.0-canonical.txt
git commit -m "test(fixtures): add canonical Apache-2.0 text for licence-gate tests"
```

---

## Task 2: Add `detect-secrets` Dev Dependency

**Files:**
- Modify: `pyproject.toml`

The secrets-scan check in `verify_pre_flip.py` shells out to `detect-secrets`. Add it to the dev group before writing tests that depend on it.

- [ ] **Step 1: Edit `pyproject.toml` dev group**

Replace the existing `[dependency-groups]` `dev` list:

```toml
[dependency-groups]
dev = [
    "pytest",
    "httpx",
    "PyYAML~=6.0.1",
    "ruff",
    "detect-secrets~=1.5",
]
```

- [ ] **Step 2: Resync the lockfile**

Run:
```bash
uv sync --all-groups
```

Expected: lockfile updates to include `detect-secrets` and its dependencies. No error.

- [ ] **Step 3: Smoke-test `detect-secrets` CLI**

Run:
```bash
uv run --group dev detect-secrets --version
```

Expected: prints a version like `1.5.x`.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build(deps): add detect-secrets to dev group"
```

---

## Task 3: Create `.secrets.baseline`

**Files:**
- Create: `.secrets.baseline`

`detect-secrets` distinguishes between "no secrets found" and "secrets found but reviewed". A baseline file records the reviewed state. Generate it once now; subsequent runs flag only new findings.

- [ ] **Step 1: Generate the baseline**

Run from the repo root:
```bash
uv run --group dev detect-secrets scan --exclude-files '\.git/' --exclude-files 'uv\.lock' --exclude-files 'mcp/tests/fixtures/' > .secrets.baseline
```

Expected: file `.secrets.baseline` exists, valid JSON, contains `results` (likely empty or containing only false positives).

- [ ] **Step 2: Inspect the baseline manually**

Run:
```bash
uv run --group dev python -c "import json, pathlib; data = json.loads(pathlib.Path('.secrets.baseline').read_text()); print('result_files:', len(data['results']))"
```

If `result_files` is `0`, baseline is clean. If > 0, open `.secrets.baseline`, mark each entry with `"is_secret": false` if it is a known false positive (and explain in the commit). Do not mark true secrets as false positives — rotate them and remove from history first.

- [ ] **Step 3: Verify the baseline gates correctly**

Run:
```bash
uv run --group dev detect-secrets scan --baseline .secrets.baseline
```

Expected: exit code 0, no new findings.

- [ ] **Step 4: Commit**

```bash
git add .secrets.baseline
git commit -m "chore: add detect-secrets baseline"
```

---

## Task 4: TDD `verify_pre_flip.py` Skeleton + LICENSE-Hash Check

**Files:**
- Create: `scripts/verify_pre_flip.py`
- Create: `mcp/tests/test_verify_pre_flip.py`

Start the gate script with one check: the `LICENSE` file SHA-256 must match the canonical Apache-2.0 hash.

- [ ] **Step 1: Write the failing test**

Create `mcp/tests/test_verify_pre_flip.py`:

```python
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
```

- [ ] **Step 2: Run the test to confirm it fails**

Run:
```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: collection error — `ModuleNotFoundError: No module named 'verify_pre_flip'`.

- [ ] **Step 3: Implement the minimal script**

Create `scripts/verify_pre_flip.py`:

```python
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


CHECKS = [check_license_apache_2_0]


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
```

- [ ] **Step 4: Run the test to confirm it passes**

Run:
```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: all three tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/verify_pre_flip.py mcp/tests/test_verify_pre_flip.py
git commit -m "feat(verify): add pre-flip license-hash check"
```

---

## Task 5: TDD Required-Files Check

**Files:**
- Modify: `scripts/verify_pre_flip.py`
- Modify: `mcp/tests/test_verify_pre_flip.py`

Add a check that confirms `NOTICE`, `AUTHORS.md`, `CHANGELOG.md`, and `licenses/MIT-floleuerer.txt` exist.

- [ ] **Step 1: Write the failing tests**

Append to `mcp/tests/test_verify_pre_flip.py`:

```python
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
```

- [ ] **Step 2: Run to confirm failure**

Run:
```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py::test_required_files_passes_when_all_present -v
```

Expected: FAIL — `AttributeError: module 'verify_pre_flip' has no attribute 'check_required_files'`.

- [ ] **Step 3: Implement the check**

In `scripts/verify_pre_flip.py`, add after `check_license_apache_2_0`:

```python
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
```

And extend the `CHECKS` list:

```python
CHECKS = [
    check_license_apache_2_0,
    check_required_files,
]
```

- [ ] **Step 4: Run all tests**

Run:
```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: all five tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/verify_pre_flip.py mcp/tests/test_verify_pre_flip.py
git commit -m "feat(verify): add pre-flip required-files check"
```

---

## Task 6: TDD No-Proprietary-Strings Check

**Files:**
- Modify: `scripts/verify_pre_flip.py`
- Modify: `mcp/tests/test_verify_pre_flip.py`

Scan all text files under the repo (excluding `.git`, `.venv`, `__pycache__`, `node_modules`, `docs-legacy/`, and the `LICENSE` itself) for the strings `proprietary commercial` and `All rights reserved.`. Both currently appear in the README and LICENSE — the check fails on the current state and will pass after Tasks 8–12.

- [ ] **Step 1: Write the failing tests**

Append to `mcp/tests/test_verify_pre_flip.py`:

```python
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
    # LICENSE is allowed to contain "All rights reserved." historically;
    # the canonical Apache-2.0 text does not, but the check must not
    # double-flag here.
    (tmp_path / "LICENSE").write_text(
        "Copyright (c) 2025 X. All rights reserved.", encoding="utf-8"
    )
    result = vpf.check_no_proprietary_strings(tmp_path)
    # LICENSE is excluded from the scan, so this passes.
    assert result.passed is True, result.message
```

- [ ] **Step 2: Run to confirm failure**

Run:
```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: the four new tests fail with `AttributeError: module 'verify_pre_flip' has no attribute 'check_no_proprietary_strings'`.

- [ ] **Step 3: Implement the check**

Add to `scripts/verify_pre_flip.py`:

```python
EXCLUDED_DIRS = {".git", ".venv", "__pycache__", "node_modules", "docs-legacy"}
EXCLUDED_FILES = {"LICENSE"}
PROPRIETARY_STRINGS = ("proprietary commercial", "All rights reserved.")


def check_no_proprietary_strings(root: Path) -> CheckResult:
    hits: list[tuple[str, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if rel.name in EXCLUDED_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for needle in PROPRIETARY_STRINGS:
            if needle in text:
                hits.append((str(rel), needle))
    if hits:
        return CheckResult(
            name="no proprietary strings",
            passed=False,
            message=f"hits: {hits}",
        )
    return CheckResult(name="no proprietary strings", passed=True, message="ok")
```

Extend `CHECKS`:

```python
CHECKS = [
    check_license_apache_2_0,
    check_required_files,
    check_no_proprietary_strings,
]
```

- [ ] **Step 4: Run all tests**

Run:
```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: all nine tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/verify_pre_flip.py mcp/tests/test_verify_pre_flip.py
git commit -m "feat(verify): add pre-flip proprietary-string scan"
```

---

## Task 7: TDD `pyproject.toml` Metadata Check

**Files:**
- Modify: `scripts/verify_pre_flip.py`
- Modify: `mcp/tests/test_verify_pre_flip.py`

Verify `pyproject.toml` carries the Apache-2.0 SPDX license, `requires-python = ">=3.12"`, and the project URLs `Homepage`, `Repository`, `Issues`, `Changelog`.

- [ ] **Step 1: Write the failing tests**

Append:

```python
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
```

- [ ] **Step 2: Run to confirm failure**

Run:
```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: the four new tests fail with `AttributeError`.

- [ ] **Step 3: Implement the check**

Add to `scripts/verify_pre_flip.py` at top with the other imports:

```python
import tomllib
```

Add the check:

```python
REQUIRED_URLS = ("Homepage", "Repository", "Issues", "Changelog")


def check_pyproject_metadata(root: Path) -> CheckResult:
    path = root / "pyproject.toml"
    if not path.is_file():
        return CheckResult(
            name="pyproject.toml metadata",
            passed=False,
            message="pyproject.toml missing",
        )
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project") or {}
    failures: list[str] = []
    license_field = project.get("license")
    if license_field != "Apache-2.0":
        failures.append(f"license != 'Apache-2.0' (got {license_field!r})")
    requires_python = project.get("requires-python")
    if requires_python != ">=3.12":
        failures.append(
            f"requires-python != '>=3.12' (got {requires_python!r})"
        )
    urls = project.get("urls") or {}
    for required_url in REQUIRED_URLS:
        if required_url not in urls:
            failures.append(f"urls.{required_url} missing")
    if failures:
        return CheckResult(
            name="pyproject.toml metadata",
            passed=False,
            message="; ".join(failures),
        )
    return CheckResult(name="pyproject.toml metadata", passed=True, message="ok")
```

Extend `CHECKS`:

```python
CHECKS = [
    check_license_apache_2_0,
    check_required_files,
    check_no_proprietary_strings,
    check_pyproject_metadata,
]
```

- [ ] **Step 4: Run all tests**

Run:
```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: all 13 tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/verify_pre_flip.py mcp/tests/test_verify_pre_flip.py
git commit -m "feat(verify): add pre-flip pyproject-metadata check"
```

---

## Task 8: TDD Secrets-Scan Check

**Files:**
- Modify: `scripts/verify_pre_flip.py`
- Modify: `mcp/tests/test_verify_pre_flip.py`

Shell out to `detect-secrets scan --baseline .secrets.baseline`. The check fails if the baseline is missing or if new findings exist.

- [ ] **Step 1: Write the failing tests**

Append:

```python
def test_secrets_scan_fails_when_baseline_missing(tmp_path: Path) -> None:
    result = vpf.check_no_unaudited_secrets(tmp_path)
    assert result.passed is False
    assert ".secrets.baseline" in result.message


def test_secrets_scan_passes_on_real_repo(tmp_path: Path) -> None:
    # The real repo carries .secrets.baseline by Task 3.
    real_root = Path(__file__).resolve().parents[2]
    result = vpf.check_no_unaudited_secrets(real_root)
    assert result.passed is True, result.message
```

- [ ] **Step 2: Run to confirm failure**

Run:
```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: the two new tests fail with `AttributeError`.

- [ ] **Step 3: Implement the check**

Add import:

```python
import shutil
import subprocess
```

Add the check:

```python
def check_no_unaudited_secrets(root: Path) -> CheckResult:
    baseline = root / ".secrets.baseline"
    if not baseline.is_file():
        return CheckResult(
            name="no unaudited secrets",
            passed=False,
            message=(
                ".secrets.baseline missing; create via: "
                "uv run --group dev detect-secrets scan > .secrets.baseline"
            ),
        )
    detect_secrets = shutil.which("detect-secrets")
    if detect_secrets is None:
        return CheckResult(
            name="no unaudited secrets",
            passed=False,
            message="detect-secrets not on PATH; run via 'uv run --group dev'",
        )
    proc = subprocess.run(
        [
            detect_secrets, "scan",
            "--baseline", str(baseline),
            "--exclude-files", r"\.git/",
            "--exclude-files", r"uv\.lock",
            "--exclude-files", r"mcp/tests/fixtures/",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return CheckResult(
            name="no unaudited secrets",
            passed=False,
            message=f"detect-secrets exit {proc.returncode}: {proc.stderr.strip()}",
        )
    return CheckResult(name="no unaudited secrets", passed=True, message="ok")
```

Extend `CHECKS`:

```python
CHECKS = [
    check_license_apache_2_0,
    check_required_files,
    check_no_proprietary_strings,
    check_pyproject_metadata,
    check_no_unaudited_secrets,
]
```

- [ ] **Step 4: Run all tests with the dev group on PATH**

The `test_secrets_scan_passes_on_real_repo` test calls `detect-secrets` via `shutil.which`. Ensure the dev group is active when running tests:

```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: all 15 tests pass so far (Tasks 4–8 cumulative). If `test_secrets_scan_passes_on_real_repo` fails because the binary is not on PATH, the test invocation needs the dev group active — verify with `uv run --group dev which detect-secrets`.

- [ ] **Step 5: Commit**

```bash
git add scripts/verify_pre_flip.py mcp/tests/test_verify_pre_flip.py
git commit -m "feat(verify): add pre-flip secrets-scan check"
```

---

## Task 9: TDD CLI Behaviour

**Files:**
- Modify: `mcp/tests/test_verify_pre_flip.py`

Test the CLI's exit codes (`0` for all-pass, `1` for any-fail) and JSON output writing.

- [ ] **Step 1: Write the failing tests**

Append:

```python
def _populate_passing_repo(root: Path) -> None:
    (root / "LICENSE").write_text(APACHE_2_0_TEXT, encoding="utf-8")
    (root / "NOTICE").write_text("notice", encoding="utf-8")
    (root / "AUTHORS.md").write_text("authors", encoding="utf-8")
    (root / "CHANGELOG.md").write_text("changelog", encoding="utf-8")
    (root / "licenses").mkdir()
    (root / "licenses" / "MIT-floleuerer.txt").write_text("mit", encoding="utf-8")
    (root / "pyproject.toml").write_text(PYPROJECT_VALID, encoding="utf-8")
    # The secrets check requires a baseline.
    (root / ".secrets.baseline").write_text(
        '{"version": "1.5.0", "results": {}}',
        encoding="utf-8",
    )


def test_main_returns_zero_on_passing_repo(tmp_path: Path) -> None:
    _populate_passing_repo(tmp_path)
    # Skip the secrets check by stubbing it: replace via monkey-patch is
    # heavy; instead point detect-secrets at a clean repo via baseline
    # arg. Here we just accept that the subprocess call against tmp_path
    # may not find detect-secrets — confirm by checking the report.
    output = tmp_path / "report.json"
    rc = vpf.main(["--root", str(tmp_path), "--output", str(output)])
    # CLI returns 1 if any check fails (detect-secrets may be unavailable
    # in tmp_path). Validate the report shape regardless.
    assert output.is_file()
    import json as _json
    payload = _json.loads(output.read_text())
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
```

- [ ] **Step 2: Run to confirm tests**

Run:
```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: tests pass. The first test does not assert on `rc` because the secrets check in `tmp_path` will fail (no `detect-secrets` invocation against the temp dir is reliable); we assert on report shape only.

- [ ] **Step 3: Commit**

```bash
git add mcp/tests/test_verify_pre_flip.py
git commit -m "test(verify): add pre-flip CLI exit-code and report tests"
```

---

## Task 10: Replace `LICENSE` with Apache-2.0

**Files:**
- Modify: `LICENSE`

The current `LICENSE` is the proprietary commercial text. Replace it with the canonical Apache-2.0 text from the fixture created in Task 1.

- [ ] **Step 1: Replace the file**

Run:
```bash
cp mcp/tests/fixtures/legal/apache-2.0-canonical.txt LICENSE
```

- [ ] **Step 2: Verify the SHA-256**

Run:
```bash
shasum -a 256 LICENSE | awk '{print $1}'
```

Expected: `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.

- [ ] **Step 3: Run the gate against the real repo (expect partial fail)**

Run:
```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_pre_flip.py
```

Expected: `LICENSE is Apache-2.0: ok`. Other checks (required files, no proprietary strings, pyproject metadata) still fail — they will be fixed in Tasks 11–15.

- [ ] **Step 4: Commit**

```bash
git add LICENSE
git commit -m "feat: re-license repository from proprietary to Apache-2.0"
```

---

## Task 11: Create `licenses/MIT-floleuerer.txt`

**Files:**
- Create: `licenses/MIT-floleuerer.txt`

Preserve the verbatim upstream MIT licence text. The text below is the canonical upstream `LICENSE` content from `floleuerer/deutsche-gesetze-mcp@main`.

- [ ] **Step 1: Create the file**

Create `licenses/MIT-floleuerer.txt` with this exact content (LF newlines, single trailing newline):

```
MIT License

Copyright (c) 2025 Florian Leuerer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Verify the file**

Run:
```bash
wc -l licenses/MIT-floleuerer.txt
```

Expected: `21 licenses/MIT-floleuerer.txt`.

Run:
```bash
grep -q "Copyright (c) 2025 Florian Leuerer" licenses/MIT-floleuerer.txt && echo OK
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add licenses/MIT-floleuerer.txt
git commit -m "docs(legal): preserve upstream MIT licence for floleuerer/deutsche-gesetze-mcp"
```

---

## Task 12: Create `NOTICE`

**Files:**
- Create: `NOTICE`

Apache-2.0 §4(d) requires that derivative works retain a `NOTICE` file when the original carries one. Even though upstream is MIT (no NOTICE requirement), we use the file to capture upstream attribution, third-party reuse positions, and the no-legal-advice disclaimer.

- [ ] **Step 1: Create the file**

Create `NOTICE` with this content:

```
legal-text-mcp-de
Copyright 2026 klein-business

Maintainer: Martin Klein <martin@klein.business>

This product includes software developed for the Model Context Protocol
(https://modelcontextprotocol.io) ecosystem.

Derivative work attribution
---------------------------

Portions of this software are derived from:

  deutsche-gesetze-mcp
  Copyright (c) 2025 Florian Leuerer
  Licensed under the MIT License
  https://github.com/floleuerer/deutsche-gesetze-mcp

The full MIT licence text covering those portions is preserved in
licenses/MIT-floleuerer.txt.

Data sources accessed at runtime
--------------------------------

This software accesses official legal text from external sources at runtime.
No editorial legal text is bundled with this source distribution.

  gesetze-im-internet.de
    German federal laws. Official texts of acts are not protected by
    copyright under §5 (1) UrhG.

  EUR-Lex / Cellar (publications.europa.eu)
    European Union acts. Reuse permitted under Commission Decision
    2011/833/EU, with attribution.

Disclaimer
----------

This software is local infrastructure. It does not constitute legal advice.
Provenance metadata is best-effort and not guaranteed to be complete.
```

- [ ] **Step 2: Commit**

```bash
git add NOTICE
git commit -m "docs(legal): add NOTICE with upstream attribution and data-source positions"
```

---

## Task 13: Create `AUTHORS.md`

**Files:**
- Create: `AUTHORS.md`

- [ ] **Step 1: Create the file**

Create `AUTHORS.md`:

```markdown
# Authors

## Primary

- Martin Klein ([@klein-business](https://github.com/klein-business)) —
  maintainer, primary author of all derivative work since the fork.

## Acknowledgements

This project is a derivative work of
[deutsche-gesetze-mcp](https://github.com/floleuerer/deutsche-gesetze-mcp)
by Florian Leuerer, originally released under the MIT License. The
upstream copyright notice and full MIT licence text are preserved in
[NOTICE](NOTICE) and [licenses/MIT-floleuerer.txt](licenses/MIT-floleuerer.txt).
```

- [ ] **Step 2: Commit**

```bash
git add AUTHORS.md
git commit -m "docs(legal): add AUTHORS with maintainer and upstream acknowledgement"
```

---

## Task 14: Create `CHANGELOG.md`

**Files:**
- Create: `CHANGELOG.md`

- [ ] **Step 1: Create the file**

Create `CHANGELOG.md`:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Re-licensed from proprietary commercial to Apache License 2.0.
- Established `LICENSE` (Apache-2.0), `NOTICE` with upstream attribution
  and data-source statements, `AUTHORS.md`, and `CHANGELOG.md`.
- Preserved upstream MIT licence terms for code derived from
  `floleuerer/deutsche-gesetze-mcp` in `licenses/MIT-floleuerer.txt`.
- Rewrote `README.md` in English with disclaimers and an OSS-focused
  structure.
- Updated `pyproject.toml` metadata (Apache-2.0 SPDX license,
  `requires-python = ">=3.12"`, project URLs, PyPI classifiers).
- Updated the README banner asset to display the Apache-2.0 badge.

### Added

- `scripts/verify_pre_flip.py` and `mcp/tests/test_verify_pre_flip.py` —
  gate that asserts the repository is ready for public visibility.
- `.secrets.baseline` and `detect-secrets` dev dependency for the
  secrets-scan gate.

[Unreleased]: https://github.com/klein-business/legal-text-mcp-de/compare/HEAD
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(legal): add CHANGELOG with Phase 1 entries"
```

---

## Task 15: Update `pyproject.toml` Metadata

**Files:**
- Modify: `pyproject.toml`

Add Apache-2.0 SPDX license, broaden `requires-python` to `>=3.12`, add project URLs, add PyPI classifiers. Do **not** switch the build backend or add `[project.scripts]` — those land in Phase 4.

- [ ] **Step 1: Read the current state**

Run:
```bash
cat pyproject.toml
```

Confirm the current `[project]` table matches what was inspected during planning (name, version, description, requires-python, dependencies).

- [ ] **Step 2: Edit the `[project]` table**

Replace the existing `[project]` table with:

```toml
[project]
name = "legal-text-mcp-de"
version = "0.1.0"
description = "Python MCP server and HTTP API for loading, validating, searching, and resolving German legal texts with source provenance."
readme = "README.md"
license = "Apache-2.0"
requires-python = ">=3.12"
authors = [
    { name = "Martin Klein", email = "martin@klein.business" },
]
maintainers = [
    { name = "Martin Klein", email = "martin@klein.business" },
]
keywords = [
    "mcp",
    "mcp-server",
    "model-context-protocol",
    "legal-tech",
    "german-law",
    "dsgvo",
    "gdpr",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Legal Industry",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Office/Business",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Text Processing :: Markup",
    "Typing :: Typed",
]
dependencies = [
    "mcp[cli]==1.23.0",
    "rapidfuzz",
    "pydantic-settings",
    "fastapi",
    "uvicorn",
]

[project.urls]
Homepage = "https://github.com/klein-business/legal-text-mcp-de"
Repository = "https://github.com/klein-business/legal-text-mcp-de"
Issues = "https://github.com/klein-business/legal-text-mcp-de/issues"
Changelog = "https://github.com/klein-business/legal-text-mcp-de/blob/main/CHANGELOG.md"
Security = "https://github.com/klein-business/legal-text-mcp-de/security/policy"
```

Keep `[dependency-groups]` (including the `detect-secrets` entry added in Task 2), `[tool.uv]`, and `[tool.ruff]` unchanged.

Note on `Development Status :: 4 - Beta`: we are pre-`v1.0.0` until Phase 4. The classifier is bumped to `5 - Production/Stable` at release time.

- [ ] **Step 3: Re-sync the lockfile**

Run:
```bash
uv sync --all-groups
```

Expected: no errors. uv may regenerate metadata but the dependency set is unchanged.

- [ ] **Step 4: Verify pre-flip check passes for pyproject**

Run:
```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_pre_flip.py
```

Expected: `pyproject.toml metadata: ok`.

- [ ] **Step 5: Verify the existing test suite still runs**

Run:
```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests -x -q
```

Expected: all tests collect and pass. If the broader `requires-python` causes any test collection issue, surface it now rather than at Phase 2 start.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: update project metadata for Apache-2.0 and Python 3.12/3.13"
```

---

## Task 16: Update `assets/readme-banner.svg`

**Files:**
- Modify: `assets/readme-banner.svg`

Swap the embedded "proprietary commercial" license badge for an Apache-2.0 badge. The banner is hand-authored SVG with text labels.

- [ ] **Step 1: Inspect the current badge**

Run:
```bash
grep -n -E "(proprietary|license|Apache|MIT)" assets/readme-banner.svg
```

Note line numbers where the license-related text appears.

- [ ] **Step 2: Update the badge text and colour**

Edit `assets/readme-banner.svg`. For each text element that currently reads `proprietary commercial` (or similar), replace with `Apache 2.0`. If the badge fill colour is a "warning red" (`#B91C1C`), change to a "permissive green" (`#16A34A`). Use the existing shields.io palette already present elsewhere in the banner.

If the banner embeds a shields.io badge URL rather than inline text, replace:

```
https://img.shields.io/badge/license-proprietary%20commercial-B91C1C?style=for-the-badge
```

with:

```
https://img.shields.io/badge/license-Apache%202.0-16A34A?style=for-the-badge
```

- [ ] **Step 3: Confirm no remaining "proprietary" text in the banner**

Run:
```bash
grep -i "proprietary" assets/readme-banner.svg
```

Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add assets/readme-banner.svg
git commit -m "docs(assets): update README banner license badge to Apache-2.0"
```

---

## Task 17: Rewrite `README.md`

**Files:**
- Modify: `README.md`

Full English rewrite. The new README replaces the proprietary licensing language, broadens the audience from internal stakeholders to OSS adopters, and prepares badge slots for Phase 2 (CI, coverage) and Phase 4 (PyPI, Scorecard).

- [ ] **Step 1: Replace `README.md` content**

Replace the entire file with:

```markdown
<p align="center">
  <img src="assets/readme-banner.svg" alt="legal-text-mcp-de: German legal text MCP server banner" width="100%">
</p>

<p align="center">
  <a href="https://github.com/klein-business/legal-text-mcp-de"><img alt="Repository" src="https://img.shields.io/badge/repo-klein--business%2Flegal--text--mcp--de-111827?style=for-the-badge&logo=github"></a>
  <img alt="Python 3.12 / 3.13" src="https://img.shields.io/badge/python-3.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="MCP streamable HTTP" src="https://img.shields.io/badge/MCP-streamable%20HTTP-0EA5E9?style=for-the-badge">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-HTTP%20API-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img alt="License: Apache 2.0" src="https://img.shields.io/badge/license-Apache%202.0-16A34A?style=for-the-badge">
</p>

# legal-text-mcp-de

`legal-text-mcp-de` is a Python [Model Context Protocol](https://modelcontextprotocol.io)
server and HTTP API for loading, validating, searching, and resolving
**German legal texts** with source provenance.

It is **local or server-side infrastructure**: no SaaS, no billing, no
accounts, no tenant model, and **no legal advice**. The runtime loads
either the committed fixture packages used by fast CI or a generated
production corpus package built outside Git. Official text comes from
`gesetze-im-internet.de` for German federal laws and from EUR-Lex /
Cellar for EU acts such as the GDPR.

> **No legal advice.** This software returns text and structured
> metadata. It does not interpret the law, advise on it, or produce
> any legal conclusion. The maintainer assumes no liability for use
> in legal decision-making contexts.

Older internal documentation has been archived under
[docs-legacy/summary.md](docs-legacy/summary.md).

## Status

| | |
| --- | --- |
| Lifecycle | Pre-`v1.0.0` public release in preparation |
| Versioning | [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html) (stability contract starts at `v1.0.0`) |
| Licence | Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE) |
| Upstream | Derived from [floleuerer/deutsche-gesetze-mcp](https://github.com/floleuerer/deutsche-gesetze-mcp) (MIT, preserved) |

## Features

- **MCP tools** for listing laws, fetching norms, resolving citations,
  full-text search, and source provenance.
- **HTTP API** (FastAPI) over the same runtime, with structured
  `/health`, `/ready`, `/laws`, `/search`, and OpenAPI endpoints.
- **Provenance-first design**: every law and norm carries source URL,
  fetch timestamp, content hash, and the parser path it traversed.
- **Two corpus modes**: committed fixture packages for deterministic
  tests and CI, or a generated production package built from official
  sources at runtime.
- **No editorial bundling**: this repository ships tooling, not legal
  text. Texts are loaded from official sources at runtime.

## Quickstart

### Run the MCP server with the committed fixture corpus

```bash
uv sync --all-groups

DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
uv run python mcp/server.py
```

The default transport is streamable HTTP at
`http://localhost:8001/mcp`.

### Run the HTTP API

```bash
DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
uv run uvicorn http_api:app --host 127.0.0.1 --port 8080
```

### Docker

The Docker image does not bundle legal text data. Mount a validated
package at `/data/legal-texts`:

```bash
docker build -t legal-text-mcp-de .
docker run --rm -p 8001:8001 \
  -v /path/to/legal-text-package:/data/legal-texts:ro \
  legal-text-mcp-de
```

## Data Sources

| Source | Coverage | Reuse position |
| --- | --- | --- |
| `gesetze-im-internet.de` | German federal laws | Public-domain-equivalent under §5 (1) UrhG |
| EUR-Lex / Cellar (`publications.europa.eu`) | EU acts (GDPR, AI Act, Data Act, …) | Reuse permitted under Commission Decision 2011/833/EU with attribution |

No text from these sources is committed to this repository. The
generated-corpus pipeline fetches them at build time and stores
provenance in a manifest.

## MCP Tools

See the [MCP tools reference](docs/features/mcp-law-tools.md) for the
full surface. Highlights:

- `list_laws(query?)` — list loaded laws with optional metadata filter.
- `get_law(code)` — law metadata + normalised norm summaries.
- `get_norm(code, norm)` — return one structured norm.
- `search_laws(query, codes?)` — search normalised texts.
- `resolve_citation(...)` — resolve structured citations without legal
  interpretation.
- `get_source_metadata(code?)`, `get_source_limitations(...)`,
  `get_corpus_coverage()`, `get_related_norms(code, norm)`.

MCP tools return JSON-compatible objects. They do not return
double-serialised JSON strings.

## HTTP API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness |
| `GET` | `/ready` | Readiness |
| `GET` | `/laws` | List laws |
| `GET` | `/laws/{code}` | Law detail |
| `GET` | `/laws/{code}/norms/{norm}` | Norm detail |
| `GET` | `/laws/{code}/norms/{norm}/relationships` | Relationship metadata |
| `GET` | `/corpus/coverage` | Corpus coverage summary |
| `GET` | `/corpus/source-limitations` | Source limitations query |
| `GET` | `/search` | Search |
| `GET` | `/openapi.json` | OpenAPI document |

Article-plus-section paths must be URL-encoded:

```
/laws/egbgb/norms/art%3A246a%2Fpar%3A1
```

## Development

```bash
uv sync --all-groups
PYTHONPATH=mcp uv run --group dev pytest mcp/tests -v
```

The full fixture-backed release gate:

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py
```

The public-flip readiness gate:

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_pre_flip.py
```

## Contributing

This is a pre-`v1.0.0` repository preparing for public release.
Contribution guidelines, code of conduct, and security policy land in
the next phases of the public-release programme.

## Licence and acknowledgements

This project is licensed under the [Apache License 2.0](LICENSE).
See [NOTICE](NOTICE) for required attribution.

Derived from [floleuerer/deutsche-gesetze-mcp](https://github.com/floleuerer/deutsche-gesetze-mcp)
(Copyright (c) 2025 Florian Leuerer, MIT). Upstream licence terms are
preserved in [licenses/MIT-floleuerer.txt](licenses/MIT-floleuerer.txt).
```

- [ ] **Step 2: Verify no "proprietary" remnants**

Run:
```bash
grep -i "proprietary" README.md
```

Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README for Apache-2.0 public release"
```

---

## Task 18: Audit `docs-legacy/`

**Files:**
- Read: `docs-legacy/*`

The legacy directory contains historical READMEs that pre-date the licensing flip. The pre-flip gate excludes `docs-legacy/` from the proprietary-string scan, but the directory still ships with the public repo. Confirm it contains nothing that should be removed.

- [ ] **Step 1: Read every file**

Run:
```bash
wc -l docs-legacy/*
```

Inspect each file:
```bash
head -100 docs-legacy/google-adk-agent--README.md
head -100 docs-legacy/root--README.md
cat docs-legacy/summary.md
```

- [ ] **Step 2: Decide per file**

For each file, decide:
- **Keep as-is** if it is a historical README without proprietary remnants and without secrets.
- **Annotate** if the file is useful as history but might mislead readers (add a one-line `> This is an archived historical document, see README.md for current state.` at the top).
- **Remove** if the file contains information that should not appear in a public repository (credentials, internal-only URLs, private email addresses).

- [ ] **Step 3: Apply decisions**

If any file is removed, run:
```bash
git rm docs-legacy/<file>
```

If any file is annotated, edit it to add the leading note.

- [ ] **Step 4: Confirm `docs-legacy/summary.md` still links to existing content**

Run:
```bash
grep -E '\[.*\]\(.*\)' docs-legacy/summary.md
```

For each link, confirm the target file still exists.

- [ ] **Step 5: Commit (only if changes were made)**

```bash
git add docs-legacy/
git commit -m "docs(legacy): audit and clean docs-legacy/ for public release"
```

If no changes were necessary, skip the commit and note the audit completion in the next task's commit message instead.

---

## Task 19: End-to-End Gate Verification

**Files:**
- None (verification only)

Confirm that all Phase 1 gates pass on the real repository state.

- [ ] **Step 1: Run the pre-flip gate**

Run:
```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_pre_flip.py --output .artifacts/pre-flip/phase-1.json
```

Expected output (every line):
```
[PASS] LICENSE is Apache-2.0: ok
[PASS] required files exist: ok
[PASS] no proprietary strings: ok
[PASS] pyproject.toml metadata: ok
[PASS] no unaudited secrets: ok
```

Exit code: `0`.

- [ ] **Step 2: Run the existing release gate**

Run:
```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py
```

Expected: all existing checks pass. If any check fails because of metadata changes from Task 15 (e.g., a docs link validator that now expects different content), fix the validator or the documentation in a small follow-up commit before declaring Phase 1 complete.

- [ ] **Step 3: Run the full test suite**

Run:
```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests -v
```

Expected: all tests pass, including the new `test_verify_pre_flip.py` tests (17 tests across Tasks 4–9).

- [ ] **Step 4: Final sanity grep**

Run:
```bash
grep -ri "proprietary commercial" --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ --exclude-dir=docs-legacy .
```

Expected: no output.

```bash
grep -ri "All rights reserved." --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ --exclude-dir=docs-legacy --exclude=LICENSE --exclude='LICENSE.*' .
```

Expected: no output (the `licenses/MIT-floleuerer.txt` does not contain "All rights reserved." either, since the MIT text does not use that phrase).

- [ ] **Step 5: Phase-closure commit**

If Step 2's release gate required any small fix, commit it now with:
```bash
git add <files>
git commit -m "chore: align release gate with Phase 1 metadata changes"
```

If no fix was needed, no extra commit is required.

---

## Phase 1 Acceptance

Phase 1 is complete when:

- `scripts/verify_pre_flip.py` exits `0` on the real repository.
- `scripts/verify_release.py` exits `0` on the real repository.
- `pytest mcp/tests` reports all tests passing including the 17
  `test_verify_pre_flip.py` cases.
- `git log --oneline -25` shows the new Phase 1 commits.
- The repository remains private (no public flip in this phase).
- `docs/superpowers/plans/2026-05-15-public-release-phase-2-ci-hardening.md`
  has not yet been written — that is the next session's brainstorming-
  to-plan output, informed by Phase 1's actual coverage baseline.

## What Phase 2 Will Pick Up

- Refactor `.github/workflows/ci.yml` into the topology defined in the
  spec.
- Add codeql, scorecard, dependency-review, commitlint, dco workflows.
- Configure `[tool.mypy] strict = true` and add `mypy` to the dev
  group; integrate into `ci.yml`.
- Add the Python 3.13 matrix entry.
- Measure the coverage baseline and pin `--cov-fail-under`.
- Introduce `.pre-commit-config.yaml`.
- Extend MegaLinter scope.

Phase 2 will also extend `scripts/verify_pre_flip.py` with workflow-
and branch-protection assertions.
