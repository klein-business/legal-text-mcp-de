# Docker Compose: working example + production reference

- **Date:** 2026-05-20
- **Status:** Approved (brainstorming) — pending implementation plan
- **Scope:** Fix the broken HTTP Compose example and the MCP-mode health
  check; add a committed, tested production Compose reference.

## 1. Context & problem

The repository ships a Docker Compose example for HTTP-mode deployment
(`examples/docker-compose/http/`, merged in #107) and documents production
deployment in `docs/operations/production-deployment.md`. Three concrete
problems.

### 1.1 The merged example does not work

`examples/docker-compose/http/compose.yml` runs `legal-text-mcp-de http` and
sets `PORT=8001`. But `_run_http` in `src/legal_text_mcp_de/cli/_server.py:51`
hard-codes the bind port to `8080` and never reads the `PORT` environment
variable:

```python
effective_port = port if port is not None else 8080
```

This contradicts the function's own docstring, which states it falls back to
"the env-driven settings (HOST/PORT/DATASET_PATH)". Consequences:

- The container's FastAPI app binds `:8080`, not `:8001`.
- The Compose `ports: "8001:8001"` mapping points at a dead container port.
- The example README's verification step (`curl http://localhost:8001/health`)
  fails with connection refused.
- The Dockerfile `HEALTHCHECK` (hard-coded to `:8001`) fails.

`_run_mcp` (the `serve` command) does it correctly via `settings.port`. Only
the `http` command is affected.

### 1.2 Production deployment is documentation-only

`docs/operations/production-deployment.md` carries Compose snippets only as
copy-pasteable Markdown — nothing committed, nothing tested, free to drift out
of sync with the codebase. The HTTP example covers only the bundled-fixture
quickstart; real operation (mounted corpus, `STRICT_DATASET`, TLS, rate
limiting) is prose.

### 1.3 MCP `serve` mode has no `/health` endpoint

`/health` is registered only on the FastAPI app (`http_api.py:112`).
`create_mcp_app` (FastMCP) registers no such route, so the MCP `serve`
transport does not answer `/health`. The Dockerfile `HEALTHCHECK` probes
`:8001/health` and the default `CMD` is `serve` — so every `serve`-mode
container is permanently `unhealthy`. This is currently unnoticed because
nothing gates on health status (`scripts/verify_uv_runtime_docker.py` never
inspects it), but it also breaks the Kubernetes `livenessProbe` example in
`production-deployment.md` and blocks a health-gated `depends_on` in the
production Compose file (§4.2).

### 1.4 Known but out of scope

The `deployment/` directory (the `mcp.klein.business` hosted service) is
internally inconsistent — `deployment/Caddyfile` proxies the Compose DNS name
`legal-text-mcp-de:8001` while `deployment/deploy.sh` starts containers with
plain `docker run` under `-blue`/`-green` names and no shared network; and
`deployment/Dockerfile.hosted` pins base image `2.1.0` while the project is at
v2.1.3. This is real but deliberately excluded — see §6.

## 2. Goals / non-goals

**Goals**

- The merged HTTP Compose example works exactly as its README documents.
- The MCP `serve` transport answers `/health`, so the shipped image's
  `HEALTHCHECK` and the Kubernetes liveness example are correct, and both
  transport surfaces are symmetric.
- A committed, runnable, CI-tested production Compose reference exists,
  exposing both transport surfaces (MCP `serve`, FastAPI `http`) switchable
  via Compose profiles, behind a Caddy reverse proxy.
- `production-deployment.md` references the committed file instead of carrying
  drift-prone inline snippets.

**Non-goals**

- Reworking the `deployment/` hosted-service directory.
- An nginx variant as a committed artifact (stays as prose).
- Rate-limiting middleware, Kubernetes/Helm manifests.

## 3. Part A — Code fixes

Two small server-side fixes, both verified by unit tests.

### 3.1 `_run_http` port fix

In `src/legal_text_mcp_de/cli/_server.py`, `_run_http`:

```python
effective_port = port if port is not None else settings.port
```

`settings.port` reads the `PORT` environment variable and defaults to `8001`
(`src/legal_text_mcp_de/config.py:13`). This aligns `_run_http` with its own
docstring and with `_run_mcp`.

### 3.2 Behavioural change (accepted)

The bare default of `http` (no `--port`, no `PORT`) moves **8080 → 8001**.

- `legal-text-mcp-de http --port 8080` continues to work (explicit flag).
- The `--port` help text in `_server.py:74` ("default 8080") is corrected to
  "default from PORT env or 8001".
- Trade-off: `serve` and a bare `http` now share `8001`; running both locally
  at once requires an explicit `--port`. Consistency is preferred over the
  previous implicit port avoidance.
- No existing test hard-codes the `8080` default (verified — `tests/` contains
  no reference to `8080` or the `http` command).

### 3.3 MCP `serve` `/health` route

`create_mcp_app` in `src/legal_text_mcp_de/server.py` registers a `/health`
route on the FastMCP app via the SDK's `custom_route` decorator (mcp 1.27.1):

```python
@app.custom_route("/health", methods=["GET"])
async def _health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})
```

`custom_route` is the SDK's documented mechanism for public, unauthenticated
endpoints such as health checks. The route returns the same `{"status":"ok"}`
payload as the FastAPI `/health`, so the Dockerfile `HEALTHCHECK` succeeds in
`serve` mode and both transport surfaces become symmetric.

### 3.4 Verification

- A regression test in `tests/test_cli/test_server.py` asserts that `_run_http`
  passes `settings.port` to the uvicorn bind when no `--port` is given, and
  that an explicit `--port` still wins (monkeypatching `uvicorn.run`).
- A test in `tests/test_server.py` boots `create_mcp_app().streamable_http_app()`
  with a Starlette `TestClient` and asserts `GET /health` returns `200` and
  `{"status":"ok"}`.
- `examples/docker-compose/http/compose.yml` needs no functional change — once
  the Part A fix lands, its `PORT=8001` takes effect and the `:8001`
  healthcheck turns green. Its misleading comment ("bundled fixture corpus
  shipped inside the image" — the image ships only reference metadata, not a
  queryable corpus) is corrected to accurate wording.

## 4. Part B — `examples/docker-compose/production/`

A new directory, sibling to `examples/docker-compose/http/`, with four files:
`compose.yaml`, `Caddyfile`, `.env.example`, `README.md`.

### 4.1 Topology

```mermaid
flowchart LR
    client[MCP client / REST consumer] -->|HTTPS 443| caddy[caddy]
    caddy -->|/mcp*| serve[serve - MCP streamable-HTTP :8001]
    caddy -->|/api/* path-stripped| http[http - FastAPI REST :8001]
    serve -->|read-only| corpus[(corpus volume /data/legal-texts)]
    http -->|read-only| corpus
```

### 4.2 Services (`compose.yaml`)

| Service | Profile(s) | Command | Internal port | Role |
|---|---|---|---|---|
| `serve` | `mcp` | `serve` | `:8001` | MCP streamable-HTTP |
| `http`  | `rest` | `http` | `:8001` | FastAPI REST |
| `caddy` | `mcp`, `rest` | — | — | Reverse proxy, TLS; host `80`/`443` (+`443/udp`) |

- Both app services bind `:8001` by default — `serve` via `settings.port`,
  `http` via the Part A fix — so the production compose needs no `PORT`
  override.
- Only `caddy` publishes host ports. The app services are reachable only on
  the internal `edge` network; the proxy is the single public ingress.
- All services use `restart: unless-stopped`.
- `serve` / `http` inherit the Dockerfile `HEALTHCHECK` (probes
  `:8001/health`, answered by both surfaces after the Part A `/health` fix).
- `caddy` uses long-form `depends_on` with `condition: service_healthy` and
  `required: false` on both app services, so it waits for whichever surfaces
  the active profile started (Docker Compose v2.20+).
- The corpus is bind-mounted read-only into both app services.

### 4.3 Profiles

`COMPOSE_PROFILES` is set in `.env` (default `mcp`). `caddy` belongs to both
profiles, so it starts whenever any app profile is active.

- `docker compose up` (default `.env`) → `serve` + `caddy`.
- `COMPOSE_PROFILES=mcp,rest` → both surfaces + `caddy`.

MCP is the default because it is the primary product surface.

### 4.4 Caddy routing

Single domain, path-based:

- `/mcp*` → `serve:8001`
- `/api/*` → path-stripped → `http:8001` (the FastAPI app serves `/laws`,
  `/search`, … at the root)
- `/health` → `serve:8001`
- TLS via Let's Encrypt using `{$DOMAIN}` / `{$ACME_EMAIL}`.
- Defence-in-depth security headers (HSTS, `X-Content-Type-Options`, CSP).
- `request_body { max_size 1MB }` as the proxy-layer body cap — covers both
  surfaces; the app-layer `MAX_REQUEST_BODY_BYTES` cap is FastAPI-only.

The README documents a subdomain split (`mcp.` / `api.`) as an alternative.

### 4.5 Corpus

Production mounts an operator-prepared corpus read-only at `/data/legal-texts`
(the directory convention — the Dockerfile default and the most-documented
path). `STRICT_DATASET=true` and `STRICT_STARTUP=true` make startup fail fast
on a missing or broken corpus. Auto-download is disabled for reproducibility.

> The repository also uses an archive convention (`/data/corpus/latest.tar.zst`,
> in `deployment/Dockerfile.hosted`). This spec standardises the reference
> example on the directory convention; the wider inconsistency is left as-is.

### 4.6 `.env.example`

All operator-tunable values in one place:

| Variable | Example | Purpose |
|---|---|---|
| `DOMAIN` | `legal.example.org` | Domain Caddy serves + ACME |
| `ACME_EMAIL` | `admin@example.org` | Let's Encrypt account |
| `COMPOSE_PROFILES` | `mcp` | Which surfaces run (`mcp`, `rest`, or `mcp,rest`) |
| `IMAGE` | `ghcr.io/klein-business/legal-text-mcp-de:2.1.3@sha256:…` | Digest-pinned image (v2.1.3, as in the HTTP example) |
| `CORPUS_HOST_PATH` | `/srv/legal-corpus` | Host path of the prepared corpus |
| `MAX_REQUEST_BODY_BYTES` | `1048576` | App-layer body cap (bytes) |

## 5. Tests & docs

### 5.1 Tests

- **Unit tests** (Part A) — see §3.4. Run by the existing `ci.yml` `test` job.
- **Compose smoke** — extends `scripts/verify_uv_runtime_docker.py`, which is
  already run by the `e2e.yml` job `uv-runtime-and-docker`. No new workflow or
  job. The new step:
  - validates both Compose files with `docker compose config` (the production
    file resolved against `.env.example`);
  - builds the image from the repository `Dockerfile`;
  - boots the production stack's app services with
    `docker compose up -d --wait serve http` against the bundled fixture
    corpus (`tests/fixtures/normalized`), overriding `IMAGE` and
    `CORPUS_HOST_PATH` via the environment. `--wait` blocks until both
    services report `healthy`, which exercises both the Part A port fix and
    the `/health` route.
- Caddy is not booted in CI (a real domain would trigger a failing Let's
  Encrypt challenge). MCP-protocol depth (`initialize` / `tools/list`) is
  already covered by the existing `verify_docker_runtime()` in the same
  script; the Compose smoke verifies the Compose wiring, not the protocol.

### 5.2 Docs

- New `examples/docker-compose/production/README.md`: start / verify / stop,
  profile switching, corpus preparation, a `tls internal` note for local
  testing of the full Caddy stack, and the subdomain alternative.
- `docs/operations/production-deployment.md`: the two inline Compose snippets
  (the Caddy option's `docker-compose.yml` and `Caddyfile`) are replaced by a
  pointer to `examples/docker-compose/production/`. The conceptual content
  (TLS rationale, body-size cap, rate-limiting note, health checks, the
  Kubernetes probe snippet) and the nginx option stay as prose.
- A cross-link is added from `examples/docker-compose/http/README.md` to the
  new production example.
- Changelog: the fixes ship as `fix(cli):` / `fix(server):` Conventional
  Commits. The project uses `release-please`
  (`.github/workflows/release-please.yml`), which generates `CHANGELOG.md`
  from commit messages — no manual changelog edit.

## 6. Out of scope

- `deployment/` directory (§1.4): Caddyfile/`deploy.sh` mismatch, stale
  `Dockerfile.hosted` base-image pin.
- nginx as a committed artifact.
- Rate-limiting middleware, Kubernetes/Helm.

## 7. Open points / risks

- **`http` default port change** (§3.2) — confirmed acceptable during
  brainstorming; no existing test depends on the `8080` default.
- **Caddy in CI** — excluded from the smoke job; the full TLS stack is verified
  manually or via the `tls internal` local path documented in the README.
- **Corpus convention split** — the directory-vs-archive inconsistency (§4.5)
  is left in place; only the new reference example is standardised.
