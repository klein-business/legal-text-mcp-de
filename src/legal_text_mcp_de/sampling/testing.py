# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Mock client for testing tools that depend on Sampling.

Use with Phase E `research_topic` tests and any other smart-tool tests.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _MockResult:
    content: str
    model: str = "mock-haiku"
    usage: None = None  # mimic shape without exposing token-count


@dataclass
class MockSamplingClient:
    """Drop-in ctx for `safe_sample` and smart tools.

    Parameters
    ----------
    responses
        Ordered list of content strings to return from successive `sample()` calls.
    supports_sampling
        Return value of `client_supports_sampling()`. Default True.
    """

    responses: list[str]
    supports_sampling: bool = True
    _queue: deque[str] = field(default_factory=deque, init=False)

    def __post_init__(self) -> None:
        self._queue = deque(self.responses)

    def client_supports_sampling(self) -> bool:
        return self.supports_sampling

    async def sample(self, *args: Any, **kwargs: Any) -> _MockResult:
        if not self._queue:
            raise RuntimeError("MockSamplingClient: no more queued responses")
        return _MockResult(content=self._queue.popleft())

    async def report_progress(self, *args: Any, **kwargs: Any) -> None:
        return None

    async def log(self, *args: Any, **kwargs: Any) -> None:
        return None
