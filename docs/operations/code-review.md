# Code review

The repo runs a five-layer review stack. Every PR passes through all
five before landing on `main`. The first three are automated and
deterministic; the fourth is automated and semantic; the fifth is
human.

## Layer 1 — Branch protection on `main`

Configured via the GitHub branch-protection API. Snapshot
(`gh api repos/.../branches/main/protection`):

| Setting | Value |
| ------- | ----- |
| `required_signatures` | `true` (SSH-signed commits required) |
| `required_status_checks` | 14 contexts (see Layer 3 below) |
| `required_pr_reviews.required_approving_review_count` | `1` |
| `required_pr_reviews.dismiss_stale_reviews` | `true` |
| `required_pr_reviews.require_code_owner_reviews` | `false` (we have one CODEOWNERS entry) |
| `required_linear_history` | `true` (no merge commits) |
| `enforce_admins` | `true` (admins are subject to the same gates) |

The `enforce_admins: true` setting means even a maintainer with
`--admin` privileges cannot merge a PR with failing required checks.
The one documented exception — described in [Edge cases](#edge-cases)
below — is the maintainer-fixup-on-fork-PR pattern, where two of the
14 checks fail by design and a brief `enforce_admins` toggle is the
clean way through.

## Layer 2 — CODEOWNERS

[`.github/CODEOWNERS`](https://github.com/klein-business/legal-text-mcp-de/blob/main/.github/CODEOWNERS)
maps every path to `@klein-business`. Solo-maintainer model today;
when a second maintainer joins, paths can be carved out per area
(e.g., `docs/ @docs-team`, `src/legal_text_mcp_de/legal_texts/ @parser-team`).

`require_code_owner_reviews: false` is intentional: with a single
CODEOWNER, `required_pr_reviews: 1` already covers the same intent.

## Layer 3 — Deterministic CI

Every PR must pass these 14 status checks before
merge:

| Check | Tool | Blocks merge | Notes |
| ----- | ---- | :---: | ----- |
| `Build (sdist + wheel)` | `uv build` | ✅ | Confirms PyPI artefacts build deterministically. |
| `Test (py3.12)` | pytest | ✅ | 547+ tests against the fixture corpus. Coverage floor `86 %` combined (statement + branch). |
| `Test (py3.13)` | pytest | ✅ | Same suite on the next supported Python. |
| `Lint (ruff)` | ruff check + format --check | ✅ | Single source of style. |
| `Mypy strict (scripts)` | mypy --strict | ✅ | Build/release scripts. |
| `Mypy strict (cli + http_api)` | mypy --strict | ✅ | Ratcheted user-facing API surface (see [openssf-application](openssf-application.md) §Warning flags). |
| `Mypy plain (src) [non-blocking]` | mypy | — | Warning gate on the rest of `src/`. |
| `Release gate (fixture-backed)` | `scripts/verify_release.py` | ✅ | Docs link check + fixture-backed E2E. |
| `uv runtime and Docker` | `scripts/verify_uv_runtime_docker.py` | ✅ | Build + run the standard image. |
| `MegaLinter` | meta-linter | ✅ | Markdown, YAML, shell, secret scan. |
| `CodeQL analysis (python)` | GitHub CodeQL | ✅ | Static security analysis. |
| `Trivy image scan` | aquasecurity/trivy | ✅ | Container CVE scan. |
| `Gitleaks scan` | gitleaks | ✅ | Secret scan. |
| `DCO sign-off check` | tim-actions/dco | ✅ | Every commit needs `Signed-off-by:`. |
| `Dependency review` | actions/dependency-review | ✅ | Blocks high-severity new deps. |
| `Lockfile integrity` | `uv lock --locked` check | ✅ | `uv.lock` matches `pyproject.toml`. |
| `PR title (Conventional Commits)` | amannn/action-semantic-pull-request | ✅ | PR title must match `feat:` / `fix:` / `docs:` / … |
| `CodeRabbit` | Layer 4 (see below) | — | Reported as a check but does not block (`request_changes_workflow: false`). |

All `uses:` references in `.github/workflows/` are pinned by SHA, not
by tag (OSSF Scorecard `Pinned-Dependencies` check). Re-pin happens
via Dependabot's weekly scan.

## Layer 4 — AI review (CodeRabbit)

[CodeRabbit Pro Plus](https://www.coderabbit.ai) is free forever for
public OSS repos. It posts a per-PR walkthrough (high-level summary,
sequence diagrams for cross-module changes, file-list summary,
estimated review effort) and inline suggestions with code-block
diffs. It also runs five pre-merge checks (description, title,
docstring coverage, linked issues, out-of-scope changes).

Behaviour is driven by [`.coderabbit.yaml`](https://github.com/klein-business/legal-text-mcp-de/blob/main/.coderabbit.yaml)
at the repo root, version-controlled like any other config:

| Setting | Value | Why |
| ------- | ----- | --- |
| `language: en-US` | English review comments | Matches repo language. |
| `tone_instructions` (≤ 250 chars) | "Direct, concise, professional. Suggest fixes as code-block diffs…" | German engineering culture, English output. |
| `reviews.profile: chill` | Friendly, less nitpicky | vs `assertive`. |
| `reviews.request_changes_workflow: false` | Bot never casts a hard "Changes Requested" | Branch protection is the gate, not the bot. |
| `reviews.poem: false` | No auto-generated poem in walkthroughs | Removes noise. (See [Edge cases](#edge-cases) — does not apply to fork PRs whose feature branch lacks `.coderabbit.yaml`.) |
| `reviews.auto_review.base_branches: [main]` | Explicit base-branch list | The default `[]` failed to resolve to the actual default branch on initial install. |
| `reviews.auto_review.drafts: false` | Skip WIP PRs | Saves quota. |
| `reviews.path_filters` (12 entries) | Exclude `docs-legacy/`, `docs/superpowers/`, fixtures, locks, caches, assets | Keeps reviews focused on real code. |
| `reviews.path_instructions` (9 entries) | Domain conventions per path | E.g., `cli/*` strict mypy + `EXIT_*` constants; `server.json` OCI registry rules (no `registryBaseUrl`, version-in-identifier); `.github/workflows/*` SHA-pin + 4-layer `workflow_run` guard. |
| `reviews.labeling_instructions` | `documentation`, `dependencies` heuristics; `good first issue` never auto-applied | Curated by maintainers. |
| `chat.allow_non_org_members: true` | Fork-PR contributors can use `@coderabbitai` | Important for the contributor funnel. |
| `knowledge_base.opt_out: false` | Let the bot learn this codebase's patterns over time | Scoped per repo. |

The catch: CodeRabbit reads `.coderabbit.yaml` only from the PR's
*source* branch, not from `main`. Fork PRs from branches created
before the config landed get the bot's defaults. This is tracked
as a feature request on
[coderabbitai/awesome-coderabbit#21](https://github.com/coderabbitai/awesome-coderabbit/issues/21).

## Layer 5 — Human review

A maintainer (currently `@klein-business`) reviews every PR before
merge. Solo-maintainer mode today; OpenSSF Best Practices Gold
criterion `two_person_review` is the dominant blocker on the path
from Silver to Gold — see
[openssf-application](openssf-application.md) §Gold pathway.

For first-time external contributors, the maintainer's review tone
follows the
[CONTRIBUTING](https://github.com/klein-business/legal-text-mcp-de/blob/main/CONTRIBUTING.md)
"Your first contribution" onramp: friendly, specific, with concrete
diffs. Don't push to the contributor's branch on the first review
cycle — give them time to react.

## Edge cases

### Fork PR from a first-time contributor with two pre-merge failures by design

The DCO check insists every commit carries a `Signed-off-by:` line
that matches the commit's author. A first-time fork contributor who
runs `git commit` (without `-s`) ships an unsigned commit. A
maintainer who pushes a fixup with `git commit -s` cannot
retroactively sign on the contributor's behalf — the DCO check
correctly stays red.

Similarly, the `PR title (Conventional Commits)` check writes a
commit-status via the `GITHUB_TOKEN` available to fork-PR workflows.
Fork PRs get a read-only token by default, so the status write fails
even when the title itself is valid Conventional Commits. The check
shows red even after the maintainer fixes the title.

The clean way through, used by the `docs(examples)` merge for
[PR #107](https://github.com/klein-business/legal-text-mcp-de/pull/107):

1. Push the fixup commit (`-s -S`, Co-Authored-By trailer) to the
   contributor's branch via "Allow edits by maintainers" (default-on).
2. Rename the PR title to Conventional Commits format.
3. Dismiss any stale `CHANGES_REQUESTED` reviews from the same maintainer
   (GitHub blocks self-approval but allows self-dismissal).
4. Temporarily flip `enforce_admins: false` via
   `gh api -X DELETE repos/.../branches/main/protection/enforce_admins`.
5. `gh pr merge --squash --admin` with a curated `--subject` and `--body`
   that preserves attribution (Co-Authored-By trailer in the body, the
   contributor remains the squash commit's primary author).
6. Re-enable `enforce_admins: true` immediately
   (`gh api -X POST .../enforce_admins`). The exposure window is on the
   order of seconds.

This pattern is acceptable because the squashed commit landing on
`main` has its own clean `Signed-off-by:` from the merging maintainer.
The DCO failure on the PR was a process artefact, not a legal one.

### Scorecard `Dangerous-Workflow` false positive

The `mcp-registry.yml` workflow uses a `workflow_run` trigger that
fires after `release.yml` succeeds on a tag. An earlier revision
pinned `actions/checkout` to
`ref: github.event.workflow_run.head_sha`, which OSSF Scorecard
flags as untrusted-code-checkout. In this repo the risk is
structurally absent (the upstream `release.yml` only listens for
`push: tags: v*.*.*`, never `pull_request`), but the static
analyzer cannot see that.

The fix in [PR #106](https://github.com/klein-business/legal-text-mcp-de/pull/106):

- The job `if:` checks four layers (`event_name`, `workflow_run.conclusion`,
  `workflow_run.event == 'push'`, `head_branch` matches v-tag shape).
- The `actions/checkout` step drops the dynamic `ref:` entirely —
  defaults to `github.ref = refs/heads/main` in workflow_run context,
  which Scorecard recognises as safe.
- A "Verify server.json version matches triggering tag" guard catches
  the rare case where `main` has moved past the just-pushed tag
  between `release.yml` finishing and `mcp-registry.yml` starting.

Documented in [security-review-2026-05](security-review-2026-05.md)
§Known false positive.

## Related

- [OpenSSF application](openssf-application.md) — full breakdown of
  Best Practices Silver criteria and the Gold pathway.
- [Security review (2026-05)](security-review-2026-05.md) — Scorecard
  structural deductions and known false positives.
- [Versioning](versioning.md) — how release-please orchestrates the
  release that all five layers gate.
- [MCP Registry distribution](../features/mcp-registry-distribution.md)
  — the post-release workflow that consumes the layer-3-blessed
  artefacts.
