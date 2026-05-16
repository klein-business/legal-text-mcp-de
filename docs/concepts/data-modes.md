# Data modes

The runtime loads from one of three dataset shapes. The mode is chosen
implicitly by what `DATASET_PATH` points at.

## Fixture packages (CI mode)

Path: `mcp/tests/fixtures/normalized/` (committed).

- ~10 laws, ~34 norms.
- Deterministic, byte-stable.
- Used by the test suite and for `verify_release.py` fixture-backed
  gates.

Start the server with the fixture corpus:

```bash
DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
uv run python mcp/server.py
```

## Generated production package

Path: any directory containing a complete package manifest
(`package.json`, `manifest.json`, `laws.json`, `norms.json`,
`source-limitations.json`, `relationships.json`, `readiness.json`,
`search-index.json`).

- Built outside Git via the `prepare_data/` pipeline against official
  sources.
- Every source has a terminal state: `imported`,
  `unsupported_format`, `source_unavailable`, `parse_failed`, or
  `excluded_by_policy`.

## Mounted production package (runtime)

The Docker image expects a generated package mounted at
`/data/legal-texts`:

```bash
docker run --rm -p 8001:8001 \
  -v /path/to/legal-text-package:/data/legal-texts:ro \
  ghcr.io/klein-business/legal-text-mcp-de:v1.0.0
```

(Replace the path. Read-only mount is sufficient.)

## Choosing the mode

| Use case | Mode |
| --- | --- |
| Local development, CI tests | Fixture |
| Production deployment | Generated, mounted |
| Quick exploration | Fixture or downloaded generated package |

## STRICT_STARTUP

Set `STRICT_STARTUP=true` to cause the server to fail-fast on any
dataset validation error at startup. Recommended for production to
surface configuration issues before accepting traffic.

When `STRICT_STARTUP` is not set (or `false`), the server starts even
if the dataset has issues; requests to affected laws return structured
error responses.

## Related

- [Provenance](provenance.md) — what metadata every law and norm record carries.
- [Quickstart → Docker](../quickstart/docker.md) — mounting a production corpus.
