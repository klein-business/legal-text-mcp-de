# Typed Python client example

The HTTP API ships an OpenAPI 3.1 spec at `/openapi.json` and a
Swagger UI at `/docs`. For Python consumers, the simplest path is
`httpx` + the published pydantic response models from
`legal_text_mcp_de.http_models` — they are part of the public API.

## Setup

Start the server (fixture corpus, default port `8001`):

```bash
DATASET_PATH=tests/fixtures/normalized \
STRICT_STARTUP=true \
uv run uvicorn legal_text_mcp_de.http_api:app --host 127.0.0.1 --port 8001
```

Install the client deps (in another shell):

```bash
pip install legal-text-mcp-de httpx
```

## Minimal example

```python
import httpx

from legal_text_mcp_de.http_models import (
    LawListResponse,
    LawDetailResponse,
    SearchResponse,
)


BASE = "http://127.0.0.1:8001"


def list_laws(client: httpx.Client, query: str | None = None) -> LawListResponse:
    params = {"query": query} if query else None
    response = client.get(f"{BASE}/laws", params=params)
    response.raise_for_status()
    return LawListResponse.model_validate(response.json())


def get_law(client: httpx.Client, code: str) -> LawDetailResponse:
    response = client.get(f"{BASE}/laws/{code}")
    response.raise_for_status()
    return LawDetailResponse.model_validate(response.json())


def search(client: httpx.Client, query: str, codes: list[str] | None = None) -> SearchResponse:
    params: dict[str, str | list[str]] = {"query": query}
    if codes:
        params["codes"] = codes
    response = client.get(f"{BASE}/search", params=params)
    response.raise_for_status()
    return SearchResponse.model_validate(response.json())


def main() -> None:
    with httpx.Client(timeout=10.0) as client:
        # 1. Discover laws containing "DSGVO"
        laws = list_laws(client, query="DSGVO")
        print(f"Found {len(laws.laws)} matching law(s)")
        for law in laws.laws:
            print(f"  {law.canonical_id} — {law.display_name}")

        # 2. Pull a specific law's full structure
        bgb = get_law(client, "BGB")
        print(f"\nBGB has {bgb.law.norm_count} norms")

        # 3. Full-text search restricted to a single code
        hits = search(client, query="Werbung", codes=["UWG"])
        print(f"\nSearch returned {len(hits.results)} hit(s):")
        for hit in hits.results[:3]:
            print(f"  {hit.canonical_id}")


if __name__ == "__main__":
    main()
```

## Error handling

The API uses structured error bodies under `error.code` /
`error.message` / `error.details`. Map them with
`legal_text_mcp_de.http_models.ErrorResponse`:

```python
from legal_text_mcp_de.http_models import ErrorResponse


try:
    law = get_law(client, "DOES_NOT_EXIST")
except httpx.HTTPStatusError as exc:
    if exc.response.status_code in {404, 409, 413, 422, 503}:
        err = ErrorResponse.model_validate(exc.response.json())
        print(f"API error [{err.error.code}]: {err.error.message}")
    else:
        raise
```

Status-code reference is in the [HTTP API overview](index.md).

## Async variant

If you are integrating with an async app (FastAPI, Starlette, anyio):

```python
import asyncio
import httpx

from legal_text_mcp_de.http_models import LawListResponse


async def list_laws_async(query: str | None = None) -> LawListResponse:
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8001", timeout=10.0) as client:
        response = await client.get("/laws", params={"query": query} if query else None)
        response.raise_for_status()
        return LawListResponse.model_validate(response.json())


asyncio.run(list_laws_async("DSGVO"))
```

## Related

- [HTTP API overview](index.md) — endpoint reference + env vars
- [OpenAPI reference](openapi.md) — full schema
- [MCP tools reference](../tools/list_laws.md) — equivalent MCP calls
