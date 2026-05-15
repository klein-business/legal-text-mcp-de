#!/usr/bin/env python3
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
from collections.abc import Callable
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEGACY_DATASET = ROOT / "mcp" / "tests" / "fixtures" / "normalized"
GENERATED_PACKAGE = ROOT / "mcp" / "tests" / "fixtures" / "generated_package"
EXPECTED_TOOLS = {
    "list_laws",
    "get_law",
    "get_norm",
    "resolve_citation",
    "search_laws",
    "get_source_metadata",
    "get_corpus_coverage",
    "get_source_limitations",
    "get_related_norms",
}
EXPECTED_HTTP_PATHS = {
    "/health",
    "/ready",
    "/laws",
    "/laws/{code}",
    "/laws/{code}/norms/{norm}",
    "/laws/{code}/norms/{norm}/relationships",
    "/corpus/coverage",
    "/corpus/source-limitations",
    "/search",
}


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def env_for_server(dataset_path: Path, port: int | None = None) -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = str(ROOT / "mcp")
    if env.get("PYTHONPATH"):
        pythonpath = pythonpath + os.pathsep + env["PYTHONPATH"]
    env.update(
        {
            "PYTHONPATH": pythonpath,
            "DATASET_PATH": str(dataset_path),
            "STRICT_STARTUP": "true",
        }
    )
    if port is not None:
        env.update({"HOST": "127.0.0.1", "PORT": str(port)})
    return env


