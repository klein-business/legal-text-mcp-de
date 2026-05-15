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
