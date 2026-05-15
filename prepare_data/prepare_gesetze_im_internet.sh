#!/bin/bash

set -euo pipefail

REPO_URL="https://github.com/bundestag/gesetze-tools"
DIR_NAME="gesetze-tools"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
    echo "Usage: $0 [--dry-run|--no-network]"
}

dry_run=false
for arg in "$@"; do
    case "$arg" in
        --dry-run|--no-network)
            dry_run=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            exit 2
            ;;
    esac
done

if [ "$dry_run" = true ]; then
    echo "Validating prepare-data dependencies through uv without network work..."
    uv run --project "$ROOT_DIR" --frozen --offline --group prepare-data --no-dev python -c "import git, yaml, docopt, lxml, cssselect, requests, bs4, roman_numbers"
    echo "Dry-run validation completed successfully."
    exit 0
fi

cd "$SCRIPT_DIR"

if [ -d "$DIR_NAME" ]; then
    echo "Directory '$DIR_NAME' already exists. Entering directory..."
else
    echo "Cloning repository from $REPO_URL..."
    git clone "$REPO_URL"
fi

cd "$DIR_NAME"

echo "Running lawde.py loadall..."
uv run --project "$ROOT_DIR" --frozen --group prepare-data --no-dev python lawde.py loadall

echo "Running lawdown.py convert laws laws_md..."
uv run --project "$ROOT_DIR" --frozen --group prepare-data --no-dev python lawdown.py convert laws laws_md

echo "Script execution completed successfully."
