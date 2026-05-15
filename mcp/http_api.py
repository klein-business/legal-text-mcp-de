from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from config import settings
from http_models import (
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
from legal_texts.errors import LegalTextError
from legal_texts.runtime import LegalTextRuntime


ERROR_RESPONSES = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}


def create_http_app(runtime: LegalTextRuntime | None = None) -> FastAPI:
    runtime = runtime or LegalTextRuntime.from_settings(settings, strict=False)
    app = FastAPI(title="legal-text-mcp-de", version="1.0.0")

    def run(call):
        try:
            return call()
        except LegalTextError as exc:
            return JSONResponse(status_code=exc.http_status, content=exc.to_dict())

    @app.get("/health", response_model=HealthResponse)
    def health():
        return {"status": "ok"}

    @app.get("/ready", response_model=ReadinessResponse, responses=ERROR_RESPONSES)
    def ready():
        return run(runtime.readiness)

    @app.get("/laws", response_model=LawListResponse, responses=ERROR_RESPONSES)
    def list_laws(query: str | None = None):
        return run(lambda: runtime.list_laws(query))

    @app.get("/laws/{code}", response_model=LawDetailResponse, responses=ERROR_RESPONSES)
    def get_law(code: str):
        return run(lambda: runtime.get_law(code))

    @app.get("/laws/{code}/norms/{norm:path}/relationships", response_model=RelationshipsResponse, responses=ERROR_RESPONSES)
    def get_norm_relationships(code: str, norm: str):
        return run(lambda: runtime.get_related_norms(code, norm))

    @app.get("/laws/{code}/norms/{norm:path}", response_model=CitationResponse, responses=ERROR_RESPONSES)
    def get_norm(code: str, norm: str):
        return run(lambda: runtime.get_norm(code, norm))

    @app.get("/corpus/coverage", response_model=CorpusCoverageResponse, responses=ERROR_RESPONSES)
    def get_corpus_coverage():
        return run(runtime.get_corpus_coverage)

    @app.get("/corpus/source-limitations", response_model=SourceLimitationsResponse, responses=ERROR_RESPONSES)
    def get_source_limitations(
        source_family: str | None = None,
        terminal_state: str | None = None,
        state_code: str | None = None,
        law_id: str | None = None,
    ):
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
    ):
        return run(lambda: runtime.search_laws(query, codes))

    return app


app = create_http_app()
