# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class HealthResponse(BaseModel):
    status: str


class ErrorBody(FlexibleModel):
    code: str
    message: str
    details: dict[str, Any]
    suggestions: list[Any] | None = None
    source: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class ReadinessResponse(FlexibleModel):
    stage: str
    state: str
    details: dict[str, Any]


class LawListResponse(FlexibleModel):
    laws: list[dict[str, Any]]
    count: int
    query: str | None = None


class LawDetailResponse(FlexibleModel):
    law: dict[str, Any]
    norms: list[dict[str, Any]]


class CitationResponse(FlexibleModel):
    law: dict[str, Any]
    norm: dict[str, Any]
    citation: dict[str, Any]
    source: dict[str, Any]
    selection: dict[str, Any] | None = None


class SearchResponse(FlexibleModel):
    query: str
    codes: list[str] | None = None
    results: list[dict[str, Any]]
    count: int


class SourceMetadataResponse(FlexibleModel):
    sources: list[dict[str, Any]]
    count: int


class CorpusCoverageResponse(FlexibleModel):
    generated_package_present: bool
    package: dict[str, Any]
    manifest: dict[str, Any]
    counts: dict[str, int]
    source_families: list[str]
    terminal_states: dict[str, int]
    state_law_coverage: dict[str, Any]


class SourceLimitationsResponse(FlexibleModel):
    source_limitations: list[dict[str, Any]]
    count: int
    filters: dict[str, Any]


class RelationshipsResponse(FlexibleModel):
    norm: dict[str, Any]
    relationships: list[dict[str, Any]]
    count: int
