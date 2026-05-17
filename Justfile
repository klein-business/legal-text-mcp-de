# Justfile for legal-text-mcp-de
# https://just.systems/
#
# Install: brew install just (macOS) or cargo install just (any OS)
# List targets: `just` or `just --list`
#
# All targets are thin wrappers around the canonical `uv` invocations so
# the contract stays in one place. See CONTRIBUTING.md for the manual
# equivalents.

set shell := ["bash", "-euo", "pipefail", "-c"]

# default target lists everything
default:
    @just --list

# Sync all dependency groups (dev + docs + prepare-data + hosted).
install:
    uv sync --all-groups

# Run the full test suite (dev + prepare-data needed for state scrapers).
test:
    uv run --group dev --group prepare-data pytest

# Run a single test by node-id, e.g. `just test-one tests/test_http_api.py::test_health_and_ready`
test-one ID:
    uv run --group dev pytest {{ID}} -v

# Ruff lint + format check.
lint:
    uv run --group dev ruff check .
    uv run --group dev ruff format --check .

# Auto-fix what ruff can fix + format.
fix:
    uv run --group dev ruff check --fix .
    uv run --group dev ruff format .

# Strict mypy on scripts/ (the gate that branch-protection requires).
typecheck:
    uv run --group dev mypy scripts

# Build docs locally with live-reload at http://127.0.0.1:8000.
docs:
    uv run --group docs mkdocs serve

# Run the MCP server against the committed fixture corpus.
run:
    DATASET_PATH=tests/fixtures/normalized STRICT_STARTUP=true uv run legal-text-mcp-de

# Run the HTTP API against the committed fixture corpus on :8080.
api:
    DATASET_PATH=tests/fixtures/normalized STRICT_STARTUP=true uv run uvicorn legal_text_mcp_de.http_api:app --host 127.0.0.1 --port 8080

# Verify the docs-link checker + the smoke test that release.yml runs.
verify-release:
    uv run --group dev python scripts/verify_release.py

# Full pre-flip checklist (used before flipping the repo to public).
verify-pre-flip:
    VERIFY_GITHUB_TOKEN="$(gh auth token)" uv run --group dev python scripts/verify_pre_flip.py

# Pre-commit hooks against all files (run once after editing many files).
pre-commit:
    uv run --group dev pre-commit run --all-files
