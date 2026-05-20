# Production deployment

> **Looking for a minimal starting point?** A copy-pasteable Docker Compose
> example for HTTP-mode deployment lives at
> [`examples/docker-compose/http/`](https://github.com/klein-business/legal-text-mcp-de/tree/main/examples/docker-compose/http).
> It boots the HTTP server on port 8001 with no corpus mounted — a
> healthcheck and image-digest pin are baked in. The two reverse-proxy
> patterns below extend that baseline with TLS termination, rate
> limiting, and the production-grade settings the example deliberately
> omits.

The HTTP API runs as a bare `uvicorn` on `http://0.0.0.0:8001`. For
production exposure you need:

1. **TLS termination** (Let's Encrypt or your own CA).
2. **A request body size limit** at the proxy layer (in addition to
   the app-layer `MAX_REQUEST_BODY_BYTES` cap — see
   [HTTP API overview](../api/index.md)).
3. **Rate limiting** per IP and per bearer token (deployment-specific;
   the app does not enforce this itself, only the optional hosted
   deployment in `deployment/ratelimit_middleware.py` does).
4. **A process supervisor** that restarts the container on failure
   (`docker compose`, `systemd`, Kubernetes — your choice).

Two reference reverse-proxy configurations follow. Both fall back to
the GHCR container as the upstream; replace `legal-text-mcp-de` with
`legal-text-mcp-de-full` if you want the bundle-included variant.

## Option 1 — Caddy (TLS-by-default, recommended)

A committed, CI-tested reference stack lives at
[`examples/docker-compose/production/`](../../examples/docker-compose/production/).
It runs both transport surfaces (MCP `serve` and the FastAPI `http` API),
selectable via Compose profiles, behind Caddy with automatic Let's Encrypt
TLS, the security headers and proxy-level body cap described above, and a
read-only corpus mount.

```bash
cd examples/docker-compose/production
cp .env.example .env      # then edit DOMAIN, ACME_EMAIL, IMAGE, CORPUS_HOST_PATH
docker compose up -d
curl -fsSL https://<your-domain>/health    # -> {"status":"ok"}
```

See the
[example README](../../examples/docker-compose/production/README.md)
for profile switching, corpus preparation, and local testing with
`tls internal`.

## Option 2 — nginx (manual cert config)

`nginx.conf` (or a server block in `sites-enabled/`):

```nginx
server {
    listen 443 ssl http2;
    server_name legal.example.org;

    ssl_certificate     /etc/letsencrypt/live/legal.example.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/legal.example.org/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Defence-in-depth headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Content-Security-Policy "default-src 'none'; frame-ancestors 'none'" always;
    server_tokens off;

    # Proxy-level body cap (app cap is independently enforced)
    client_max_body_size 1m;

    # Health endpoint for upstream monitoring (no logging)
    location = /health {
        access_log off;
        proxy_pass http://127.0.0.1:8001/health;
    }

    location / {
        proxy_pass         http://127.0.0.1:8001;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
        proxy_send_timeout 30s;
    }
}

server {
    listen 80;
    server_name legal.example.org;
    return 301 https://$host$request_uri;
}
```

Run the container behind it (systemd unit, native install, or:

```bash
docker run -d --name legal-text-mcp-de --restart unless-stopped \
  -p 127.0.0.1:8001:8001 \
  -v /srv/legal-corpus:/data/legal-texts:ro \
  -e DATASET_PATH=/data/legal-texts \
  -e STRICT_STARTUP=true \
  -e MAX_REQUEST_BODY_BYTES=1048576 \
  ghcr.io/klein-business/legal-text-mcp-de:2.1.3 serve
```

```bash
sudo nginx -t && sudo systemctl reload nginx
curl -fsSL https://legal.example.org/health    # -> {"status":"ok"}
```

## Health checking

The container exposes `/health` (lightweight) and `/ready`
(includes dataset readiness). For Kubernetes:

```yaml
readinessProbe:
  httpGet: { path: /ready, port: 8001 }
  initialDelaySeconds: 5
  periodSeconds: 10
livenessProbe:
  httpGet: { path: /health, port: 8001 }
  periodSeconds: 30
```

## Logging + observability

The Hosted-deployment variant
(`deployment/anonymised_logging.py`, `deployment/metrics.py`) adds:
- per-request JSON log lines (method, path, status, latency, UA bucket
  — no bodies, no PII)
- Prometheus `/metrics` endpoint

If you want those, build with `deployment/Dockerfile.hosted` instead
of the default image. Otherwise run plain `uvicorn` and pipe stdout
to your log shipper.

## Related

- [HTTP API overview](../api/index.md) — body-size cap details
- [Security](security.md) — full threat model and mitigations
- [Hosted-service operations](hosted-service.md) — `mcp.klein.business/legal/de` runbook
- [Verify with cosign](verify-with-cosign.md) — image signature verification before deploy
