# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Pydantic models for the research_topic Smart Tool."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RankedNorm(BaseModel):
    """One ranked norm returned by the LLM-ranking step."""

    canonical_id: str
    title: str
    relevance_score: float = Field(ge=0, le=10)


class ResearchReport(BaseModel):
    """Structured output of research_topic."""

    model_config = ConfigDict(extra="forbid")

    topic: str
    top_norms: list[RankedNorm] = Field(default_factory=list)
    related_norms: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    synthesis: str | None = None
    candidates_examined: int = 0
    sampling_calls: int = 0
    provenance: list[dict[str, Any]] = Field(default_factory=list)
    status: Literal["ok", "no_matches", "degraded_no_sampling", "error"] = "ok"
    degraded_mode: str | None = None
    note: str | None = None
