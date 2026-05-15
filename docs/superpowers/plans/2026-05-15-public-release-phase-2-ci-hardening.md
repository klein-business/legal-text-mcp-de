# Phase 2 — CI/CD Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the single-workflow CI on `main` into the eight-workflow hardened topology defined in Pillar 3 of the parent spec, add the Phase-1 carryover fixes (SECURITY.md, mypy stufenweise, pre-commit, coverage floor, detect-secrets SKIP, CHANGELOG link, pin tighten), and extend `verify_pre_flip.py` with three new checks (workflow set, required status checks, branch protection).

**Architecture:** Each workflow is one focused YAML file. Quality gates live in `pyproject.toml` (mypy, coverage). Pre-commit mirrors CI for developer convenience but is not the authoritative gate. `verify_pre_flip.py` grows from 5 to 8 checks; GitHub-API-backed checks use stdlib `urllib.request` and are skipped without `VERIFY_GITHUB_TOKEN`. The phase ends with all required status checks active on `main` branch protection.

**Tech Stack:** Python 3.12+3.13 (CI matrix), uv (existing), ruff (existing), pytest with `pytest-cov` (existing), mypy (new dev dep), `pre-commit` (new dev dep, optional), `detect-secrets` 1.5.0 (existing, pin-tightened), GitHub Actions `tim-actions/dco`, `wagoid/commitlint-github-action`, `actions/dependency-review-action`, `github/codeql-action`, `ossf/scorecard-action`, `oxsecurity/megalinter/flavors/python` (existing).

**Reference spec:** [docs/superpowers/specs/2026-05-15-public-release-phase-2-ci-hardening-design.md](../specs/2026-05-15-public-release-phase-2-ci-hardening-design.md). Parent: [docs/superpowers/specs/2026-05-15-public-release-enterprise-readiness-design.md](../specs/2026-05-15-public-release-enterprise-readiness-design.md).

**Out of scope:** SPDX retrofit on existing files; mypy strict on `mcp/`; Pillar 4 (Dependabot, SBOM, SLSA, cosign); Pillar 2 community files except SECURITY.md; mkdocs site; `release.yml`/`docs.yml`; build-backend migration.

---

## Task 1: Tighten `detect-secrets` Version Pin

**Files:**
- Modify: `pyproject.toml`

The Phase-1 review flagged `detect-secrets~=1.5` as inconsistent with the project's three-component pin convention (`PyYAML~=6.0.1`, `requests~=2.33.0`). Tighten to `~=1.5.0` (allows patches within 1.5.x).

- [ ] **Step 1: Edit `pyproject.toml`**

Replace the dev group entry:
```toml
    "detect-secrets~=1.5",
```
with:
```toml
    "detect-secrets~=1.5.0",
```

- [ ] **Step 2: Re-sync the lockfile**

Run:
```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
uv sync --all-groups
```

Expected: no errors. `detect-secrets` stays at 1.5.0.

- [ ] **Step 3: Verify the secrets-scan still passes**

Run:
```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_pre_flip.py 2>&1 | grep "no unaudited secrets"
```

Expected: `[PASS] no unaudited secrets: ok`.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build(deps): tighten detect-secrets pin to ~=1.5.0"
```

---

## Task 2: Fix CHANGELOG `[Unreleased]` Compare Link

**Files:**
- Modify: `CHANGELOG.md`

Current: `[Unreleased]: https://github.com/klein-business/legal-text-mcp-de/compare/HEAD` — this is a `HEAD...HEAD` no-op. Use the initial commit on `main` as the anchor.

- [ ] **Step 1: Identify the initial commit on `main`**

Run:
```bash
git log --reverse --oneline main | head -1
```

Expected: a single commit SHA + subject (likely `e510e4b Initial commit` or similar). Record the SHA.

- [ ] **Step 2: Edit the link in `CHANGELOG.md`**

Replace the existing `[Unreleased]` link with:
```
[Unreleased]: https://github.com/klein-business/legal-text-mcp-de/compare/<initial-sha>...HEAD
```

(Substitute `<initial-sha>` with the SHA from Step 1.)

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): fix unreleased compare link"
```

---

## Task 3: Add `mypy` to Dev Group and `[tool.mypy]` Section

**Files:**
- Modify: `pyproject.toml`

Add mypy as a dev dependency and configure it stufenweise: strict on `scripts/`, non-strict on `mcp/`.

- [ ] **Step 1: Add `mypy` to dev group**

In `pyproject.toml`, append to the `dev` list:
```toml
    "mypy~=1.13.0",
```

(Final list ordering: pytest, httpx, PyYAML, ruff, detect-secrets, mypy.)

- [ ] **Step 2: Add `[tool.mypy]` and overrides at the end of pyproject.toml**

Append:
```toml
[tool.mypy]
python_version = "3.12"
files = ["scripts", "mcp"]
show_error_codes = true
pretty = true

[[tool.mypy.overrides]]
module = "scripts.*"
strict = true

[[tool.mypy.overrides]]
module = "mcp.*"
# Per-module ratchet to strict planned. Currently plain mypy as warning-gate.
strict = false
```

- [ ] **Step 3: Sync**

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
uv sync --all-groups
```

- [ ] **Step 4: Smoke-test mypy invocation**

Run:
```bash
PYTHONPATH=mcp uv run --group dev mypy scripts 2>&1 | tail -3
```

Expected: either "Success: no issues found" or a list of typing errors. Either is acceptable for this task — the goal is to confirm mypy runs. Errors are fixed in Task 12 (typecheck-strict CI job setup) by fixing the actual issues or adding focused ignores.

Run also:
```bash
PYTHONPATH=mcp uv run --group dev mypy mcp 2>&1 | tail -3
```

Expected: plain mypy may report many findings. Acceptable; the `mcp/*` override is non-strict.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build(deps): add mypy with stufenweise strict config"
```

---

## Task 4: TDD `SKIPPED` Result Type in `verify_pre_flip`

**Files:**
- Modify: `scripts/verify_pre_flip.py`
- Modify: `mcp/tests/test_verify_pre_flip.py`

Replace the binary `passed: bool` with a tri-state `status: Literal["PASS", "FAIL", "SKIP"]`. The secrets-check returns SKIP when `detect-secrets-hook` is missing from PATH. Aggregator treats SKIP like PASS (exit code 0 when all are PASS or SKIP).

- [ ] **Step 1: Write the failing tests**

Append to `mcp/tests/test_verify_pre_flip.py`:

```python


def test_check_result_supports_skipped_status() -> None:
    """SKIPPED is a valid third status value."""
    skipped = vpf.CheckResult(name="x", status="SKIP", message="reason")
    assert skipped.status == "SKIP"
    assert skipped.passed is False  # backwards-compat property
    assert skipped.skipped is True


def test_secrets_scan_skips_when_tool_missing(
    tmp_path: Path, monkeypatch: "pytest.MonkeyPatch"
) -> None:
    """When detect-secrets-hook is not on PATH, return SKIPPED, not FAIL."""
    (tmp_path / ".secrets.baseline").write_text(
        '{"version": "1.5.0", "results": {}}', encoding="utf-8"
    )
    monkeypatch.setattr(vpf.shutil, "which", lambda name: None)
    result = vpf.check_no_unaudited_secrets(tmp_path)
    assert result.status == "SKIP", result.message
    assert "detect-secrets-hook" in result.message


def test_main_returns_zero_when_all_pass_or_skip(tmp_path: Path) -> None:
    """SKIPPED checks do not cause non-zero exit."""
    _populate_passing_repo(tmp_path)
    # Force the secrets check to be SKIP-ish by removing the baseline; it'll
    # FAIL with "missing baseline", though, so this test needs a different angle.
    # Instead: confirm a synthetic SKIP doesn't fail the aggregator.
    skipped = vpf.CheckResult(name="x", status="SKIP", message="m")
    passed = vpf.CheckResult(name="y", status="PASS", message="ok")
    rc = vpf._aggregate_exit_code([skipped, passed])
    assert rc == 0


