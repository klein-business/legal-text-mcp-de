# Quickstart with Docker

The Docker image does not bundle legal text data. Mount a generated
package at `/data/legal-texts`.

## Pull the image

```bash
docker pull ghcr.io/klein-business/legal-text-mcp-de:2.1.3
```

## Verify the signature

```bash
cosign verify ghcr.io/klein-business/legal-text-mcp-de:2.1.3 \
  --certificate-identity-regexp 'https://github.com/klein-business/.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

See [Verify with cosign](../operations/verify-with-cosign.md) for
details.

## Run

```bash
docker run --rm -p 8001:8001 \
  -v /path/to/legal-text-package:/data/legal-texts:ro \
  ghcr.io/klein-business/legal-text-mcp-de:2.1.3 serve
```

The container runs as UID 10001 (non-root). The dataset mount is
read-only.

## Build locally (development)

```bash
docker build -t legal-text-mcp-de:dev .
docker run --rm -p 8001:8001 \
  -v $(pwd)/mcp/tests/fixtures/normalized:/data/legal-texts:ro \
  legal-text-mcp-de:dev serve
```

## Verification

```bash
curl http://localhost:8001/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Expected: JSON response listing ten tools (9 v1 law tools +
`research_topic`).

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `DATASET_PATH` | `/data/legal-texts` | Path to the corpus inside the container. |
| `STRICT_STARTUP` | `false` | Fail fast on dataset errors when `true`. |
| `HOST` | `0.0.0.0` | Bind address inside the container. |
| `PORT` | `8001` | Port inside the container. |

## Related

- [uvx](uvx.md) — running without Docker.
- [Verify with cosign](../operations/verify-with-cosign.md) — image signature verification.
- [SBOM](../operations/sbom.md) — inspecting the image SBOM.
