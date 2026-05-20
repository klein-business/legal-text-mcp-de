# Docker Compose Production Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the broken HTTP Compose example and the MCP-mode health check, then add a committed, CI-tested production Docker Compose reference.

**Architecture:** Two small server-side fixes — `_run_http` honours the `PORT` env var, and the FastMCP app gains a `/health` route — then a new `examples/docker-compose/production/` directory wiring both transport surfaces (`serve`, `http`) behind a Caddy reverse proxy via Compose profiles. The stack is verified by extending the existing `scripts/verify_uv_runtime_docker.py` e2e check (already run by `e2e.yml`).

**Tech Stack:** Python 3.12, Typer CLI, FastMCP (mcp 1.27.1), FastAPI/uvicorn, Docker Compose v2.20+, Caddy 2, pytest, uv.

**Spec:** `docs/superpowers/specs/2026-05-20-docker-compose-production-design.md`

---

## File Structure

**Modified:**
- `src/legal_text_mcp_de/cli/_server.py` — `_run_http` port fallback + `--port` help text.
- `src/legal_text_mcp_de/server.py` — `/health` custom route on the FastMCP app.
- `scripts/verify_uv_runtime_docker.py` — Compose config validation + smoke check.
- `tests/test_cli/test_server.py` — two regression tests for `_run_http`.
- `docs/operations/production-deployment.md` — replace inline Caddy snippets with a pointer.
- `examples/docker-compose/http/README.md` — cross-link to the production example.
- `examples/docker-compose/http/compose.yml` — correct the misleading corpus comment.

**Created:**
- `tests/test_server.py` — test for the MCP `/health` route.
- `examples/docker-compose/production/compose.yaml` — the production stack.
- `examples/docker-compose/production/Caddyfile` — reverse proxy config.
- `examples/docker-compose/production/.env.example` — operator-tunable values.
- `examples/docker-compose/production/README.md` — usage guide.

Tasks are ordered by dependency: Task 4 (smoke) needs Tasks 1–3 in place.

---

### Task 1: Fix `_run_http` to honour the `PORT` env var

**Files:**
- Modify: `src/legal_text_mcp_de/cli/_server.py`
- Test: `tests/test_cli/test_server.py`

`_run_http` hard-codes the bind port to `8080` and ignores `PORT`, contradicting its own docstring and breaking the `examples/docker-compose/http/` example. The fix mirrors `_run_mcp`: fall back to `settings.port` (which reads `PORT`, default `8001`).

- [ ] **Step 1: Write the regression tests**

In `tests/test_cli/test_server.py`, change the module docstring on line 3 from:

```python
"""Tests for cli/_server.py — flag parsing only, mcp.run() is mocked."""
```

to:

```python
"""Tests for cli/_server.py — flag parsing and port resolution; run is mocked."""
```

Then append these two functions to the end of the file:

```python


def test_http_uses_settings_port_when_no_flag(monkeypatch):
    """Regression: `http` must honour settings.port (PORT env), not hard-code 8080."""
    from legal_text_mcp_de.cli._server import _run_http
    from legal_text_mcp_de.config import settings

    captured = {}

    def fake_uvicorn_run(app_path, *, host, port, log_level):
        captured["port"] = port

    monkeypatch.setattr("uvicorn.run", fake_uvicorn_run)
    monkeypatch.setattr(settings, "port", 12345)

    _run_http(host=None, port=None, dataset=None)

    assert captured["port"] == 12345


def test_http_explicit_port_overrides_settings(monkeypatch):
    """An explicit --port still wins over settings.port."""
    from legal_text_mcp_de.cli._server import _run_http
    from legal_text_mcp_de.config import settings

    captured = {}

    def fake_uvicorn_run(app_path, *, host, port, log_level):
        captured["port"] = port

    monkeypatch.setattr("uvicorn.run", fake_uvicorn_run)
    monkeypatch.setattr(settings, "port", 12345)

    _run_http(host=None, port=9999, dataset=None)

    assert captured["port"] == 9999
```

