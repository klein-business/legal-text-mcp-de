# Governance

This project follows a benevolent-dictator-for-life (BDFL) model with
the maintainer
([@klein-business](https://github.com/klein-business)) as the sole
decision-maker on direction, scope, and code merges.

## Decision-making

- Routine changes (bug fixes, dependency bumps, documentation
  improvements): a single maintainer review approves merge.
- Larger changes (new MCP tools, schema changes, architectural
  refactors): discussion in a GitHub issue or Discussion thread
  precedes the PR. Decisions are recorded on the issue.
- Disagreement on direction: the maintainer's decision is final.
  Contributors who disagree may fork.

## Branch protection bypass

`main` is protected with required status checks, signed-commit
enforcement, and a one-reviewer requirement. For solo-maintainer
operation, `@klein-business` is on the bypass allowlist for
`required_pull_request_reviews`. Bypass uses are recorded in the
GitHub branch-protection audit log; the maintainer reviews the log
periodically.

## Co-maintainers

The project is open to additional maintainers. Path to co-maintainer
status:

1. A sustained pattern of high-quality contributions (typically six
   or more accepted PRs over three months, mix of features and bug
   fixes).
2. Demonstrated alignment with the project's scope-discipline (no
   legal advice; provenance-first; OSS Tier-C quality bars).
3. Maintainer invitation, accepted in writing on a GitHub Discussion.
4. Trial period of three months as a reviewer (write access without
   admin) before promotion to full maintainer.

## Roadmap

The roadmap lives in [ROADMAP.md](ROADMAP.md) and is updated
periodically. Open issues with the label `roadmap` track planned
work. The maintainer accepts roadmap proposals through Discussions
or RFC issues.

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Reports go to
`martin@klein.business`.

## Licence

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