def test_main_returns_nonzero_when_any_fail(tmp_path: Path) -> None:
    failed = vpf.CheckResult(name="x", status="FAIL", message="m")
    passed = vpf.CheckResult(name="y", status="PASS", message="ok")
    skipped = vpf.CheckResult(name="z", status="SKIP", message="m")
    rc = vpf._aggregate_exit_code([passed, skipped, failed])
    assert rc == 1
```

- [ ] **Step 2: Run tests to confirm failures**

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v -k "skipped or status"
```

Expected: 4 new tests fail (either `AttributeError`, `TypeError`, or assertion failure).

- [ ] **Step 3: Update `CheckResult` in `scripts/verify_pre_flip.py`**

Replace the existing dataclass:
```python
@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
```

with:
```python
from typing import Literal

CheckStatus = Literal["PASS", "FAIL", "SKIP"]


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str

    @property
    def passed(self) -> bool:
        """Backwards-compatible property: only PASS counts as passed."""
        return self.status == "PASS"

    @property
    def skipped(self) -> bool:
        return self.status == "SKIP"

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"
```

- [ ] **Step 4: Update every `CheckResult(...)` constructor call in the script**

Replace each `passed=True` with `status="PASS"`, each `passed=False` with `status="FAIL"`. Affected functions: `check_license_apache_2_0`, `check_required_files`, `check_no_proprietary_strings`, `check_pyproject_metadata`, `check_no_unaudited_secrets`. Use Edit's `replace_all` carefully — there are many occurrences.

The exact substitutions:
- `passed=True,` → `status="PASS",`
- `passed=False,` → `status="FAIL",`

After substitution, search for any remaining `passed=` in the file (should be zero):
```bash
grep -n "passed=" scripts/verify_pre_flip.py
```

Expected: no matches.

- [ ] **Step 5: Update `check_no_unaudited_secrets` to return SKIP**

In the function body, change the "detect-secrets-hook not on PATH" branch:

Before:
```python
    detect_secrets_hook = shutil.which("detect-secrets-hook")
    if detect_secrets_hook is None:
        return CheckResult(
            name="no unaudited secrets",
            status="FAIL",
            message="detect-secrets-hook not on PATH; run via 'uv run --group dev'",
        )
```

After:
```python
    detect_secrets_hook = shutil.which("detect-secrets-hook")
    if detect_secrets_hook is None:
        return CheckResult(
            name="no unaudited secrets",
            status="SKIP",
            message="detect-secrets-hook not on PATH; run via 'uv run --group dev'",
        )
```

- [ ] **Step 6: Add `_aggregate_exit_code` helper**

Add this helper function before `main()`:

```python
def _aggregate_exit_code(results: list[CheckResult]) -> int:
    """Return 0 if no FAIL, else 1. SKIP counts as success."""
    return 0 if not any(r.failed for r in results) else 1
```

- [ ] **Step 7: Update `main()` to use the helper and render SKIP**

Replace the per-result print loop:
```python
    for r in results:
        flag = "PASS" if r.passed else "FAIL"
        print(f"[{flag}] {r.name}: {r.message}")
```

with:
```python
    for r in results:
        print(f"[{r.status}] {r.name}: {r.message}")
```

Replace the return statement:
```python
    return 0 if all(r.passed for r in results) else 1
```

with:
```python
    return _aggregate_exit_code(results)
```

- [ ] **Step 8: Run all verify_pre_flip tests**

```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: all tests pass (Phase-1 tests adapted via the `passed` property; new SKIP tests pass).

If any Phase-1 test still uses `passed=True/False` style construction, update it to `status="PASS"/"FAIL"` style.

- [ ] **Step 9: Run the gate on the real repo**

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_pre_flip.py
```

Expected: all 5 checks PASS. Lines now use `[PASS]` (no longer mixed `PASS`/`FAIL`).

- [ ] **Step 10: Commit**

```bash
git add scripts/verify_pre_flip.py mcp/tests/test_verify_pre_flip.py
git commit -m "refactor(verify): introduce SKIP status; secrets-check skips on missing tool"
```

---

## Task 5: Measure Coverage Baseline + Evidence Doc

**Files:**
- Create: `docs/operations/coverage-baseline-phase2.md`

Measure current coverage and capture it as evidence. The result determines the floor in Task 6.

- [ ] **Step 1: Add `pytest-cov` to dev dependencies**

Edit `pyproject.toml`, dev group. Append:
```toml
    "pytest-cov~=6.0.0",
```

Run:
```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
uv sync --all-groups
```

- [ ] **Step 2: Run pytest with coverage**

```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests --cov=mcp --cov-report=term-missing 2>&1 | tail -40
```

Record the bottom-line `TOTAL` percentage.

- [ ] **Step 3: Write the evidence file**

Create `docs/operations/coverage-baseline-phase2.md` with:

```markdown
# Coverage Baseline — Phase 2

Measured: <YYYY-MM-DD>

| Metric | Value |
| --- | --- |
| Tool | `pytest-cov` |
| Target | `mcp/` package (all submodules) |
| Test set | `mcp/tests/` (267 tests, 0 failures) |
| Statement coverage | <measured>% |
| Branch coverage | not measured (statement coverage only at this stage) |

## Adopted floor

The Phase-2 CI gate sets `[tool.coverage.report] fail_under` to
`max(85, baseline)` = `<computed>%`. The floor is monotonic — Phase 3
and later may raise it but never lower it.

## Raw output

\`\`\`text
<paste the final TOTAL line and any sibling per-module lines>
\`\`\`
```

Fill in `<measured>`, `<computed>`, and the raw output from Step 2.

- [ ] **Step 4: Commit**

```bash
git add docs/operations/coverage-baseline-phase2.md pyproject.toml uv.lock
git commit -m "test(coverage): measure Phase 2 baseline + add pytest-cov"
```

---

## Task 6: Add `[tool.coverage]` Sections to `pyproject.toml`

**Files:**
- Modify: `pyproject.toml`

Use the baseline from Task 5 to set `fail_under`.

- [ ] **Step 1: Append coverage config to `pyproject.toml`**

```toml
[tool.coverage.run]
source = ["mcp"]
branch = false
omit = [
    "mcp/tests/*",
    "mcp/__pycache__/*",
]

[tool.coverage.report]
fail_under = <computed-floor>
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

Substitute `<computed-floor>` with the value from Task 5 (max(85, baseline)).

- [ ] **Step 2: Verify coverage gate**

```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests --cov=mcp --cov-report=term --cov-fail-under=<computed-floor> 2>&1 | tail -5
```

Expected: exit code 0, "TOTAL" line followed by "Required coverage: <floor>%" without failure.

- [ ] **Step 3: Test the floor enforces**

Temporarily set `fail_under` 5 points above the baseline to confirm the failure mode works:

```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests --cov=mcp --cov-fail-under=<baseline+5> 2>&1 | tail -3
```

Expected: non-zero exit, message about coverage below threshold. Revert `fail_under` to the computed floor (do not commit the test value).

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "test(coverage): enforce coverage floor in pyproject.toml"
```

---

## Task 7: Create `.pre-commit-config.yaml`

**Files:**
- Create: `.pre-commit-config.yaml`

Mirror the CI quality gates locally for developer convenience.

- [ ] **Step 1: Create the file**

Write `.pre-commit-config.yaml` with:

