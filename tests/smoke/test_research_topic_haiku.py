# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Cost-capped smoke test against real Anthropic Haiku.

Skipped unless ANTHROPIC_API_KEY env var is set. Designed to run on PRs
that touch research_topic or sampling.
"""

import os

import pytest


pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)


@pytest.mark.asyncio
async def test_research_topic_against_haiku_returns_non_empty_synthesis():
    pytest.skip("real-Haiku smoke test will be enabled in Task F (public hosting setup)")
