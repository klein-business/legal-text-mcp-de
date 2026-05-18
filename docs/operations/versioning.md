# Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## Stability contract

The stability contract begins at **v1.0.0** and continues through the
current **v2.0.0** GA:

- **MCP tool signatures** (names, required parameters, return shapes) are stable
  across patch and minor releases. The v1 → v2 transition added one new tool
  (`research_topic`) and kept all 9 v1 tool signatures byte-identical; the
  contract is frozen by `tests/test_v1_compat.py` going forward.
- **HTTP routes** (paths, methods, response shapes) are stable across patch and
  minor releases.
- **Breaking changes** trigger a major version bump.

The CLI invocation form (subcommand names, flag names, positional
argument order) is **not** part of the v1.0.0 stability contract. CLI
subcommand renames trigger a CHANGELOG entry with a clear migration
note, but no major version bump.

See [Migration v1 → v2](migration-v1-v2.md) for the v2.0 changes that required
the major bump (corpus distribution model, `DATASET_PATH` default,
`get_corpus_coverage` aggregate counts).

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

- **Current `v2.x`** — receives bug fixes and security patches.
- **Previous major (`v1.x`)** — receives security patches until 2026-11-17
  (6 months after `v2.0.0` GA), then unsupported.

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
