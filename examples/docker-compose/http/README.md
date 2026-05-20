# Docker Compose HTTP Example

Boots `legal-text-mcp-de` in HTTP mode against the bundled fixture
corpus shipped inside the image — no external corpus download needed
for the quickstart.

> **For a production stack** — both transport surfaces behind Caddy with
> TLS, Compose profiles, and a corpus mount — see the committed
> [`../production/`](../production/) example. Background and the nginx
> alternative are in
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
