# Launch procedure

This document is the runbook for the v1.0.0 public flip. Execute the
steps in order. Each step is an explicit, mechanically-verifiable
action.

## Pre-flight (mechanical)

```bash
VERIFY_GITHUB_TOKEN=<your-PAT-with-repo-scope> \
  PYTHONPATH=mcp uv run --group dev python scripts/verify_pre_flip.py
```

Expected: 11/11 PASS. If anything fails, fix it before continuing.

## One-time PyPI setup

1. Go to <https://pypi.org/manage/account/publishing/>.
2. Click "Add a new pending publisher".
3. Fill in:
   - Project name: `legal-text-mcp-de`
   - Owner: `klein-business`
   - Repository: `legal-text-mcp-de`
   - Workflow filename: `release.yml`
   - Environment name: `pypi`
4. Save.

## One-time GitHub Pages setup

1. Settings → Pages.
2. Source: `Deploy from a branch` → `gh-pages` → `/ (root)`.
3. Save. (The branch is auto-created by `docs.yml` on first push to `main`.)

To bootstrap the `gh-pages` branch before the first docs deployment,
the `docs.yml` workflow runs automatically on every push to `main`.
No manual branch creation is needed.

## GitHub Settings changes for public flip

1. Settings → General → Visibility → Public. Confirm.
2. Settings → Code security and analysis:
   - Private Vulnerability Reporting → Enable.
   - Secret Scanning → Enable.
   - Push Protection → Enable.
3. Settings → General → Features:
   - Discussions → Enable.
   - Wiki → Disable.
4. Settings → About:
   - Description: "Python MCP server and HTTP API for German legal
     texts with source provenance."
   - Homepage URL: `https://klein-business.github.io/legal-text-mcp-de`.
   - Topics: `mcp`, `mcp-server`, `model-context-protocol`,
     `claude-desktop`, `legal-tech`, `german-law`, `gesetze`,
     `dsgvo`, `gdpr`, `python`, `fastapi`.

## Branch protection updates

Settings → Branches → main → Edit. Required status checks (add
new contexts from Phase 3+4):

The exact list is asserted by `verify_pre_flip.check_required_status_checks`.
Ensure `required_signatures = true`.

## Push the v1.0.0 tag

Two options:

### Option A — let release-please drive it

Merge any open release-please PR titled "chore: release 1.0.0". This
creates and pushes the tag automatically and triggers `release.yml`.

### Option B — manual tag push

```bash
git tag -s v1.0.0 -m "v1.0.0"
git push origin v1.0.0
```

(`-s` signs the tag with the maintainer's GPG key. `required_signatures
= true` enforces signed tags.)

## Post-flip verification

```bash
# PyPI
pip install legal-text-mcp-de==1.0.0
legal-text-mcp-de --version

# GHCR
docker pull ghcr.io/klein-business/legal-text-mcp-de:v1.0.0
cosign verify ghcr.io/klein-business/legal-text-mcp-de:v1.0.0 \
  --certificate-identity-regexp 'https://github.com/klein-business/.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com

# Docs site
curl -fsSL -o /dev/null https://klein-business.github.io/legal-text-mcp-de
echo "docs site exit: $?"
```

All three commands should succeed.

## Day-1 actions

1. File the OpenSSF Best Practices Silver application using the
   pre-drafted answers in
   [openssf-application.md](openssf-application.md). URL:
   <https://bestpractices.coreinfrastructure.org>.
2. Optional: PR onto `awesome-mcp-servers`.
3. Optional: announcement posts (HN, LinkedIn, Reddit). User-driven;
   not part of the engineering scope.

## Rollback plan

Within 24 hours of flip, if a critical issue surfaces:

1. Settings → Visibility → Private (immediate).
2. `pypi yank legal-text-mcp-de 1.0.0 --reason "<text>"` — keeps
   existing installs working but blocks new ones.
3. Delete GHCR tags via the GitHub Container Registry UI; the image
   digests remain (compliance) but tags are gone.
4. Communicate via a GitHub Discussion announcement and a CHANGELOG
   entry.
