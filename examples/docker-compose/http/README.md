# Docker Compose HTTP Example

Boots `legal-text-mcp-de` in HTTP mode against the bundled fixture
corpus shipped inside the image — no external corpus download needed
for the quickstart.

> **For production deployments** pin to a different image digest,
> set `STRICT_DATASET=true`, and bind-mount a real corpus archive at
> `/data/corpus/latest.tar.zst`. See
> [`docs/operations/production-deployment.md`](../../../docs/operations/production-deployment.md).

## Start

```bash
cd examples/docker-compose/http
docker compose up -d
```

## Verify

```bash
curl http://localhost:8001/health
```

Expected response: `{"status":"ok"}`.

## Stop

```bash
docker compose down
```
