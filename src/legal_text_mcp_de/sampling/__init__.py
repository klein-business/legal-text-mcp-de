# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Sampling helpers for Tier-4 MCP smart tools."""

from legal_text_mcp_de.sampling.client import safe_sample
from legal_text_mcp_de.sampling.errors import (
    SamplingError,
    SamplingNotSupported,
    SamplingRefused,
    SamplingTimeout,
    SchemaValidationError,
)
from legal_text_mcp_de.sampling.schemas import (
    RankingEntry,
    RankingResult,
    SampleResult,
)
from legal_text_mcp_de.sampling.testing import MockSamplingClient

__all__ = [
    "MockSamplingClient",
    "RankingEntry",
    "RankingResult",
    "SampleResult",
    "SamplingError",
    "SamplingNotSupported",
    "SamplingRefused",
    "SamplingTimeout",
    "SchemaValidationError",
    "safe_sample",
]