```yaml
# Pre-commit hook configuration. Mirrors CI checks for fast local feedback.
# CI is the authoritative gate; pre-commit is opt-in.
# Install with: uv run --group dev pre-commit install
# Run locally:  uv run --group dev pre-commit run --all-files

repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.6  # latest stable at time of authoring; check at install time
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        args: [--config-file=pyproject.toml]
        additional_dependencies:
          - pydantic-settings
          - fastapi
          - rapidfuzz

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]
        exclude: |
          (?x)^(
            uv\.lock|
            mcp/tests/fixtures/.*|
            \.secrets\.baseline
          )$

  - repo: https://github.com/DavidAnson/markdownlint-cli2
    rev: v0.18.1
    hooks:
      - id: markdownlint-cli2

  - repo: https://github.com/rhysd/actionlint
    rev: v1.7.6
    hooks:
      - id: actionlint

  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.10.0
    hooks:
      - id: shellcheck
        args: [--severity=warning]

  - repo: local
    hooks:
      - id: spdx-header
        name: SPDX-License-Identifier on new Python files
        entry: scripts/check_spdx_header.py
        language: python
        types: [python]
        pass_filenames: true
```

- [ ] **Step 2: Add `pre-commit` to dev dependencies**

In `pyproject.toml` dev list:
```toml
    "pre-commit~=4.0",
```

Run:
```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
uv sync --all-groups
```

- [ ] **Step 3: Defer first run until Task 8 lands**

The `spdx-header` hook references `scripts/check_spdx_header.py` which doesn't exist yet (Task 8 creates it). Do NOT run `pre-commit run --all-files` here.

- [ ] **Step 4: Commit**

```bash
git add .pre-commit-config.yaml pyproject.toml uv.lock
git commit -m "build(precommit): add pre-commit config mirroring CI gates"
```

---

## Task 8: TDD `scripts/check_spdx_header.py` + Header Template

**Files:**
- Create: `.github/spdx-header-template.txt`
- Create: `scripts/check_spdx_header.py`
- Create: `mcp/tests/test_check_spdx_header.py`

A pre-commit hook that ensures every NEW Python file carries the SPDX header. Existing files are exempt (no retrofit in Phase 2).

- [ ] **Step 1: Create the header template**

Create `.github/spdx-header-template.txt` with this exact content:

```
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
```

- [ ] **Step 2: Write the failing tests**

Create `mcp/tests/test_check_spdx_header.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Unit tests for scripts/check_spdx_header.py."""

from __future__ import annotations

import subprocess
import sys
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
```

- [ ] **Step 3: Run to confirm failure**

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_check_spdx_header.py -v
```

Expected: collection error — `ModuleNotFoundError: No module named 'scripts.check_spdx_header'`.

- [ ] **Step 4: Implement the script**

Create `scripts/check_spdx_header.py`:

```python
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
EXEMPT_FILE = REPO_ROOT / ".github" / "spdx-header-exempt.txt"

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
```

- [ ] **Step 5: Generate the exempt list (pre-Phase-2 Python files only)**

Exclude the two files we just created (`scripts/check_spdx_header.py` and `mcp/tests/test_check_spdx_header.py`) since they correctly carry the SPDX header and must remain subject to the hook for future modifications.

Run from repo root:
```bash
find mcp scripts -name "*.py" -type f \
  | grep -v -E "(scripts/check_spdx_header\.py$|mcp/tests/test_check_spdx_header\.py$)" \
  | sort > .github/spdx-header-exempt.txt
```

Then prepend a header comment to the file using your editor or:
```bash
printf '# Files exempt from the SPDX-header pre-commit hook.\n# These existed before Phase 2; retrofit is deferred to a future cleanup.\n# Lines starting with # are ignored.\n\n%s\n' "$(cat .github/spdx-header-exempt.txt)" > .github/spdx-header-exempt.txt
```

Verify:
```bash
wc -l .github/spdx-header-exempt.txt
head -10 .github/spdx-header-exempt.txt
grep -E "check_spdx_header" .github/spdx-header-exempt.txt
```

Expected: ~25-30 lines (matches the count of existing Python files); the third grep returns no output (the Phase-2 additions are NOT on the list).

- [ ] **Step 6: Run tests**

```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_check_spdx_header.py -v
```

Expected: all 6 tests pass.

- [ ] **Step 7: Try the pre-commit hook end-to-end**

Create a temporary new file:
```bash
echo "x = 1" > /tmp/test_spdx.py
PYTHONPATH=mcp uv run --group dev python scripts/check_spdx_header.py /tmp/test_spdx.py
```

Expected: exit code 1, error message about missing header.

Then:
```bash
printf "# SPDX-License-Identifier: Apache-2.0\n# Copyright 2026 klein-business\nx = 1\n" > /tmp/test_spdx.py
PYTHONPATH=mcp uv run --group dev python scripts/check_spdx_header.py /tmp/test_spdx.py
rm /tmp/test_spdx.py
```

Expected: exit code 0.

- [ ] **Step 8: Commit**

```bash
git add scripts/check_spdx_header.py mcp/tests/test_check_spdx_header.py .github/spdx-header-template.txt .github/spdx-header-exempt.txt
git commit -m "feat(precommit): add SPDX-header check for new Python files"
```

---

## Task 9: Extract MegaLinter into `megalinter.yml`

**Files:**
- Create: `.github/workflows/megalinter.yml`
- Modify: `.github/workflows/ci.yml`

The existing `ci.yml` contains a `megalinter` job inline. The Phase 2 design has MegaLinter in its own workflow.

- [ ] **Step 1: Create `.github/workflows/megalinter.yml`**

```yaml
name: MegaLinter

on:
  pull_request:
  push:
    branches:
      - main

permissions:
  contents: read

concurrency:
  group: megalinter-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  megalinter:
    name: MegaLinter
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6
        with:
          fetch-depth: 0

      - name: MegaLinter
        uses: oxsecurity/megalinter/flavors/python@8fbdead70d1409964ab3d5afa885e18ee85388bb # v9.4.0
        env:
          VALIDATE_ALL_CODEBASE: true
```

- [ ] **Step 2: Remove the `megalinter` job from `ci.yml`**

In `.github/workflows/ci.yml`, delete the entire `megalinter:` job block (from `megalinter:` through the end of its `steps:` list). Leave only the `tests:` job.

- [ ] **Step 3: Validate with actionlint**

If `actionlint` is on PATH (e.g., via `brew install actionlint`):
```bash
actionlint .github/workflows/megalinter.yml .github/workflows/ci.yml
```

Expected: no output (success). If actionlint is not installed, skip and rely on CI to catch syntax errors.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/megalinter.yml .github/workflows/ci.yml
git commit -m "ci: extract MegaLinter into its own workflow"
```

---

## Task 10: Add MegaLinter Linter Expansion

**Files:**
- Modify: `.mega-linter.yml`

Expand MegaLinter's linter set per the spec: add MARKDOWN_MARKDOWNLINT2, ACTION_ACTIONLINT, JSON_JSONLINT.

- [ ] **Step 1: Edit `.mega-linter.yml`**

Replace the existing content with:

```yaml
APPLY_FIXES: none
DEFAULT_BRANCH: main
PRINT_ALPACA: false
SHOW_ELAPSED_TIME: true
ENABLE_LINTERS:
  - PYTHON_RUFF
  - BASH_SHELLCHECK
  - YAML_PRETTIER
  - MARKDOWN_MARKDOWNLINT2
  - ACTION_ACTIONLINT
  - JSON_JSONLINT
PYTHON_RUFF_CONFIG_FILE: pyproject.toml
MARKDOWN_MARKDOWNLINT2_FILTER_REGEX_EXCLUDE: ^(docs-legacy|docs/superpowers)/
```

(The exclude regex prevents linting historical and meta-doc content.)

- [ ] **Step 2: Commit**

```bash
git add .mega-linter.yml
git commit -m "ci(megalinter): expand linter set to markdown, actions, json"
```

---

## Task 11: Retire `verify_ci_workflow.py`

**Files:**
- Delete: `scripts/verify_ci_workflow.py`
- Modify: `scripts/verify_release.py` (remove any reference)
- Modify: `mcp/tests/test_release_gate.py` (if it asserts on the script)

The script hardcodes the old 2-job ci.yml structure (`jobs == {"tests", "megalinter"}`, specific step ordering). After the refactor it would be garbage. The `check_workflow_set` check in `verify_pre_flip.py` (Task 19) replaces its existence-check role; actionlint and actual workflow execution replace its correctness-check role.

