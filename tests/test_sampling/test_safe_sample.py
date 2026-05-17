# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from legal_text_mcp_de.sampling.client import safe_sample
from legal_text_mcp_de.sampling.errors import (
    SamplingNotSupported,
    SamplingTimeout,
    SchemaValidationError,
)
from legal_text_mcp_de.sampling.schemas import RankingResult


@pytest.mark.asyncio
async def test_safe_sample_returns_validated_payload():
    ctx = MagicMock()
    ctx.client_supports_sampling = MagicMock(return_value=True)
    ranking_json = json.dumps({"ranking": [{"norm_id": "x", "score": 9.0, "reason": "y"}]})
    ctx.sample = AsyncMock(return_value=MagicMock(content=ranking_json, model="haiku", usage=None))

    result = await safe_sample(
        ctx,
        system="x",
        user_message="y",
        schema=RankingResult,
        max_tokens=500,
    )
    assert isinstance(result.content, RankingResult)
    assert result.content.ranking[0].norm_id == "x"


@pytest.mark.asyncio
async def test_safe_sample_returns_raw_text_without_schema():
    ctx = MagicMock()
    ctx.client_supports_sampling = MagicMock(return_value=True)
    ctx.sample = AsyncMock(return_value=MagicMock(content="hello world", model="haiku", usage=None))

    result = await safe_sample(ctx, system="s", user_message="u")
    assert result.content == "hello world"
    assert result.raw == "hello world"


@pytest.mark.asyncio
async def test_safe_sample_raises_when_client_does_not_support():
    ctx = MagicMock()
    ctx.client_supports_sampling = MagicMock(return_value=False)
    with pytest.raises(SamplingNotSupported):
        await safe_sample(ctx, system="s", user_message="u")


@pytest.mark.asyncio
async def test_safe_sample_raises_timeout_after_retries():
    ctx = MagicMock()
    ctx.client_supports_sampling = MagicMock(return_value=True)

    async def hang(*a, **kw):
        import asyncio as _asyncio

        await _asyncio.sleep(10)

    ctx.sample = AsyncMock(side_effect=hang)
    with pytest.raises(SamplingTimeout):
        await safe_sample(
            ctx,
            system="s",
            user_message="u",
            timeout_s=0.05,
            retries=1,
        )


@pytest.mark.asyncio
async def test_safe_sample_schema_validation_failure():
    ctx = MagicMock()
    ctx.client_supports_sampling = MagicMock(return_value=True)
    ctx.sample = AsyncMock(return_value=MagicMock(content="not json", model="haiku", usage=None))

    with pytest.raises(SchemaValidationError):
        await safe_sample(
            ctx,
            system="s",
            user_message="u",
            schema=RankingResult,
            retries=0,
        )


@pytest.mark.asyncio
async def test_safe_sample_succeeds_after_transient_failure():
    ctx = MagicMock()
    ctx.client_supports_sampling = MagicMock(return_value=True)
    good = json.dumps({"ranking": [{"norm_id": "ok", "score": 5.0, "reason": "r"}]})
    ctx.sample = AsyncMock(
        side_effect=[
            MagicMock(content="not json", model="haiku", usage=None),
            MagicMock(content=good, model="haiku", usage=None),
        ]
    )
    result = await safe_sample(
        ctx,
        system="s",
        user_message="u",
        schema=RankingResult,
        retries=1,
    )
    assert result.content.ranking[0].norm_id == "ok"
