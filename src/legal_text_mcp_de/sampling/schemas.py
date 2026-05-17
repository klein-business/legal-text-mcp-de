# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Pydantic schemas for sampling I/O."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SampleResult(BaseModel):
    """Outcome of a single sampling call."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    content: Any
    raw: str
    tokens_used: int | None = None
    model_used: str | None = None


class RankingEntry(BaseModel):
    norm_id: str
    score: float = Field(ge=0, le=10)
    reason: str


class RankingResult(BaseModel):
    ranking: list[RankingEntry]

    def top_n(self, n: int) -> list[RankingEntry]:
        return sorted(self.ranking, key=lambda r: -r.score)[:n]
