# Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## Stability contract

The stability contract begins at **v1.0.0**:

- **MCP tool signatures** (names, required parameters, return shapes) are stable
  across patch and minor releases.
- **HTTP routes** (paths, methods, response shapes) are stable across patch and
  minor releases.
- **Breaking changes** trigger a major version bump.

Before v1.0.0 (current state), any release may include breaking changes. The
`CHANGELOG.md` documents all changes.

## Version scheme

```
vMAJOR.MINOR.PATCH
```

| Component | When to increment |
| --- | --- |
| `MAJOR` | Breaking change to any public API (MCP tool signature, HTTP route, or dataset schema). |
| `MINOR` | New functionality that is backwards-compatible. |
| `PATCH` | Backwards-compatible bug fix. |

## Deprecation policy

Deprecated interfaces are announced in `CHANGELOG.md` and:

1. Deprecated in release N — marked with a warning in the docs and optionally
   a runtime warning.
2. Deprecated for two full minor releases (N and N+1).
3. Removed in N+2.

Emergency security fixes may bypass the deprecation cycle.

## Support policy

- **Current `v1.x`** — receives bug fixes and security patches.
- **Previous major** — once a `v2.0.0` exists, the previous `v1.x` receives
  security patches for 6 months, then is unsupported.

## Release automation

Releases are managed by
[`googleapis/release-please-action`](https://github.com/googleapis/release-please-action).
Conventional Commits on `main` accumulate into a release-please PR. Merging the
PR creates the tag and triggers `release.yml`, which:

1. Builds the wheel and sdist.
2. Generates a CycloneDX SBOM.
3. Produces SLSA-3 provenance.
4. Publishes to PyPI via Trusted Publisher.
5. Builds and signs the GHCR image with cosign.

## Changelog

Changes are documented in [`CHANGELOG.md`](https://github.com/klein-business/legal-text-mcp-de/blob/main/CHANGELOG.md)
following the [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) format.

## Related

- [SBOM](sbom.md) — inspecting the software bill of materials.
- [Verify with cosign](verify-with-cosign.md) — verifying release artefacts.
