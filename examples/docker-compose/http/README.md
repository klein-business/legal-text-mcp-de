# Docker Compose HTTP Example

Boots `legal-text-mcp-de` in HTTP mode with no corpus mounted — the
server starts and `/health` responds, but `/laws` and `/search` return
errors until a corpus is bind-mounted.

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
