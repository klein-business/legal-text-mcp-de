#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "tests" / "fixtures" / "normalized"
IMAGE_TAG = "legal-text-mcp-de:uv-migration"
EXPECTED_TOOLS = {
    "get_corpus_coverage",
    "list_laws",
    "get_law",
    "get_norm",
    "resolve_citation",
    "search_laws",
    "get_source_metadata",
    "get_source_limitations",
    "get_related_norms",
    "research_topic",
}


def print_step(message: str) -> None:
    print(f"==> {message}", flush=True)


def run_checked(args: list[str], *, env: dict[str, str] | None = None) -> None:
    print_step("Running: " + " ".join(args))
    subprocess.run(args, cwd=ROOT, env=env, check=True)


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def env_for_server(port: int | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "DATASET_PATH": str(DATASET),
            "STRICT_STARTUP": "true",
        }
    )
    if port is not None:
        env.update(
            {
                "HOST": "127.0.0.1",
                "PORT": str(port),
            }
        )
    return env


def start_process(args: list[str], *, env: dict[str, str]) -> subprocess.Popen[str]:
    print_step("Starting: " + " ".join(args))
    return subprocess.Popen(
        args,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def collect_process_output(process: subprocess.Popen[str]) -> str:
    if process.poll() is None:
        process.terminate()
        try:
            return process.communicate(timeout=5)[0]
        except subprocess.TimeoutExpired:
            process.kill()
            return process.communicate(timeout=5)[0]
    return process.communicate(timeout=5)[0]


def wait_for_port(port: int, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                return
        except Exception as exc:  # noqa: BLE001 - surfaced on timeout.
            last_error = exc
        time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for 127.0.0.1:{port}: {last_error}")


def get_json(url: str, *, timeout: float = 5.0) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            status = response.status
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read().decode("utf-8")
    if status != 200:
        raise AssertionError(f"{url} returned {status}: {body}")
    return json.loads(body)  # type: ignore[no-any-return]


def wait_for_ready(url: str, timeout: float = 20.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return get_json(url, timeout=1.0)
        except Exception as exc:  # noqa: BLE001 - surfaced on timeout.
            last_error = exc
        time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def import_external_mcp_client() -> tuple[Any, Any]:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    return ClientSession, streamablehttp_client


async def mcp_initialize_list_tools(port: int) -> None:
    ClientSession, streamablehttp_client = import_external_mcp_client()
    async with streamablehttp_client(f"http://127.0.0.1:{port}/mcp") as (read, write, _get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            if names != EXPECTED_TOOLS:
                raise AssertionError(f"Unexpected tools: {sorted(names)}")


def wait_for_mcp_initialize_list_tools(port: int, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: BaseException | None = None
    while time.monotonic() < deadline:
        try:
            asyncio.run(mcp_initialize_list_tools(port))
            return
        except BaseException as exc:  # noqa: BLE001 - surfaced on timeout.
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for MCP initialize/list-tools: {last_error!r}")


def assert_contains(path: Path, expected: str) -> None:
    text = path.read_text(encoding="utf-8")
    if expected not in text:
        raise AssertionError(f"{path} does not contain expected text: {expected}")


def verify_static_files() -> None:
    dockerfile = ROOT / "Dockerfile"
    helper = ROOT / "prepare_data" / "prepare_gesetze_im_internet.sh"
    helper_text = helper.read_text(encoding="utf-8")

    print_step("Checking Dockerfile uv runtime contract")
    assert_contains(dockerfile, "COPY --from=ghcr.io/astral-sh/uv:")
    assert_contains(dockerfile, "uv sync --frozen --no-dev")
    assert_contains(dockerfile, 'CMD ["uv", "run", "--frozen", "--no-sync", "legal-text-mcp-de", "serve"]')

    print_step("Checking data-prep uv contract")
    assert_contains(
        helper, 'uv run --project "$ROOT_DIR" --frozen --group prepare-data --no-dev python lawde.py loadall'
    )
    assert_contains(
        helper,
        'uv run --project "$ROOT_DIR" --frozen --group prepare-data --no-dev python lawdown.py convert laws laws_md',
    )
    for retired in [
        "python3 -m venv",
        "source venv/bin/activate",
        "pip install -r",
        "requirements.txt",
    ]:
        if retired in helper_text:
            raise AssertionError(f"{helper} still contains retired workflow text: {retired}")


def verify_prepare_data_script() -> None:
    run_checked(["bash", "-n", "prepare_data/prepare_gesetze_im_internet.sh"])
    run_checked(["bash", "prepare_data/prepare_gesetze_im_internet.sh", "--dry-run"])
    run_checked(["bash", "prepare_data/prepare_gesetze_im_internet.sh", "--no-network"])


def verify_release_and_e2e() -> None:
    env = os.environ.copy()
    run_checked(["uv", "run", "--group", "dev", "python", "scripts/verify_release.py"], env=env)
    run_checked(["uv", "run", "--group", "dev", "python", "scripts/verify_e2e.py"], env=env)


def verify_direct_mcp_startup() -> None:
    port = free_port()
    process = start_process(
        ["uv", "run", "legal-text-mcp-de", "serve"],
        env=env_for_server(port),
    )
    try:
        wait_for_port(port)
        wait_for_mcp_initialize_list_tools(port)
    except Exception:
        output = collect_process_output(process)
        if output:
            print(output, file=sys.stderr)
        raise
    finally:
        if process.poll() is None:
            collect_process_output(process)


def verify_direct_http_startup() -> None:
    port = free_port()
    process = start_process(
        ["uv", "run", "uvicorn", "legal_text_mcp_de.http_api:app", "--host", "127.0.0.1", "--port", str(port)],
        env=env_for_server(),
    )
    try:
        ready = wait_for_ready(f"http://127.0.0.1:{port}/ready")
        if ready.get("stage") != "serving_dataset":
            raise AssertionError(f"Unexpected readiness payload: {ready}")
    except Exception:
        output = collect_process_output(process)
        if output:
            print(output, file=sys.stderr)
        raise
    finally:
        if process.poll() is None:
            collect_process_output(process)


def docker_rm(name: str) -> None:
    subprocess.run(
        ["docker", "rm", "-f", name],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def verify_docker_runtime() -> None:
    container_name = f"legal-text-mcp-de-uv-{os.getpid()}"
    host_port = free_port()
    docker_rm(container_name)
    try:
        run_checked(["docker", "build", "-t", IMAGE_TAG, "."])
        run_checked(
            [
                "docker",
                "run",
                "-d",
                "--name",
                container_name,
                "-p",
                f"{host_port}:8001",
                "-v",
                f"{DATASET}:/data/legal-texts:ro",
                IMAGE_TAG,
            ]
        )
        wait_for_port(host_port, timeout=30.0)
        wait_for_mcp_initialize_list_tools(host_port, timeout=30.0)
    except Exception:
        logs = subprocess.run(
            ["docker", "logs", container_name],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        ).stdout
        if logs:
            print(logs, file=sys.stderr)
        raise
    finally:
        docker_rm(container_name)


def verify_compose_config() -> None:
    """Validate both committed Docker Compose files parse and interpolate."""
    print_step("Validating Docker Compose files")
    run_checked(
        [
            "docker",
            "compose",
            "-f",
            "examples/docker-compose/http/compose.yml",
            "config",
            "--quiet",
        ]
    )
    run_checked(
        [
            "docker",
            "compose",
            "-f",
            "examples/docker-compose/production/compose.yaml",
            "--env-file",
            "examples/docker-compose/production/.env.example",
            "--profile",
            "mcp",
            "--profile",
            "rest",
            "config",
            "--quiet",
        ]
    )


def verify_compose_smoke() -> None:
    """Boot the production Compose app services against the fixture corpus.

    Caddy is skipped (it would attempt a real ACME challenge). `--wait`
    blocks until both app services report `healthy`, which exercises the
    `_run_http` port fix and the MCP `/health` route end-to-end.
    """
    compose_project = f"legal-text-mcp-de-smoke-{os.getpid()}"
    compose_args = ["docker", "compose", "-p", compose_project, "-f", "examples/docker-compose/production/compose.yaml"]
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
        cwd=ROOT,
        env=env,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
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
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        ).stdout
        if logs:
            print(logs, file=sys.stderr)
        raise
    finally:
        subprocess.run(
            [*compose_args, "down", "-v"],
            cwd=ROOT,
            env=env,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


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


if __name__ == "__main__":
    raise SystemExit(main())
