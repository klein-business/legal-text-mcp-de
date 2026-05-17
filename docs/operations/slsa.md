# SLSA-3 build provenance

Every release publishes SLSA-3 (level 3) build provenance for both
the Python distribution and the OCI image.

## Python wheel/sdist provenance

Generator:
[`slsa-framework/slsa-github-generator` Python builder](https://github.com/slsa-framework/slsa-github-generator/blob/main/internal/builders/generic/README.md).

The provenance is attached to the GitHub Release as
`slsa-python.intoto.jsonl` and uploaded to PyPI via PEP 740 by the
Trusted Publisher action.

Verify:

```bash
slsa-verifier verify-artifact \
  --provenance-path slsa-python.intoto.jsonl \
  --source-uri github.com/klein-business/legal-text-mcp-de \
  legal_text_mcp_de-1.0.0-py3-none-any.whl
```

## OCI image provenance

Generator:
[`slsa-framework/slsa-github-generator` Docker builder](https://github.com/slsa-framework/slsa-github-generator/blob/main/internal/builders/docker/README.md).

The provenance is attached to the GHCR image as a cosign attestation
and to the GitHub Release as `slsa-oci.intoto.jsonl`.

Verify via cosign:

```bash
cosign verify-attestation \
  --type slsaprovenance \
  --certificate-identity-regexp 'https://github.com/klein-business/.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/klein-business/legal-text-mcp-de:v2.0.0
```

## Why SLSA-3?

Level 3 requires:
- Hermetic, isolated builds.
- Build platform attesting to its own integrity.
- Source-tampering resistance.

GitHub-hosted runners + `slsa-github-generator` together meet these
requirements without per-project hardening work.