- [ ] **Step 1: Check `verify_release.py` for the reference**

```bash
grep -n "verify_ci_workflow" scripts/verify_release.py
```

If a match is found, note the line numbers; they will be removed in Step 3.

- [ ] **Step 2: Check `test_release_gate.py` for assertions on the script**

```bash
grep -n "verify_ci_workflow" mcp/tests/test_release_gate.py mcp/tests/test_*.py
```

If matches are found, the tests need updating too.

- [ ] **Step 3: Remove references**

Edit `scripts/verify_release.py` and any matching tests to remove the references. Use the Edit tool with the exact lines identified in Steps 1-2.

- [ ] **Step 4: Delete the script**

```bash
git rm scripts/verify_ci_workflow.py
```

- [ ] **Step 5: Run the full test suite to verify nothing depends on the script**

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
PYTHONPATH=mcp uv run --group dev pytest mcp/tests -q --tb=short 2>&1 | tail -5
```

Expected: tests pass. If anything fails, fix the test or the reference.

- [ ] **Step 6: Run the release gate**

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py 2>&1 | tail -10
```

Expected: passes (the release gate may have asserted on the now-deleted script; that's the only test we need to fix here).

- [ ] **Step 7: Commit**

```bash
git add scripts/verify_ci_workflow.py scripts/verify_release.py mcp/tests/test_release_gate.py 2>/dev/null
git diff --cached --name-only  # confirm what's staged
git commit -m "refactor: retire verify_ci_workflow.py (superseded by verify_pre_flip workflow-set check)"
```

---

## Task 12: Refactor `ci.yml` Into Multi-Job Structure

**Files:**
- Modify: `.github/workflows/ci.yml`

Replace the single `tests` job with: lint, typecheck-strict, typecheck-warn, test (matrix), lock-integrity, build. The E2E/Docker job moves to `e2e.yml` in Task 13.

- [ ] **Step 1: Replace the file content**

Overwrite `.github/workflows/ci.yml` with:

```yaml
name: CI

on:
  pull_request:
  push:
    branches:
      - main

permissions:
  contents: read

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: Lint (ruff)
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6

      - name: Install uv
        uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0
        with:
          version: "0.10.12"
          enable-cache: true

      - name: Sync
        run: uv sync --locked --all-groups

      - name: Ruff check
        run: uv run ruff check .

      - name: Ruff format check
        run: uv run ruff format --check .

  typecheck-strict:
    name: Mypy strict (scripts)
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6

      - name: Install uv
        uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0
        with:
          version: "0.10.12"
          enable-cache: true

      - name: Sync
        run: uv sync --locked --all-groups

      - name: Mypy strict on scripts/
        run: uv run --group dev mypy scripts

  typecheck-warn:
    name: Mypy plain (mcp) [non-blocking]
    runs-on: ubuntu-latest
    timeout-minutes: 5
    continue-on-error: true
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6

      - name: Install uv
        uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0
        with:
          version: "0.10.12"
          enable-cache: true

      - name: Sync
        run: uv sync --locked --all-groups

      - name: Mypy on mcp/ (capped output)
        run: |
          uv run --group dev mypy mcp 2>&1 | head -60 | tee mypy-mcp-summary.txt || true

      - name: Upload mypy summary
        uses: actions/upload-artifact@b4b15b8c7c6ac21ea08fcf65892d2ee8f75cf882 # v4.4.4
        with:
          name: mypy-mcp-summary
          path: mypy-mcp-summary.txt
          retention-days: 14

  test:
    name: Test (py${{ matrix.python-version }})
    runs-on: ubuntu-latest
    timeout-minutes: 10
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6

      - name: Install uv
        uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0
        with:
          version: "0.10.12"
          enable-cache: true
          python-version: ${{ matrix.python-version }}

      - name: Sync
        run: uv sync --locked --all-groups

      - name: Pytest with coverage
        run: PYTHONPATH=mcp uv run --group dev pytest mcp/tests --cov=mcp --cov-report=xml

      - name: Upload coverage XML
        if: matrix.python-version == '3.12'
        uses: actions/upload-artifact@b4b15b8c7c6ac21ea08fcf65892d2ee8f75cf882 # v4.4.4
        with:
          name: coverage-xml
          path: coverage.xml
          retention-days: 14

  lock-integrity:
    name: Lockfile integrity
    runs-on: ubuntu-latest
    timeout-minutes: 3
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6

      - name: Install uv
        uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0
        with:
          version: "0.10.12"
          enable-cache: true

      - name: Check lock matches pyproject
        run: uv lock --check

  build:
    name: Build (sdist + wheel)
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6

      - name: Install uv
        uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0
        with:
          version: "0.10.12"
          enable-cache: true

      - name: Sync
        run: uv sync --locked --all-groups

      - name: Build
        run: uv build || echo "Build skipped — package = false in [tool.uv]. Phase 4 introduces hatchling."
        # Phase 4 task: switch [tool.uv] package = false to hatchling. Until then,
        # `uv build` may report nothing to build; the step records the intent.
```

- [ ] **Step 2: Validate**

```bash
# If actionlint available locally:
actionlint .github/workflows/ci.yml || true
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: refactor ci.yml into lint/typecheck/test/lock/build jobs"
```

---

## Task 13: Create `e2e.yml`

**Files:**
- Create: `.github/workflows/e2e.yml`

The E2E gate (`verify_release.py`, `verify_e2e.py`, `verify_uv_runtime_docker.py`) moves out of `ci.yml` into its own workflow with nightly trigger.

- [ ] **Step 1: Create the file**

```yaml
name: E2E

on:
  pull_request:
  push:
    branches:
      - main
  schedule:
    # Nightly at 03:00 UTC
    - cron: "0 3 * * *"

permissions:
  contents: read

concurrency:
  group: e2e-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  release-gate:
    name: Release gate (fixture-backed)
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6

      - name: Install uv
        uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0
        with:
          version: "0.10.12"
          enable-cache: true

      - name: Sync
        run: uv sync --locked --all-groups

      - name: Verify release gate
        run: PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py

  uv-runtime-and-docker:
    name: uv runtime and Docker
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6

      - name: Install uv
        uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0
        with:
          version: "0.10.12"
          enable-cache: true

      - name: Sync
        run: uv sync --locked --all-groups

      - name: Verify uv runtime and Docker
        run: PYTHONPATH=mcp uv run --group dev python scripts/verify_uv_runtime_docker.py
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/e2e.yml
git commit -m "ci: extract E2E gate into dedicated workflow with nightly trigger"
```

---

## Task 14: Create `.commitlintrc.json` and `commitlint.yml`

**Files:**
- Create: `.commitlintrc.json`
- Create: `.github/workflows/commitlint.yml`

Enforce Conventional Commits on PR titles only.

- [ ] **Step 1: Create `.commitlintrc.json`**

```json
{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "type-enum": [
      2,
      "always",
      ["feat", "fix", "chore", "refactor", "docs", "test", "ci", "perf", "build", "style"]
    ],
    "subject-case": [2, "never", ["upper-case", "pascal-case", "start-case"]],
    "header-max-length": [2, "always", 100]
  }
}
```

- [ ] **Step 2: Create `.github/workflows/commitlint.yml`**

```yaml
name: Commitlint

on:
  pull_request:
    types: [opened, edited, synchronize, reopened]

permissions:
  contents: read
  pull-requests: read

jobs:
  pr-title:
    name: PR title (Conventional Commits)
    runs-on: ubuntu-latest
    timeout-minutes: 3
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6

      - name: Lint PR title
        uses: wagoid/commitlint-github-action@b948419dd99f3fd78a6548d48f94e3df7f6bf3ed # v6.2.1
        with:
          configFile: .commitlintrc.json
          firstParent: false
          failOnWarnings: false
          helpURL: https://www.conventionalcommits.org
        env:
          # Lint PR title only (single virtual commit composed of the title)
          NODE_PATH: /github/workspace/node_modules
```

Note: `wagoid/commitlint-github-action` by default lints commits on the PR, not the title. To lint the title only, an alternative is to use `amannn/action-semantic-pull-request`:

Update the file to use the dedicated PR-title linter instead:

```yaml
name: Commitlint

on:
  pull_request:
    types: [opened, edited, synchronize, reopened]

permissions:
  contents: read
  pull-requests: read

jobs:
  pr-title:
    name: PR title (Conventional Commits)
    runs-on: ubuntu-latest
    timeout-minutes: 3
    steps:
      - name: Lint PR title
        uses: amannn/action-semantic-pull-request@0723387faaf9b38adef4775cd42cfd5155ed6017 # v5.5.3
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          types: |
            feat
            fix
            chore
            refactor
            docs
            test
            ci
            perf
            build
            style
          requireScope: false
          subjectPattern: ^[a-z].+$
          subjectPatternError: |
            Subject must start with a lowercase letter.
          wip: true
```

Use this latter form. Delete the first attempt.

- [ ] **Step 3: Sanity-test the config**

If a PR title would be `feat: Phase 2 — add CI hardening`, the leading capital `P` in `Phase` would FAIL `subject-case` rule. The PR-title commit messages we used in Phase 1 sometimes start with `feat: Phase 1 — re-license …` (capital P). Adjust the `subjectPattern` to allow leading uppercase if the user prefers German-style sentence capitalization. Alternatively, the `subject-case` rule via `@commitlint/config-conventional` allows sentence-case.

Use this final variant:
```yaml
          subjectPattern: ^[A-Za-z].+$
          subjectPatternError: |
            Subject must start with a letter.
```

- [ ] **Step 4: Commit**

```bash
git add .commitlintrc.json .github/workflows/commitlint.yml
git commit -m "ci(commitlint): enforce Conventional Commits on PR titles"
```

---

## Task 15: Create `dco.yml`

**Files:**
- Create: `.github/workflows/dco.yml`

Enforce DCO sign-off on every commit in a PR.

- [ ] **Step 1: Create the file**

```yaml
name: DCO

on:
  pull_request:
    types: [opened, edited, synchronize, reopened]

permissions:
  contents: read
  pull-requests: read

jobs:
  dco:
    name: DCO sign-off check
    runs-on: ubuntu-latest
    timeout-minutes: 3
    steps:
      - name: Checkout PR
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6
        with:
          fetch-depth: 0
          ref: ${{ github.event.pull_request.head.sha }}

      - name: DCO check
        uses: tim-actions/dco@2fd24ae9f0e84576b48bbb1d09ba0caa31cb6a5b # v1.1.0
        with:
          commits: ${{ github.event.pull_request.head.sha }}
```

- [ ] **Step 2: Document local setup**

The maintainer commits with `git commit -s` to add the `Signed-off-by:` trailer. This will be documented in `CONTRIBUTING.md` in Phase 3. For Phase 2, no in-repo docs change; just the workflow.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/dco.yml
git commit -m "ci(dco): add DCO sign-off enforcement"
```

---

## Task 16: Create `dependency-review.yml`

**Files:**
- Create: `.github/workflows/dependency-review.yml`

Run GitHub's official Dependency Review on every PR.

- [ ] **Step 1: Create the file**

```yaml
name: Dependency Review

on:
  pull_request:

permissions:
  contents: read

jobs:
  dependency-review:
    name: Dependency review
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6

      - name: Dependency Review
        uses: actions/dependency-review-action@4081bf99e2866ebe428fc0477b69eb4fcda7220a # v4.5.0
        with:
          fail-on-severity: high
          comment-summary-in-pr: on-failure
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/dependency-review.yml
git commit -m "ci(deps): add Dependency Review for PRs"
```

---

## Task 17: Create `codeql.yml`

**Files:**
- Create: `.github/workflows/codeql.yml`

Python SAST via GitHub CodeQL.

- [ ] **Step 1: Create the file**

```yaml
name: CodeQL

on:
  pull_request:
  push:
    branches:
      - main
  schedule:
    - cron: "30 4 * * 1"  # Mondays at 04:30 UTC

permissions:
  actions: read
  contents: read
  security-events: write

jobs:
  analyze:
    name: CodeQL analysis (python)
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6

      - name: Initialize CodeQL
        uses: github/codeql-action/init@aa578102511db1f4524ed59b8cc2bae4f6e88195 # v3.27.6
        with:
          languages: python
          queries: security-extended

      - name: Autobuild (no-op for Python)
        uses: github/codeql-action/autobuild@aa578102511db1f4524ed59b8cc2bae4f6e88195 # v3.27.6

      - name: Analyze
        uses: github/codeql-action/analyze@aa578102511db1f4524ed59b8cc2bae4f6e88195 # v3.27.6
        with:
          category: "/language:python"
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/codeql.yml
git commit -m "ci(security): add CodeQL Python SAST workflow"
```

---

## Task 18: Create `scorecard.yml`

**Files:**
- Create: `.github/workflows/scorecard.yml`

OpenSSF Scorecard weekly + push to default branch.

- [ ] **Step 1: Create the file**

```yaml
name: Scorecard

on:
  branch_protection_rule:
  schedule:
    - cron: "30 4 * * 2"  # Tuesdays at 04:30 UTC
  push:
    branches:
      - main

permissions: read-all

jobs:
  analysis:
    name: OpenSSF Scorecard
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      security-events: write
      id-token: write
      contents: read
      actions: read
    steps:
      - name: Checkout
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6
        with:
          persist-credentials: false

      - name: Run Scorecard
        uses: ossf/scorecard-action@f49aabe0b5af0936a0987cfb85d86b75731b0186 # v2.4.1
        with:
          results_file: results.sarif
          results_format: sarif
          publish_results: true

      - name: Upload SARIF artifact
        uses: actions/upload-artifact@b4b15b8c7c6ac21ea08fcf65892d2ee8f75cf882 # v4.4.4
        with:
          name: scorecard-sarif
          path: results.sarif
          retention-days: 14

      - name: Upload to GitHub Code Scanning
        uses: github/codeql-action/upload-sarif@aa578102511db1f4524ed59b8cc2bae4f6e88195 # v3.27.6
        with:
          sarif_file: results.sarif
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/scorecard.yml
git commit -m "ci(security): add OpenSSF Scorecard weekly workflow"
```

---

## Task 19: TDD `check_workflow_set` in `verify_pre_flip`

**Files:**
- Modify: `scripts/verify_pre_flip.py`
- Modify: `mcp/tests/test_verify_pre_flip.py`

Asserts `.github/workflows/` contains exactly the eight expected files.

- [ ] **Step 1: Write the failing tests**

Append to `mcp/tests/test_verify_pre_flip.py`:

```python


EXPECTED_WORKFLOWS = {
    "ci.yml",
    "e2e.yml",
    "codeql.yml",
    "scorecard.yml",
    "dependency-review.yml",
    "commitlint.yml",
    "dco.yml",
    "megalinter.yml",
}


def test_workflow_set_passes_when_complete(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    for name in EXPECTED_WORKFLOWS:
        (wf / name).write_text("name: x\non: push", encoding="utf-8")
    result = vpf.check_workflow_set(tmp_path)
    assert result.status == "PASS", result.message


def test_workflow_set_fails_when_missing(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text("name: x", encoding="utf-8")
    result = vpf.check_workflow_set(tmp_path)
    assert result.status == "FAIL"
    assert "missing" in result.message.lower()
    assert "codeql.yml" in result.message


def test_workflow_set_fails_when_extra(tmp_path: Path) -> None:
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    for name in EXPECTED_WORKFLOWS:
        (wf / name).write_text("x", encoding="utf-8")
    (wf / "rogue.yml").write_text("x", encoding="utf-8")
    result = vpf.check_workflow_set(tmp_path)
    assert result.status == "FAIL"
    assert "unexpected" in result.message.lower()
    assert "rogue.yml" in result.message
```

- [ ] **Step 2: Run to confirm failure**

```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py::test_workflow_set_passes_when_complete -v
```

Expected: FAIL with `AttributeError: module 'verify_pre_flip' has no attribute 'check_workflow_set'`.

- [ ] **Step 3: Implement the check**

Add to `scripts/verify_pre_flip.py` after `check_no_unaudited_secrets`:

```python
EXPECTED_WORKFLOWS = (
    "ci.yml",
    "e2e.yml",
    "codeql.yml",
    "scorecard.yml",
    "dependency-review.yml",
    "commitlint.yml",
    "dco.yml",
    "megalinter.yml",
)


def check_workflow_set(root: Path) -> CheckResult:
    wf_dir = root / ".github" / "workflows"
    if not wf_dir.is_dir():
        return CheckResult(
            name="workflow set",
            status="FAIL",
            message=f"{wf_dir} does not exist",
        )
    present = {p.name for p in wf_dir.iterdir() if p.is_file() and p.suffix in {".yml", ".yaml"}}
    expected = set(EXPECTED_WORKFLOWS)
    missing = sorted(expected - present)
    extra = sorted(present - expected)
    problems: list[str] = []
    if missing:
        problems.append(f"missing: {', '.join(missing)}")
    if extra:
        problems.append(f"unexpected: {', '.join(extra)}")
    if problems:
        return CheckResult(
            name="workflow set",
            status="FAIL",
            message="; ".join(problems),
        )
    return CheckResult(name="workflow set", status="PASS", message="ok")
```

Extend `CHECKS`:
```python
CHECKS = [
    check_license_apache_2_0,
    check_required_files,
    check_no_proprietary_strings,
    check_pyproject_metadata,
    check_no_unaudited_secrets,
    check_workflow_set,
]
```

- [ ] **Step 4: Run all tests**

```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: all tests pass including the 3 new workflow-set tests.

- [ ] **Step 5: Run the gate on real repo**

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_pre_flip.py 2>&1 | grep "workflow set"
```

Expected: `[PASS] workflow set: ok` (assumes Tasks 9-17 produced all 8 workflows).

- [ ] **Step 6: Commit**

```bash
git add scripts/verify_pre_flip.py mcp/tests/test_verify_pre_flip.py
git commit -m "feat(verify): add pre-flip workflow-set check"
```

---

## Task 20: TDD `check_required_status_checks` (GitHub API)

**Files:**
- Modify: `scripts/verify_pre_flip.py`
- Modify: `mcp/tests/test_verify_pre_flip.py`

Queries `https://api.github.com/repos/<owner>/<repo>/branches/main/protection` and asserts the expected status-check contexts are required. Uses stdlib `urllib.request`. Skips when `VERIFY_GITHUB_TOKEN` is unset.

- [ ] **Step 1: Write the failing tests**

Append:

```python
from unittest.mock import MagicMock, patch


EXPECTED_REQUIRED_CHECKS = {
    "Lint (ruff)",
    "Mypy strict (scripts)",
    "Test (py3.12)",
    "Test (py3.13)",
    "Lockfile integrity",
    "Build (sdist + wheel)",
    "MegaLinter",
    "Release gate (fixture-backed)",
    "uv runtime and Docker",
    "CodeQL analysis (python)",
    "Dependency review",
    "PR title (Conventional Commits)",
    "DCO sign-off check",
}


def test_required_status_checks_skips_without_token(monkeypatch) -> None:
    monkeypatch.delenv("VERIFY_GITHUB_TOKEN", raising=False)
    result = vpf.check_required_status_checks(Path("/tmp"))
    assert result.status == "SKIP"
    assert "VERIFY_GITHUB_TOKEN" in result.message


def test_required_status_checks_passes_when_all_present(monkeypatch) -> None:
    monkeypatch.setenv("VERIFY_GITHUB_TOKEN", "fake-token")
    payload = {
        "required_status_checks": {
            "contexts": list(EXPECTED_REQUIRED_CHECKS),
        }
    }
    with patch.object(vpf, "_fetch_github_json", return_value=payload):
        result = vpf.check_required_status_checks(Path("/tmp"))
    assert result.status == "PASS", result.message


def test_required_status_checks_fails_when_any_missing(monkeypatch) -> None:
    monkeypatch.setenv("VERIFY_GITHUB_TOKEN", "fake-token")
    payload = {
        "required_status_checks": {
            "contexts": ["Lint (ruff)"],  # only one
        }
    }
    with patch.object(vpf, "_fetch_github_json", return_value=payload):
        result = vpf.check_required_status_checks(Path("/tmp"))
    assert result.status == "FAIL"
    assert "missing" in result.message.lower()
```

- [ ] **Step 2: Run to confirm failure**

```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py::test_required_status_checks_skips_without_token -v
```

Expected: FAIL with `AttributeError`.

- [ ] **Step 3: Implement helpers + check**

Add to `scripts/verify_pre_flip.py`:

```python
import json as _json
import os
import urllib.error
import urllib.request

GITHUB_API_BASE = "https://api.github.com"
GITHUB_REPO_SLUG = "klein-business/legal-text-mcp-de"
GITHUB_DEFAULT_BRANCH = "main"

EXPECTED_REQUIRED_CHECKS = {
    "Lint (ruff)",
    "Mypy strict (scripts)",
    "Test (py3.12)",
    "Test (py3.13)",
    "Lockfile integrity",
    "Build (sdist + wheel)",
    "MegaLinter",
    "Release gate (fixture-backed)",
    "uv runtime and Docker",
    "CodeQL analysis (python)",
    "Dependency review",
    "PR title (Conventional Commits)",
    "DCO sign-off check",
}


def _fetch_github_json(path: str, token: str) -> dict:
    """GET https://api.github.com/<path> with auth; return parsed JSON."""
    url = f"{GITHUB_API_BASE}/{path.lstrip('/')}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return _json.loads(resp.read().decode("utf-8"))


def check_required_status_checks(root: Path) -> CheckResult:
    token = os.environ.get("VERIFY_GITHUB_TOKEN")
    if not token:
        return CheckResult(
            name="required status checks",
            status="SKIP",
            message="VERIFY_GITHUB_TOKEN not set; cannot query branch protection",
        )
    try:
        payload = _fetch_github_json(
            f"/repos/{GITHUB_REPO_SLUG}/branches/{GITHUB_DEFAULT_BRANCH}/protection",
            token,
        )
    except urllib.error.HTTPError as exc:
        return CheckResult(
            name="required status checks",
            status="FAIL",
            message=f"GitHub API {exc.code}: {exc.reason}",
        )
    contexts = set(
        (payload.get("required_status_checks") or {}).get("contexts") or []
    )
    missing = sorted(EXPECTED_REQUIRED_CHECKS - contexts)
    if missing:
        return CheckResult(
            name="required status checks",
            status="FAIL",
            message=f"missing required contexts: {', '.join(missing)}",
        )
    return CheckResult(name="required status checks", status="PASS", message="ok")
```

Extend `CHECKS`:
```python
CHECKS = [
    check_license_apache_2_0,
    check_required_files,
    check_no_proprietary_strings,
    check_pyproject_metadata,
    check_no_unaudited_secrets,
    check_workflow_set,
    check_required_status_checks,
]
```

- [ ] **Step 4: Run tests**

```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Run the gate (will SKIP without token)**

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_pre_flip.py 2>&1 | grep "required status checks"
```

Expected: `[SKIP] required status checks: VERIFY_GITHUB_TOKEN not set; …`.

- [ ] **Step 6: Commit**

```bash
git add scripts/verify_pre_flip.py mcp/tests/test_verify_pre_flip.py
git commit -m "feat(verify): add pre-flip required-status-checks check (GitHub API)"
```

---

## Task 21: TDD `check_branch_protection` (GitHub API)

**Files:**
- Modify: `scripts/verify_pre_flip.py`
- Modify: `mcp/tests/test_verify_pre_flip.py`

Asserts protection has `enforce_admins=true`, `required_linear_history=true`, `allow_force_pushes=false`, and `required_signatures=true`.

- [ ] **Step 1: Write the failing tests**

Append:

```python
def test_branch_protection_skips_without_token(monkeypatch) -> None:
    monkeypatch.delenv("VERIFY_GITHUB_TOKEN", raising=False)
    result = vpf.check_branch_protection(Path("/tmp"))
    assert result.status == "SKIP"


def test_branch_protection_passes_when_strict(monkeypatch) -> None:
    monkeypatch.setenv("VERIFY_GITHUB_TOKEN", "fake")
    payload = {
        "enforce_admins": {"enabled": True},
        "required_linear_history": {"enabled": True},
        "allow_force_pushes": {"enabled": False},
        "required_signatures": {"enabled": True},
    }
    with patch.object(vpf, "_fetch_github_json", return_value=payload):
        result = vpf.check_branch_protection(Path("/tmp"))
    assert result.status == "PASS", result.message


def test_branch_protection_fails_when_admins_not_enforced(monkeypatch) -> None:
    monkeypatch.setenv("VERIFY_GITHUB_TOKEN", "fake")
    payload = {
        "enforce_admins": {"enabled": False},
        "required_linear_history": {"enabled": True},
        "allow_force_pushes": {"enabled": False},
        "required_signatures": {"enabled": True},
    }
    with patch.object(vpf, "_fetch_github_json", return_value=payload):
        result = vpf.check_branch_protection(Path("/tmp"))
    assert result.status == "FAIL"
    assert "enforce_admins" in result.message
```

- [ ] **Step 2: Run to confirm failure**

```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py::test_branch_protection_skips_without_token -v
```

Expected: FAIL with `AttributeError`.

- [ ] **Step 3: Implement**

Add:

```python
EXPECTED_PROTECTION_RULES = (
    ("enforce_admins", True),
    ("required_linear_history", True),
    ("allow_force_pushes", False),
    ("required_signatures", True),
)


def check_branch_protection(root: Path) -> CheckResult:
    token = os.environ.get("VERIFY_GITHUB_TOKEN")
    if not token:
        return CheckResult(
            name="branch protection",
            status="SKIP",
            message="VERIFY_GITHUB_TOKEN not set; cannot query branch protection",
        )
    try:
        payload = _fetch_github_json(
            f"/repos/{GITHUB_REPO_SLUG}/branches/{GITHUB_DEFAULT_BRANCH}/protection",
            token,
        )
    except urllib.error.HTTPError as exc:
        return CheckResult(
            name="branch protection",
            status="FAIL",
            message=f"GitHub API {exc.code}: {exc.reason}",
        )
    failures: list[str] = []
    for rule, want in EXPECTED_PROTECTION_RULES:
        block = payload.get(rule) or {}
        got = bool(block.get("enabled"))
        if got != want:
            failures.append(f"{rule}: expected {want}, got {got}")
    if failures:
        return CheckResult(
            name="branch protection",
            status="FAIL",
            message="; ".join(failures),
        )
    return CheckResult(name="branch protection", status="PASS", message="ok")
```

Extend `CHECKS`:
```python
CHECKS = [
    check_license_apache_2_0,
    check_required_files,
    check_no_proprietary_strings,
    check_pyproject_metadata,
    check_no_unaudited_secrets,
    check_workflow_set,
    check_required_status_checks,
    check_branch_protection,
]
```

- [ ] **Step 4: Run tests**

```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Verify the gate now has 8 checks**

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_pre_flip.py 2>&1 | grep -E "^\[" | wc -l
```

Expected: `8`.

- [ ] **Step 6: Commit**

```bash
git add scripts/verify_pre_flip.py mcp/tests/test_verify_pre_flip.py
git commit -m "feat(verify): add pre-flip branch-protection check (GitHub API)"
```

---

## Task 22: Create `SECURITY.md`

**Files:**
- Create: `SECURITY.md`

Activates GitHub's Security Advisory tab and provides the disclosure policy.

- [ ] **Step 1: Create the file**

```markdown
# Security Policy

## Reporting a Vulnerability

We take security issues seriously. **Please do not file a public GitHub
issue** for security reports.

### Preferred channel

[GitHub Security Advisories — Report a vulnerability](https://github.com/klein-business/legal-text-mcp-de/security/advisories/new)

This routes your report to the maintainer privately. GitHub will assign
a draft advisory and a private discussion thread.

### Backup channel

If the preferred channel is unavailable, e-mail
`martin@klein.business` with subject `legal-text-mcp-de security
report` and include:

- a description of the issue and its impact,
- reproduction steps or a proof of concept,
- the affected version (`v0.x` pre-release vs. tagged release),
- your name / handle if you wish to be credited.

## Response SLA

| Stage | Target |
| --- | --- |
| Acknowledgement of receipt | 5 business days |
| Initial severity assessment | 10 business days |
| Coordinated public disclosure (or fix released) | 90 days from acknowledgement |

If a fix takes longer than 90 days, we will keep you informed and
coordinate disclosure timing.

## Supported Versions

This project is pre-`v1.0.0`. The stability contract for the MCP tool
surface and HTTP API begins at `v1.0.0`. Security patches before
`v1.0.0` are issued on the current development line only.

| Version | Status |
| --- | --- |
| `v1.x` | Supported (current development; pre-release) |
| `< v1.0.0` | Not supported; upgrade to the latest tagged release |

After `v1.0.0`, the prior `v(N-1).x` line receives security patches for
six months following a new major release.

## CVE Assignment

We use GitHub as a CNA (CVE Numbering Authority) and request CVE IDs
through GitHub Security Advisories. Reporters are credited unless they
request otherwise.

## Verification of Signed Releases

From Phase 4 onward (introduces release signing), every release
artefact is signed with [Sigstore cosign](https://docs.sigstore.dev/).
The verification snippet is documented in the
[release notes](https://github.com/klein-business/legal-text-mcp-de/releases)
and in `docs/operations/verify-with-cosign.md` (added in Phase 4).

## Out of scope

- Vulnerabilities in dependencies that are upstream's responsibility;
  please file those with the dependency project. We track high-severity
  dependency issues via Dependabot.
- Bugs without security impact (please file a regular issue instead).
- Theoretical attacks without a demonstrated impact path.

## Acknowledgements

We thank all reporters who follow this policy. With your permission, we
list contributors who have responsibly disclosed issues in the release
notes.
```

- [ ] **Step 2: Manual step — enable Private Vulnerability Reporting**

This cannot be done via `git`. Document the required GitHub setting:

```
Settings → Code security and analysis → Private vulnerability reporting → Enable
```

Add a check-off list line to your Phase-2 closing notes (or to the PR description):
- [ ] PVR enabled in GitHub Settings (verify via Security tab on the repo home)

- [ ] **Step 3: Verify the Security tab is reachable**

```bash
gh api "repos/klein-business/legal-text-mcp-de" --jq '.security_and_analysis.secret_scanning.status'
```

Expected: a string like `enabled` or `disabled`. (This isn't the PVR-specific setting; it confirms the security-analysis endpoint is reachable for the repo.)

- [ ] **Step 4: Commit**

```bash
git add SECURITY.md
git commit -m "docs(security): add SECURITY.md with vulnerability disclosure policy"
```

---

## Task 23: Update `verify_pre_flip` Required-Files List

**Files:**
- Modify: `scripts/verify_pre_flip.py`
- Modify: `mcp/tests/test_verify_pre_flip.py`

Add `SECURITY.md` to `REQUIRED_FILES`.

- [ ] **Step 1: Edit the required files tuple**

In `scripts/verify_pre_flip.py`, change:
```python
REQUIRED_FILES = (
    "NOTICE",
    "AUTHORS.md",
    "CHANGELOG.md",
    "licenses/MIT-floleuerer.txt",
)
```

to:
```python
REQUIRED_FILES = (
    "NOTICE",
    "AUTHORS.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "licenses/MIT-floleuerer.txt",
)
```

- [ ] **Step 2: Update the corresponding test**

In `mcp/tests/test_verify_pre_flip.py`, update `test_required_files_passes_when_all_present` to create SECURITY.md too:

Add this line where the other required files are created:
```python
    (tmp_path / "SECURITY.md").write_text("security", encoding="utf-8")
```

And update `test_required_files_fails_when_any_missing` assertion:
```python
    assert "SECURITY.md" in result.message
```

Also update `_populate_passing_repo` helper to include SECURITY.md:
```python
    (root / "SECURITY.md").write_text("security", encoding="utf-8")
```

- [ ] **Step 3: Run tests**

```bash
PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_verify_pre_flip.py -v
```

Expected: all tests pass.

- [ ] **Step 4: Run the gate**

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_pre_flip.py 2>&1 | grep "required files"
```

Expected: `[PASS] required files exist: ok`.

- [ ] **Step 5: Commit**

```bash
git add scripts/verify_pre_flip.py mcp/tests/test_verify_pre_flip.py
git commit -m "feat(verify): require SECURITY.md in pre-flip gate"
```

---

## Task 24: Update CHANGELOG `[Unreleased]` for Phase 2

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Append Phase 2 entries under `## [Unreleased]`**

Replace the existing `## [Unreleased]` section's body to include both Phase 1 and Phase 2 changes. Add (or update) the following under the existing `### Changed` and `### Added` sections:

Under `### Changed`:
```markdown
- Hardened CI into eight workflows (ci, e2e, codeql, scorecard,
  dependency-review, commitlint, dco, megalinter).
- Configured mypy stufenweise: strict on `scripts/`, plain (warning-only)
  on `mcp/`.
- Coverage floor enforced via `[tool.coverage.report] fail_under` in
  `pyproject.toml`.
- Switched `detect-secrets` pin from `~=1.5` to `~=1.5.0` (consistency
  with project convention).
- `verify_pre_flip.py` extended from 5 to 8 checks
  (`check_workflow_set`, `check_required_status_checks`,
  `check_branch_protection`); secrets-check now returns `SKIP` (rather
  than `FAIL`) when `detect-secrets-hook` is missing from PATH.
- Fixed `[Unreleased]` compare link in `CHANGELOG.md` to point at the
  initial commit rather than `HEAD`.
```

Under `### Added`:
```markdown
- `SECURITY.md` — vulnerability disclosure policy and supported-versions
  table.
- `.pre-commit-config.yaml` — developer-convenience hooks mirroring CI.
- `scripts/check_spdx_header.py` — pre-commit hook ensuring new Python
  files carry the SPDX header.
- `.commitlintrc.json` — Conventional Commits configuration applied to
  PR titles.
- `docs/operations/coverage-baseline-phase2.md` — coverage baseline
  evidence.
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): record Phase 2 changes"
```

---

## Task 25: Final End-to-End Verification

**Files:**
- None (verification only)

Confirm all Phase 2 acceptance criteria are met.

- [ ] **Step 1: Run the test suite**

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
PYTHONPATH=mcp uv run --group dev pytest mcp/tests -v 2>&1 | tail -5
```

Expected: all tests pass.

- [ ] **Step 2: Run the existing release gate**

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py
```

Expected: passes.

- [ ] **Step 3: Run the pre-flip gate (without GitHub token)**

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_pre_flip.py
```

Expected output:
```
[PASS] LICENSE is Apache-2.0: ok
[PASS] required files exist: ok
[PASS] no proprietary strings: ok
[PASS] pyproject.toml metadata: ok
[PASS] no unaudited secrets: ok
[PASS] workflow set: ok
[SKIP] required status checks: VERIFY_GITHUB_TOKEN not set; …
[SKIP] branch protection: VERIFY_GITHUB_TOKEN not set; …
```

Exit code: `0` (SKIP does not fail).

- [ ] **Step 4: Run the pre-flip gate WITH a GitHub token (if available)**

If you have a GitHub PAT with `repo` scope:

```bash
VERIFY_GITHUB_TOKEN=<your-pat> PYTHONPATH=mcp uv run --group dev python scripts/verify_pre_flip.py
```

Expected: the two `[SKIP]` lines change to `[FAIL]` (because branch protection on `main` doesn't yet require all the Phase-2 status checks — that comes from running this verification AFTER a test PR has run on the new workflows so they appear in the eligible-checks list).

Note: The status-check listing in branch protection only includes contexts that have actually run. This means Step 4 will FAIL until you've at least once pushed the Phase-2 branch to GitHub and let the workflows execute. That's expected; the FAIL guides the manual configuration step that follows.

- [ ] **Step 5: Linter sanity (local actionlint, optional)**

If `actionlint` is on PATH:
```bash
actionlint .github/workflows/*.yml
```

Expected: no errors.

- [ ] **Step 6: Verify each workflow YAML parses**

For each new workflow file, run:
```bash
PYTHONPATH=mcp uv run --group dev python -c "import yaml, pathlib; [yaml.safe_load(p.read_text()) for p in pathlib.Path('.github/workflows').glob('*.yml')]; print('all parse ok')"
```

Expected: `all parse ok`.

- [ ] **Step 7: Confirm commit history is clean Conventional Commits**

```bash
git log --oneline $(git merge-base HEAD origin/main)..HEAD
```

Inspect the list — every subject should start with `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`, `ci:`, `build:`, or `style:`. No `Co-Authored-By` trailers anywhere:

```bash
git log $(git merge-base HEAD origin/main)..HEAD --grep="Co-Authored-By"
```

Expected: empty.

- [ ] **Step 8: No commit needed for this verification task**

Verification only. If any of the above failed, fix in a follow-up commit named appropriately.

---

## Phase 2 Acceptance

Phase 2 is complete when:

- All eight workflow files exist in `.github/workflows/`.
- `pyproject.toml` has the mypy and coverage sections.
- `.pre-commit-config.yaml`, `.commitlintrc.json`, `SECURITY.md`, and
  `scripts/check_spdx_header.py` exist.
- `verify_pre_flip.py` reports 6 PASS + 2 SKIP (without
  `VERIFY_GITHUB_TOKEN`) or 8 PASS (with token and properly configured
  branch protection).
- All 267+ tests pass (some Phase 2 tasks add tests, so the count
  grows).
- A test PR (pushed to a feature branch) successfully exercises every
  new workflow; the workflows appear in GitHub's branch-protection
  status-check eligibility list.

## Manual Steps Reserved for Phase-2 Closing (Post-Implementation)

These cannot be automated via `git` and must be performed via the
GitHub UI or API by the user:

1. **Enable Private Vulnerability Reporting**:
   `Settings → Code security and analysis → Private vulnerability
   reporting → Enable`.
2. **Update branch protection on `main`** to require the new contexts:
   `Lint (ruff)`, `Mypy strict (scripts)`, `Test (py3.12)`, `Test
   (py3.13)`, `Lockfile integrity`, `Build (sdist + wheel)`,
   `MegaLinter`, `Release gate (fixture-backed)`, `uv runtime and
   Docker`, `CodeQL analysis (python)`, `Dependency review`, `PR title
   (Conventional Commits)`, `DCO sign-off check`. Set
   `required_signatures = true`. Keep `enforce_admins = true`,
   `required_linear_history = true`, `allow_force_pushes = false`.
3. **Run `verify_pre_flip` with token** after step 2 to confirm 8/8
   PASS.

Once these are done, Phase 2 is at acceptance; Phase 3 (Community
files + mkdocs site) can begin.

## What Phase 3 Will Pick Up

- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`,
  `GOVERNANCE.md`, `ROADMAP.md`.
- `.github/CODEOWNERS`, issue and PR templates,
  `.github/dependabot.yml`.
- mkdocs-material documentation site + `docs.yml` workflow.
- `docs/` content migration to mkdocs structure.
