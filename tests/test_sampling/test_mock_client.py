# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import pytest

from legal_text_mcp_de.sampling.client import safe_sample
from legal_text_mcp_de.sampling.errors import SamplingNotSupported
from legal_text_mcp_de.sampling.testing import MockSamplingClient


@pytest.mark.asyncio
async def test_mock_client_returns_queued_responses_in_order():
    ctx = MockSamplingClient(responses=["first", "second"])
    r1 = await safe_sample(ctx, system="s", user_message="u")
    r2 = await safe_sample(ctx, system="s", user_message="u")
    assert r1.content == "first"
    assert r2.content == "second"


@pytest.mark.asyncio
async def test_mock_client_can_disable_sampling():
    ctx = MockSamplingClient(responses=[], supports_sampling=False)
    with pytest.raises(SamplingNotSupported):
        await safe_sample(ctx, system="s", user_message="u")
