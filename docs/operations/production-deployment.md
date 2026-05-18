# Production deployment

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

`Caddyfile`:

```caddyfile
legal.example.org {
    # Automatic Let's Encrypt + HTTP/3
    tls admin@example.org

    # Defence-in-depth security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        Content-Security-Policy "default-src 'none'; frame-ancestors 'none'"
        -Server
    }

    # Proxy-level body cap (app cap is independently enforced)
    request_body {
        max_size 1MB
    }

    reverse_proxy legal-text-mcp-de:8001 {
        health_uri /health
        health_interval 30s
        health_timeout 5s
    }
}
```

`docker-compose.yml`:

```yaml
services:
  legal-text-mcp-de:
    image: ghcr.io/klein-business/legal-text-mcp-de:2.1.3
    restart: unless-stopped
    environment:
      DATASET_PATH: /data/legal-texts
      STRICT_STARTUP: "true"
      MAX_REQUEST_BODY_BYTES: "1048576"
    volumes:
      - /srv/legal-corpus:/data/legal-texts:ro
    networks: [edge]

  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports: ["80:80", "443:443", "443:443/udp"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    networks: [edge]
    depends_on: [legal-text-mcp-de]

volumes:
  caddy_data:
  caddy_config:

networks:
  edge:
```

Bring up:

```bash
docker compose up -d
curl -fsSL https://legal.example.org/health    # -> {"status":"ok"}
```

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