def start_process(args: list[str], env: dict[str, str]) -> subprocess.Popen[str]:
    return subprocess.Popen(
        args,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def wait_for_url(url: str, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if 200 <= response.status < 500:
                    return
        except Exception as exc:  # noqa: BLE001 - surfaced on timeout.
            last_error = exc
        time.sleep(0.1)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def wait_for_port(port: int, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                return
        except Exception as exc:  # noqa: BLE001 - surfaced on timeout.
            last_error = exc
        time.sleep(0.1)
    raise RuntimeError(f"Timed out waiting for 127.0.0.1:{port}: {last_error}")


def get_json(url: str, *, expected_status: int = 200) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=5.0) as response:
            status = response.status
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read().decode("utf-8")
    if status != expected_status:
        raise AssertionError(f"{url} returned {status}, expected {expected_status}: {body}")
    return json.loads(body)  # type: ignore[no-any-return]


def assert_openapi_paths(base: str) -> None:
    schema = get_json(f"{base}/openapi.json")
    missing = EXPECTED_HTTP_PATHS - set(schema["paths"])
    if missing:
        raise AssertionError(f"OpenAPI schema missing paths: {sorted(missing)}")


def run_http_legacy_e2e(port: int) -> None:
    base = f"http://127.0.0.1:{port}"
    health = get_json(f"{base}/health")
    ready = get_json(f"{base}/ready")
    laws = get_json(f"{base}/laws?query=DSGVO")
    law = get_json(f"{base}/laws/BGB")
    container = get_json(f"{base}/laws/egbgb/norms/art%3A246a")
    child = get_json(f"{base}/laws/egbgb/norms/art%3A246a%2Fpar%3A1")
    coverage = get_json(f"{base}/corpus/coverage")
    limitations = get_json(f"{base}/corpus/source-limitations")
    relationships = get_json(f"{base}/laws/BGB/norms/par%3A355/relationships")
    search = get_json(f"{base}/search?query=Werbung&codes=UWG")
    missing_law = get_json(f"{base}/laws/NOPE", expected_status=404)
    invalid = get_json(f"{base}/search?query=!!!", expected_status=422)
    assert_openapi_paths(base)

    assert health == {"status": "ok"}
    assert ready["stage"] == "serving_dataset"
    assert ready["state"] == "ready"
    assert laws["count"] == 1
    assert laws["laws"][0]["canonical_id"] == "dsgvo_eu_2016_679"
    assert law["law"]["canonical_id"] == "bgb"
    assert law["norms"]
    assert container["norm"]["status"] == "container"
    assert child["norm"]["canonical_id"] == "egbgb/art:246a/par:1"
    assert coverage["generated_package_present"] is False
    assert limitations["count"] == 0
    assert relationships["count"] == 0
    assert search["codes"] == ["uwg_2004"]
    assert search["results"]
    assert missing_law["error"]["code"] == "LAW_NOT_FOUND"
    assert invalid["error"]["code"] == "INVALID_QUERY"


def run_http_generated_package_e2e(port: int) -> None:
    base = f"http://127.0.0.1:{port}"
    health = get_json(f"{base}/health")
    ready = get_json(f"{base}/ready")
    laws = get_json(f"{base}/laws?query=DSGVO")
    law = get_json(f"{base}/laws/DSGVO")
    norm = get_json(f"{base}/laws/DSGVO/norms/art%3A5")
    recital = get_json(f"{base}/laws/DSGVO/norms/recital%3A1")
    coverage = get_json(f"{base}/corpus/coverage")
    limitations = get_json(f"{base}/corpus/source-limitations?source_family=state-law")
    relationships = get_json(f"{base}/laws/DSGVO/norms/art%3A5/relationships")
    search = get_json(f"{base}/search?query=Personenbezogene")
    assert_openapi_paths(base)

    assert health == {"status": "ok"}
    assert ready["stage"] == "serving_dataset"
    assert ready["state"] == "ready"
    assert laws["count"] == 1
    assert law["law"]["canonical_id"] == "dsgvo_eu_2016_679"
    assert norm["norm"]["canonical_id"] == "dsgvo_eu_2016_679/art:5"
    assert recital["norm"]["canonical_id"] == "dsgvo_eu_2016_679/recital:1"
    assert coverage["generated_package_present"] is True
    assert coverage["counts"]["source_limitations"] == 1
    assert limitations["count"] == 1
    assert relationships["count"] == 1
    assert relationships["relationships"][0]["relationship_id"] == "rel-dsgvo-art5-limitation"
    assert search["query"] == "personenbezogene"
    assert search["count"] == 1
    assert search["results"][0]["canonical_id"] == "dsgvo_eu_2016_679/art:5"


def import_external_mcp_client() -> tuple[Any, Any]:
    original_path = list(sys.path)
    blocked = {ROOT.resolve(), (ROOT / "mcp").resolve()}
    sys.modules.pop("mcp", None)
    sys.modules.pop("mcp.client", None)
    sys.path = [path for path in sys.path if path and Path(path).resolve() not in blocked]
    try:
        from mcp import ClientSession  # type: ignore[attr-defined]
        from mcp.client.streamable_http import streamablehttp_client
    finally:
        sys.path = original_path
    return ClientSession, streamablehttp_client


async def run_mcp_legacy_e2e(port: int) -> None:
    ClientSession, streamablehttp_client = import_external_mcp_client()
    async with streamablehttp_client(f"http://127.0.0.1:{port}/mcp") as (read, write, _get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            assert names == EXPECTED_TOOLS

            laws = await session.call_tool("list_laws", {"query": "DSGVO"})
            law = await session.call_tool("get_law", {"code": "BGB"})
            norm = await session.call_tool("get_norm", {"code": "BGB", "norm": "§ 355"})
            citation = await session.call_tool(
                "resolve_citation",
                {
                    "code": "EGBGB",
                    "unit": "art",
                    "paragraph_or_article": "246a",
                    "child_unit": "par",
                    "child_value": "1",
                },
            )
            search = await session.call_tool("search_laws", {"query": "Werbung", "codes": ["UWG"]})
            coverage = await session.call_tool("get_corpus_coverage", {})
            limitations = await session.call_tool("get_source_limitations", {})
            relationships = await session.call_tool("get_related_norms", {"code": "BGB", "norm": "§ 355"})
            source_metadata = await session.call_tool("get_source_metadata", {"code": "DSGVO"})
            missing = await session.call_tool("get_norm", {"code": "BGB", "norm": "§ 999"})

            assert structured_content(laws)["laws"][0]["canonical_id"] == "dsgvo_eu_2016_679"
            assert structured_content(law)["law"]["canonical_id"] == "bgb"
            assert structured_content(norm)["norm"]["canonical_id"] == "bgb/par:355"
            assert structured_content(citation)["norm"]["canonical_id"] == "egbgb/art:246a/par:1"
            search_data = structured_content(search)
            assert search_data["codes"] == ["uwg_2004"]
            assert search_data["results"]
            assert structured_content(coverage)["generated_package_present"] is False
            assert structured_content(limitations)["count"] == 0
            assert structured_content(relationships)["count"] == 0
            assert structured_content(source_metadata)["sources"][0]["source"]["source_kind"] == "eur-lex-cellar"
            assert structured_content(missing)["error"]["code"] == "NORM_NOT_FOUND"


async def run_mcp_generated_package_e2e(port: int) -> None:
    ClientSession, streamablehttp_client = import_external_mcp_client()
    async with streamablehttp_client(f"http://127.0.0.1:{port}/mcp") as (read, write, _get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert {tool.name for tool in tools.tools} == EXPECTED_TOOLS

            laws = await session.call_tool("list_laws", {})
            law = await session.call_tool("get_law", {"code": "DSGVO"})
            norm = await session.call_tool("get_norm", {"code": "DSGVO", "norm": "art:5"})
            recital = await session.call_tool("get_norm", {"code": "DSGVO", "norm": "recital:1"})
            search = await session.call_tool("search_laws", {"query": "Personenbezogene"})
            source_metadata = await session.call_tool("get_source_metadata", {"code": "DSGVO"})
            coverage = await session.call_tool("get_corpus_coverage", {})
            limitations = await session.call_tool("get_source_limitations", {"source_family": "state-law"})
            relationships = await session.call_tool("get_related_norms", {"code": "DSGVO", "norm": "art:5"})

            assert structured_content(laws)["count"] == 1
            assert structured_content(law)["law"]["canonical_id"] == "dsgvo_eu_2016_679"
            assert structured_content(norm)["norm"]["canonical_id"] == "dsgvo_eu_2016_679/art:5"
            assert structured_content(recital)["norm"]["canonical_id"] == "dsgvo_eu_2016_679/recital:1"
            generated_search = structured_content(search)
            assert generated_search["query"] == "personenbezogene"
            assert generated_search["count"] == 1
            assert generated_search["results"][0]["canonical_id"] == "dsgvo_eu_2016_679/art:5"
            assert structured_content(source_metadata)["sources"][0]["source"]["source_kind"] == "eur-lex-cellar"
            assert structured_content(coverage)["generated_package_present"] is True
            assert structured_content(coverage)["counts"]["relationships"] == 1
            assert structured_content(limitations)["count"] == 1
            relationship_data = structured_content(relationships)
            assert relationship_data["count"] == 1
            assert relationship_data["relationships"][0]["relationship_id"] == "rel-dsgvo-art5-limitation"


def structured_content(result: Any) -> dict[str, Any]:
    payload = getattr(result, "structuredContent", None)
    if payload is None:
        payload = getattr(result, "structured_content", None)
    if payload is None:
        raise AssertionError(f"MCP result has no structured content: {result!r}")
    return payload  # type: ignore[no-any-return]


def terminate(process: subprocess.Popen[str]) -> str:
    if process.poll() is None:
        process.terminate()
        try:
            return process.communicate(timeout=5)[0]
        except subprocess.TimeoutExpired:
            process.kill()
            return process.communicate(timeout=5)[0]
    return process.communicate(timeout=5)[0]


def run_case(
    label: str,
    dataset_path: Path,
    http_check: Callable[[int], None],
    mcp_check: Callable[[int], Any],
) -> None:
    http_port = free_port()
    mcp_port = free_port()
    http_process = start_process(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "http_api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(http_port),
        ],
        env_for_server(dataset_path),
    )
    mcp_process = start_process(
        [sys.executable, "mcp/server.py"],
        env_for_server(dataset_path, mcp_port),
    )
    outputs: list[tuple[str, str]] = []
    try:
        wait_for_url(f"http://127.0.0.1:{http_port}/health")
        wait_for_port(mcp_port)
        http_check(http_port)
        asyncio.run(mcp_check(mcp_port))
        print(f"{label} HTTP CLI E2E OK")
        print(f"{label} MCP streamable HTTP E2E OK")
    finally:
        outputs.append(("HTTP", terminate(http_process)))
        outputs.append(("MCP", terminate(mcp_process)))
        if any(process.returncode not in {0, -15, None} for process in [http_process, mcp_process]):
            for name, output in outputs:
                print(f"\n--- {label} {name} server output ---\n{output}", file=sys.stderr)


def main() -> int:
    try:
        run_case("legacy", LEGACY_DATASET, run_http_legacy_e2e, run_mcp_legacy_e2e)
        run_case("generated-package", GENERATED_PACKAGE, run_http_generated_package_e2e, run_mcp_generated_package_e2e)
        return 0
    except Exception as exc:
        print(f"E2E FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
