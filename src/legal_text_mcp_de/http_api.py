# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

from typing import Annotated, Any, Callable, TypeVar

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp

from legal_text_mcp_de.config import settings
from legal_text_mcp_de.http_models import (
    CitationResponse,
    CorpusCoverageResponse,
    ErrorResponse,
    HealthResponse,
    LawDetailResponse,
    LawListResponse,
    ReadinessResponse,
    RelationshipsResponse,
    SearchResponse,
    SourceLimitationsResponse,
)
from legal_text_mcp_de.legal_texts.errors import LegalTextError
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime


# FastAPI accepts `dict[int | str, dict[str, Any]]` for the `responses` kwarg.
# Annotating loosely (Any) is the standard pattern because FastAPI's runtime
# accepts both `{"model": <pydantic_model>}` and arbitrary `dict[str, Any]`
# payloads in the same slot, and there is no narrower stable type for it.
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}


_T = TypeVar("_T")


class RequestBodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Defence-in-depth: reject requests whose body exceeds the limit.

    The operator's reverse proxy is expected to enforce its own
    request-size cap; this middleware closes the gap when the API is
    exposed directly (e.g. inside a container without a fronting proxy).

    The middleware short-circuits on a known ``Content-Length`` header
    that exceeds the limit. Requests without ``Content-Length`` (e.g.
    chunked transfers, GETs without a body) are not pre-rejected — the
    framework's own body-reading machinery applies for those, so a
    chunked POST that streams beyond the limit will be cut off by the
    transport layer, not by this middleware. That is by design: this
    cap is a last-line defence, not a substitute for proxy-level limits.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                size: int | None = int(content_length)
            except ValueError:
                size = None
            if size is not None and size > self.max_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": {
                            "code": "PAYLOAD_TOO_LARGE",
                            "message": (
                                f"Request body of {size} bytes exceeds the "
                                f"configured maximum of {self.max_bytes} bytes."
                            ),
                            "details": {
                                "max_request_body_bytes": self.max_bytes,
                                "received_bytes": size,
                            },
                        }
                    },
                )
        return await call_next(request)


def create_http_app(runtime: LegalTextRuntime | None = None) -> FastAPI:
    runtime = runtime or LegalTextRuntime.from_settings(settings, strict=False)
    app = FastAPI(title="legal-text-mcp-de", version="1.0.0")
    app.add_middleware(
        RequestBodySizeLimitMiddleware,
        max_bytes=settings.max_request_body_bytes,
    )

    def run(call: Callable[[], _T]) -> _T | JSONResponse:
        """Wrap a runtime call so LegalTextError is rendered as JSON.

        Returning ``_T | JSONResponse`` is acceptable here because FastAPI
        will pass through a ``JSONResponse`` unchanged and validate ``_T``
        against the route's ``response_model``.
        """
        try:
            return call()
        except LegalTextError as exc:
            return JSONResponse(status_code=exc.http_status, content=exc.to_dict())

    @app.get("/health", response_model=HealthResponse)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready", response_model=ReadinessResponse, responses=ERROR_RESPONSES)
    def ready() -> Any:
        return run(runtime.readiness)

    @app.get("/laws", response_model=LawListResponse, responses=ERROR_RESPONSES)
    def list_laws(query: str | None = None) -> Any:
        return run(lambda: runtime.list_laws(query))

    @app.get("/laws/{code}", response_model=LawDetailResponse, responses=ERROR_RESPONSES)
    def get_law(code: str) -> Any:
        return run(lambda: runtime.get_law(code))

    @app.get(
        "/laws/{code}/norms/{norm:path}/relationships", response_model=RelationshipsResponse, responses=ERROR_RESPONSES
    )
    def get_norm_relationships(code: str, norm: str) -> Any:
        return run(lambda: runtime.get_related_norms(code, norm))

    @app.get("/laws/{code}/norms/{norm:path}", response_model=CitationResponse, responses=ERROR_RESPONSES)
    def get_norm(code: str, norm: str) -> Any:
        return run(lambda: runtime.get_norm(code, norm))

    @app.get("/corpus/coverage", response_model=CorpusCoverageResponse, responses=ERROR_RESPONSES)
    def get_corpus_coverage() -> Any:
        return run(runtime.get_corpus_coverage)

    @app.get("/corpus/source-limitations", response_model=SourceLimitationsResponse, responses=ERROR_RESPONSES)
    def get_source_limitations(
        source_family: str | None = None,
        terminal_state: str | None = None,
        state_code: str | None = None,
        law_id: str | None = None,
    ) -> Any:
        return run(
            lambda: runtime.get_source_limitations(
                source_family=source_family,
                terminal_state=terminal_state,
                state_code=state_code,
                law_id=law_id,
            )
        )

    @app.get("/search", response_model=SearchResponse, responses=ERROR_RESPONSES)
    def search(
        query: str,
        codes: Annotated[list[str] | None, Query()] = None,
    ) -> Any:
        return run(lambda: runtime.search_laws(query, codes))

    return app


app = create_http_app()