- [ ] **Step 2: Run the tests to verify the first one fails**

Run: `uv run --group dev pytest tests/test_cli/test_server.py -v`
Expected: `test_http_uses_settings_port_when_no_flag` **FAILS** with `assert 8080 == 12345` (the current code hard-codes `8080`). `test_http_explicit_port_overrides_settings` and `test_serve_runs_mcp_app` PASS.

- [ ] **Step 3: Apply the fix**

In `src/legal_text_mcp_de/cli/_server.py`, change line 51 from:

```python
    effective_port = port if port is not None else 8080
```

to:

```python
    effective_port = port if port is not None else settings.port
```

In the same file, change the `http` command's `--port` option (line 74) from:

```python
    port: Annotated[int | None, typer.Option("--port", help="Bind port (default 8080).")] = None,
```

to:

```python
    port: Annotated[int | None, typer.Option("--port", help="Bind port (default from PORT env or 8001).")] = None,
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --group dev pytest tests/test_cli/test_server.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Verify lint and types**

Run: `uv run ruff check src/legal_text_mcp_de/cli/_server.py tests/test_cli/test_server.py`
Expected: no findings.

Run: `uv run --group dev mypy --strict src/legal_text_mcp_de/cli/`
Expected: no errors (`_server.py` is strict-ratcheted).

- [ ] **Step 6: Commit**

```bash
git add src/legal_text_mcp_de/cli/_server.py tests/test_cli/test_server.py
git commit -m "fix(cli): http command honours PORT env instead of hard-coded 8080"
```

---

### Task 2: Add a `/health` route to the MCP `serve` transport

**Files:**
- Modify: `src/legal_text_mcp_de/server.py`
- Test: `tests/test_server.py` (create)

The MCP `serve` transport (FastMCP) exposes no `/health`, so the Dockerfile `HEALTHCHECK` fails for the default `CMD ["… "serve"]`. Register `/health` via the SDK's `custom_route` decorator (the documented mechanism for public health endpoints, mcp 1.27.1).

- [ ] **Step 1: Write the failing test**

Create `tests/test_server.py`:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for server.py — the FastMCP app factory."""

from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from legal_text_mcp_de.legal_texts.dataset import NormalizedDataset
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime
from legal_text_mcp_de.server import create_mcp_app


FIXTURE_DATASET = Path(__file__).parent / "fixtures" / "normalized"


def test_mcp_app_serves_health():
    """The MCP streamable-HTTP transport must answer GET /health.

    The Dockerfile HEALTHCHECK probes :8001/health and the default CMD is
    `serve`; without this route every serve-mode container is unhealthy.
    """
    dataset = NormalizedDataset.load(FIXTURE_DATASET, require_search_index=True)
    runtime = LegalTextRuntime.from_dataset(dataset)
    client = TestClient(create_mcp_app(runtime).streamable_http_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

This mirrors the runtime-construction pattern in `tests/test_http_api.py` (load `NormalizedDataset`, build `LegalTextRuntime.from_dataset`), so the test needs no network and no env setup.

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run --group dev pytest tests/test_server.py -v`
Expected: **FAIL** — `GET /health` returns `404`, so `assert response.status_code == 200` fails.

- [ ] **Step 3: Implement the `/health` route**

In `src/legal_text_mcp_de/server.py`, change the import block. The current third-party import (line 13) is:

```python
from mcp.server.fastmcp import FastMCP
```

Replace that single line with:

```python
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
```

Then, in `create_mcp_app`, register the route after the `register_prompts(app)` call and before `return app`. The current end of the function is:

```python
    register_v1_tools(app, runtime)
    register_research_topic(app, runtime)
    register_resources(app, runtime)
    register_prompts(app)
    return app
```

Replace it with:

```python
    register_v1_tools(app, runtime)
    register_research_topic(app, runtime)
    register_resources(app, runtime)
    register_prompts(app)

    @app.custom_route("/health", methods=["GET"])
    async def _health(_request: Request) -> Response:
        """Liveness probe for the Dockerfile HEALTHCHECK and load balancers."""
        return JSONResponse({"status": "ok"})

    return app
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run --group dev pytest tests/test_server.py -v`
Expected: PASS.

- [ ] **Step 5: Verify lint and the wider test suite**

Run: `uv run ruff check src/legal_text_mcp_de/server.py tests/test_server.py`
Expected: no findings.

Run: `uv run --group dev pytest tests/test_server.py tests/test_http_api.py tests/test_cli -v`
Expected: all PASS (confirms the import change did not break the MCP/HTTP app construction).

- [ ] **Step 6: Commit**

```bash
git add src/legal_text_mcp_de/server.py tests/test_server.py
git commit -m "fix(server): expose /health on the MCP serve transport"
```

---

### Task 3: Create the production Docker Compose example

**Files:**
- Create: `examples/docker-compose/production/compose.yaml`
- Create: `examples/docker-compose/production/Caddyfile`
- Create: `examples/docker-compose/production/.env.example`
- Create: `examples/docker-compose/production/README.md`

- [ ] **Step 1: Create `examples/docker-compose/production/compose.yaml`**

```yaml
# Production Docker Compose reference for legal-text-mcp-de.
#
# Copy .env.example to .env and edit it before `docker compose up -d`.
# COMPOSE_PROFILES (set in .env) selects which transport surface runs:
#   mcp       -> MCP streamable-HTTP (serve)  + caddy
#   rest      -> FastAPI REST API   (http)    + caddy
#   mcp,rest  -> both surfaces                + caddy
#
# Only caddy publishes host ports; the app services are reachable only on
# the internal network. See README.md and
# docs/operations/production-deployment.md.

services:
  serve:
    image: ${IMAGE}
    profiles: ["mcp"]
    command: ["uv", "run", "--frozen", "--no-sync", "legal-text-mcp-de", "serve"]
    restart: unless-stopped
    environment:
      DATASET_PATH: /data/legal-texts
      STRICT_STARTUP: "true"
      STRICT_DATASET: "true"
      MAX_REQUEST_BODY_BYTES: ${MAX_REQUEST_BODY_BYTES:-1048576}
    volumes:
      - ${CORPUS_HOST_PATH}:/data/legal-texts:ro
    networks: [edge]

  http:
    image: ${IMAGE}
    profiles: ["rest"]
    command: ["uv", "run", "--frozen", "--no-sync", "legal-text-mcp-de", "http"]
    restart: unless-stopped
    environment:
      DATASET_PATH: /data/legal-texts
      STRICT_STARTUP: "true"
      STRICT_DATASET: "true"
      MAX_REQUEST_BODY_BYTES: ${MAX_REQUEST_BODY_BYTES:-1048576}
    volumes:
      - ${CORPUS_HOST_PATH}:/data/legal-texts:ro
    networks: [edge]

  caddy:
    image: caddy:2-alpine
    profiles: ["mcp", "rest"]
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    environment:
      DOMAIN: ${DOMAIN}
      ACME_EMAIL: ${ACME_EMAIL}
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    networks: [edge]
    depends_on:
      serve:
        condition: service_healthy
        required: false
      http:
        condition: service_healthy
        required: false

volumes:
  caddy_data:
  caddy_config:

networks:
  edge:
```

- [ ] **Step 2: Create `examples/docker-compose/production/Caddyfile`**

```caddyfile
# Caddy reverse proxy for the legal-text-mcp-de production stack.
# DOMAIN and ACME_EMAIL are read from the container environment
# (set in compose.yaml from .env). Indentation is not significant to Caddy.

{$DOMAIN} {
    tls {$ACME_EMAIL}

    encode zstd gzip

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        Content-Security-Policy "default-src 'none'; frame-ancestors 'none'"
        Referrer-Policy "no-referrer"
        -Server
    }

    # Proxy-level request body cap. The FastAPI app enforces its own
    # MAX_REQUEST_BODY_BYTES on top; the MCP transport relies on this.
    request_body {
        max_size 1MB
    }

    # MCP streamable-HTTP transport (profile: mcp).
    handle /mcp* {
        reverse_proxy serve:8001
    }

    # FastAPI REST API (profile: rest). /api is stripped before proxying,
    # so /api/laws reaches the upstream as /laws.
    handle_path /api/* {
        reverse_proxy http:8001
    }

    # Liveness endpoint — answered by the MCP transport.
    handle /health {
        reverse_proxy serve:8001
    }

    handle {
        respond "Not Found" 404
    }
}
```

- [ ] **Step 3: Create `examples/docker-compose/production/.env.example`**

```bash
# Copy this file to .env and edit the values before `docker compose up -d`.

# Domain Caddy serves; also the subject of the Let's Encrypt certificate.
DOMAIN=legal.example.org

# Email for the Let's Encrypt account (expiry notices).
ACME_EMAIL=admin@example.org

# Which transport surface(s) to run: mcp, rest, or mcp,rest.
COMPOSE_PROFILES=mcp

# Digest-pinned server image. Bump alongside releases.
IMAGE=ghcr.io/klein-business/legal-text-mcp-de:2.1.3@sha256:d53b9538a7c6c8f04d826f28f7e6b2215ce2e557c01c1de2b854edec44e4b98e

# Absolute host path to a prepared corpus directory, bind-mounted read-only
# at /data/legal-texts. See README.md for how to produce one.
CORPUS_HOST_PATH=/srv/legal-corpus

# App-layer request body cap in bytes (Caddy enforces its own limit on top).
MAX_REQUEST_BODY_BYTES=1048576
```

- [ ] **Step 4: Create `examples/docker-compose/production/README.md`**

```markdown
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
```

- [ ] **Step 5: Validate the Compose file**

Run:

```bash
docker compose \
  -f examples/docker-compose/production/compose.yaml \
  --env-file examples/docker-compose/production/.env.example \
  --profile mcp --profile rest config --quiet
```

Expected: exit code `0`, no output (the file parses and all variables interpolate).

- [ ] **Step 6: Commit**

```bash
git add examples/docker-compose/production/
git commit -m "docs(examples): add production Docker Compose reference stack"
```

---

### Task 4: Smoke-test the production stack in `verify_uv_runtime_docker.py`

**Files:**
- Modify: `scripts/verify_uv_runtime_docker.py`

`scripts/verify_uv_runtime_docker.py` is already run by the `e2e.yml` job `uv-runtime-and-docker`. Extend it with a Compose config check and a Compose smoke. `scripts/` is mypy-`--strict`; the new code matches the existing typed style. Requires a running Docker daemon.

- [ ] **Step 1: Add the two verification functions**

In `scripts/verify_uv_runtime_docker.py`, insert the following two functions immediately before the existing `def main() -> int:` line:

```python
def verify_compose_config() -> None:
    """Validate both committed Docker Compose files parse and interpolate."""
    print_step("Validating Docker Compose files")
    run_checked(
        [
            "docker", "compose",
            "-f", "examples/docker-compose/http/compose.yml",
            "config", "--quiet",
        ]
    )
    run_checked(
        [
            "docker", "compose",
            "-f", "examples/docker-compose/production/compose.yaml",
            "--env-file", "examples/docker-compose/production/.env.example",
            "--profile", "mcp", "--profile", "rest",
            "config", "--quiet",
        ]
    )


def verify_compose_smoke() -> None:
    """Boot the production Compose app services against the fixture corpus.

    Caddy is skipped (it would attempt a real ACME challenge). `--wait`
    blocks until both app services report `healthy`, which exercises the
    `_run_http` port fix and the MCP `/health` route end-to-end.
    """
    compose_args = ["docker", "compose", "-f", "examples/docker-compose/production/compose.yaml"]
    env = os.environ.copy()
    env.update(
        {
            "IMAGE": IMAGE_TAG,
            "CORPUS_HOST_PATH": str(DATASET),
            "DOMAIN": "smoke.invalid",
            "ACME_EMAIL": "smoke@smoke.invalid",
        }
    )
    print_step("Compose smoke: building image")
    run_checked(["docker", "build", "-t", IMAGE_TAG, "."])
    subprocess.run(
        [*compose_args, "down", "-v"],
        cwd=ROOT, env=env, check=False,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        print_step("Compose smoke: docker compose up --wait serve http")
        run_checked(
            [*compose_args, "up", "-d", "--wait", "--wait-timeout", "120", "serve", "http"],
            env=env,
        )
    except Exception:
        logs = subprocess.run(
            [*compose_args, "logs"],
            cwd=ROOT, env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
        ).stdout
        if logs:
            print(logs, file=sys.stderr)
        raise
    finally:
        subprocess.run(
            [*compose_args, "down", "-v"],
            cwd=ROOT, env=env, check=False,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
```

- [ ] **Step 2: Wire the functions into `main`**

The current `main` is:

```python
def main() -> int:
    verify_static_files()
    verify_prepare_data_script()
    verify_release_and_e2e()
    verify_direct_mcp_startup()
    verify_direct_http_startup()
    verify_docker_runtime()
    print("uv runtime and Docker verification OK")
    return 0
```

Replace it with:

```python
def main() -> int:
    verify_static_files()
    verify_prepare_data_script()
    verify_release_and_e2e()
    verify_direct_mcp_startup()
    verify_direct_http_startup()
    verify_docker_runtime()
    verify_compose_config()
    verify_compose_smoke()
    print("uv runtime and Docker verification OK")
    return 0
```

- [ ] **Step 3: Verify types**

Run: `uv run --group dev mypy --strict scripts/verify_uv_runtime_docker.py`
Expected: no errors.

- [ ] **Step 4: Run the new checks (Docker daemon required)**

Run:

```bash
uv run --group dev python -c "from scripts.verify_uv_runtime_docker import verify_compose_config, verify_compose_smoke; verify_compose_config(); verify_compose_smoke()"
```

Expected: prints the `==> Validating …` / `==> Compose smoke: …` steps and exits `0`. `docker compose up --wait` returns only once `serve` and `http` are both `healthy` — proving the Task 1 port fix (the `http` service binds `:8001`) and the Task 2 `/health` route (the `serve` healthcheck passes). On failure the container logs are printed to stderr.

- [ ] **Step 5: Commit**

```bash
git add scripts/verify_uv_runtime_docker.py
git commit -m "test(e2e): smoke-test the production Docker Compose stack"
```

---

### Task 5: Update deployment docs and cross-links

**Files:**
- Modify: `docs/operations/production-deployment.md`
- Modify: `examples/docker-compose/http/README.md`
- Modify: `examples/docker-compose/http/compose.yml`

- [ ] **Step 1: Point `production-deployment.md` at the committed stack**

In `docs/operations/production-deployment.md`, replace the entire `## Option 1 — Caddy` section — everything from the heading line `## Option 1 — Caddy (TLS-by-default, recommended)` through the closing ```` ``` ```` of its `Bring up` code block (the block ending with the line `curl -fsSL https://legal.example.org/health    # -> {"status":"ok"}`) — with:

````markdown
## Option 1 — Caddy (TLS-by-default, recommended)

A committed, CI-tested reference stack lives at
[`examples/docker-compose/production/`](https://github.com/klein-business/legal-text-mcp-de/tree/main/examples/docker-compose/production).
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
[example README](https://github.com/klein-business/legal-text-mcp-de/tree/main/examples/docker-compose/production)
for profile switching, corpus preparation, and local testing with
`tls internal`.
````

Leave the `## Option 2 — nginx`, `## Health checking`, `## Logging + observability`, and `## Related` sections unchanged.

- [ ] **Step 2: Cross-link from the HTTP example README**

In `examples/docker-compose/http/README.md`, replace the existing production blockquote:

```markdown
> **For production deployments** pin to a different image digest,
> set `STRICT_DATASET=true`, and bind-mount a real corpus archive at
> `/data/corpus/latest.tar.zst`. See
> [`docs/operations/production-deployment.md`](../../../docs/operations/production-deployment.md).
```

with:

```markdown
> **For a production stack** — both transport surfaces behind Caddy with
> TLS, Compose profiles, and a corpus mount — see the committed
> [`../production/`](../production/) example. Background and the nginx
> alternative are in
> [`docs/operations/production-deployment.md`](../../../docs/operations/production-deployment.md).
```

- [ ] **Step 3: Correct the misleading corpus comment in the HTTP example**

The HTTP example claims it uses a "bundled fixture corpus shipped inside the image", but the image ships only reference metadata, not a queryable corpus. In `examples/docker-compose/http/compose.yml`, replace this header-comment fragment (lines 3–7):

```yaml
# This example boots the FastAPI HTTP transport against the bundled
# fixture corpus shipped inside the image. For a real production
# deployment, pin to a different image digest, set STRICT_DATASET=true,
# and bind-mount a corpus archive at /data/corpus/latest.tar.zst. See
# docs/operations/production-deployment.md.
```

with:

```yaml
# This example boots the FastAPI HTTP transport with no corpus mounted:
# the server starts and answers /health, but law and search endpoints
# stay empty until a corpus is bind-mounted. For a corpus-backed
# production stack see examples/docker-compose/production/ and
# docs/operations/production-deployment.md.
```

Then replace the `environment:` comment (lines 25–27):

```yaml
      # Use the bundled fixture corpus shipped inside the image. For
      # production, set STRICT_DATASET=true and bind-mount a corpus
      # archive (see docs/operations/production-deployment.md).
```

with:

```yaml
      # No corpus is mounted here; /health works regardless. For a
      # corpus-backed deployment, bind-mount one and set
      # STRICT_DATASET=true — see examples/docker-compose/production/.
```

- [ ] **Step 4: Verify the Markdown links resolve**

Run:

```bash
test -f examples/docker-compose/production/README.md \
  && test -f docs/features/data-preparation.md \
  && test -f docs/operations/production-deployment.md \
  && echo "links OK"
```

Expected: prints `links OK` (the relative link targets used in the new/edited docs exist).

- [ ] **Step 5: Commit**

```bash
git add docs/operations/production-deployment.md examples/docker-compose/http/README.md examples/docker-compose/http/compose.yml
git commit -m "docs: point production-deployment at the committed Compose stack"
```

---

## Final verification

After all five tasks, run the full check suite:

- [ ] `uv run ruff check .` — no findings.
- [ ] `uv run --group dev mypy --strict src/legal_text_mcp_de/cli/ scripts/verify_uv_runtime_docker.py` — no errors.
- [ ] `uv run --group dev pytest tests` — all tests pass, coverage gate (`fail_under = 86`) holds.
- [ ] `uv run --group dev python scripts/verify_uv_runtime_docker.py` — ends with `uv runtime and Docker verification OK` (Docker daemon required; this runs the full e2e check including the new Compose smoke).

## Notes

- **Changelog:** none of these tasks edit `CHANGELOG.md`. The project uses
  `release-please`, which generates the changelog from the `fix(cli):`,
  `fix(server):`, `docs(examples):`, `test(e2e):`, and `docs:` commit
  messages above. No manual changelog edit.
- **Out of scope** (per the spec): the `deployment/` directory, an nginx
  committed artifact, rate-limiting middleware, Kubernetes/Helm.
