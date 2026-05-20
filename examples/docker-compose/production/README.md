# Production Docker Compose stack

A committed, CI-tested reference deployment of `legal-text-mcp-de` behind a
Caddy reverse proxy with automatic TLS. It exposes both transport surfaces,
selectable via Compose profiles:

- **`mcp`** — the MCP streamable-HTTP transport (`serve`), proxied at `/mcp`.
- **`rest`** — the FastAPI REST API (`http`), proxied under `/api/`.

Only Caddy publishes host ports (`80`/`443`); the app services are reachable
only on the internal Compose network.

## Prerequisites

- Docker Engine with Compose v2.20+ (`depends_on` `required:` support).
- A DNS record pointing your domain at the host (for Let's Encrypt).
- A prepared corpus directory on the host — see [Corpus](#corpus).

## Configure

```bash
cd examples/docker-compose/production
cp .env.example .env
```

Edit `.env`:

| Variable | What to set |
| --- | --- |
| `DOMAIN` | The public domain, e.g. `legal.example.org`. |
| `ACME_EMAIL` | Your email for the Let's Encrypt account. |
| `COMPOSE_PROFILES` | `mcp`, `rest`, or `mcp,rest`. |
| `IMAGE` | Digest-pinned image; bump on upgrades. |
| `CORPUS_HOST_PATH` | Absolute host path to the corpus directory. |
| `MAX_REQUEST_BODY_BYTES` | App-layer body cap (default 1 MiB). |

## Start

```bash
docker compose up -d
```

With the default `COMPOSE_PROFILES=mcp` this starts `serve` + `caddy`. Set
`COMPOSE_PROFILES=mcp,rest` to run both surfaces.

## Verify

```bash
curl -fsSL https://<your-domain>/health      # -> {"status":"ok"}
```

The MCP endpoint is `https://<your-domain>/mcp`; the REST API (profile
`rest`) is under `https://<your-domain>/api/` (e.g. `/api/laws`).

## Stop

```bash
docker compose down
```

## Corpus

The image ships no corpus. Produce a normalized corpus directory (see
[`docs/features/data-preparation.md`](../../../docs/features/data-preparation.md))
and point `CORPUS_HOST_PATH` at it. It is bind-mounted read-only at
`/data/legal-texts`; `STRICT_DATASET` and `STRICT_STARTUP` make the
container fail fast if the corpus is missing or invalid.

## Local testing without a public domain

Caddy needs a real domain for Let's Encrypt. To test the full stack
locally, set `DOMAIN=localhost` and replace `tls {$ACME_EMAIL}` in the
`Caddyfile` with `tls internal` — Caddy then issues its own local CA
certificate. The CI smoke test (`scripts/verify_uv_runtime_docker.py`)
skips Caddy and boots the app services directly.

## Alternative: subdomain split

Instead of path-based routing (`/mcp`, `/api/`), give each surface its own
subdomain. Replace the single site block in the `Caddyfile` with two
blocks — `mcp.<domain>` reverse-proxying `serve:8001` and `api.<domain>`
reverse-proxying `http:8001` — and add DNS records for both.

## Related

- [`docs/operations/production-deployment.md`](../../../docs/operations/production-deployment.md)
  — TLS, body limits, rate limiting, health checks, nginx alternative.
- [`../http/`](../http/) — the minimal HTTP-mode quickstart example.
