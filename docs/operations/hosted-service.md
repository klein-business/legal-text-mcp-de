# Hosted MCP service operations

## URLs

- **Production:** https://mcp.klein.business/legal/de
- **Staging:**   https://staging-mcp.klein.business/legal/de
- **Privacy:**   https://mcp.klein.business/privacy
- **Terms:**     https://mcp.klein.business/terms
- **Health:**    https://mcp.klein.business/health
- **Metrics:**   https://mcp.klein.business/metrics (internal only)

## Topology

```
[Internet] → Caddy (TLS + CSP) → legal-text-mcp-de container (×N) → /data/corpus mount
```

## Deploy

```bash
# Tag and image must already exist on GHCR
./deployment/deploy.sh 2.0.0-rc.4
```

## Rollback

```bash
./deployment/deploy.sh 2.0.0-rc.3   # previous stable
```

## Corpus refresh

Daily cron pulls latest bundle from S3 → swaps `/data/corpus/latest.tar.zst` symlink atomically.

## Soak testing

- New tags first ship to staging
- Verify zero SEV≥2 incidents for 2 weeks before promoting to production

## Production promotion checklist

Before promoting a tag from staging to production:

- [ ] Staging has run the tag for ≥ 2 weeks
- [ ] No SEV≥2 incidents in that window
- [ ] /metrics shows P95 latency < 500ms for get_norm (warm cache)
- [ ] /health returns status=ok consistently
- [ ] CodeQL, Trivy, Gitleaks all green on the source commit
- [ ] CHANGELOG updated with any operational notes
- [ ] DNS TTL lowered before swap, restored after
- [ ] On-call notified

> Record the promotion in docs/operations/soak-test.md with verdict "OK for promotion to prod".
