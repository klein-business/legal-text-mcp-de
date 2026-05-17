# Verify with cosign

Every OCI image released since v1.0.0 is signed with
[Sigstore cosign](https://docs.sigstore.dev/) using keyless OIDC
signing from GitHub Actions. Examples below use the current image tag
`2.0.0`; substitute the tag you actually pulled.

## Install cosign

[Cosign installation instructions](https://docs.sigstore.dev/system_config/installation).

Via Homebrew:

```bash
brew install cosign
```

## Verify the signature

```bash
cosign verify ghcr.io/klein-business/legal-text-mcp-de:2.0.0 \
  --certificate-identity-regexp 'https://github.com/klein-business/.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

Expected output: a JSON object listing the certificate, the workflow
identity, and confirming the signature is valid. Non-zero exit
indicates verification failure.

## Verify SBOM and SLSA attestations

```bash
cosign verify-attestation \
  --type cyclonedx \
  --certificate-identity-regexp 'https://github.com/klein-business/.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/klein-business/legal-text-mcp-de:2.0.0

cosign verify-attestation \
  --type slsaprovenance \
  --certificate-identity-regexp 'https://github.com/klein-business/.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/klein-business/legal-text-mcp-de:2.0.0
```

Both return JSON predicates with the expected types when verification
succeeds.

## Why no signing key?

Keyless signing ties each signature to the build identity (the
GitHub Actions workflow run that produced it). Verification checks
that the certificate was issued to the project's repo and a workflow
the maintainer controls. There is no long-lived private key to leak.

## What if verification fails?

Stop. Verification failure means the image was modified, the
signature was forged, or you are pulling from a fork that isn't
ours. Open a security issue (see
[SECURITY.md](https://github.com/klein-business/legal-text-mcp-de/blob/main/SECURITY.md))
before using the image.

## Related

- [SBOM](sbom.md) — inspecting the software bill of materials.
- [Versioning](versioning.md) — release process overview.
