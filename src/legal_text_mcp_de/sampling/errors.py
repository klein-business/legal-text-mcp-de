# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Sampling helper error hierarchy."""


class SamplingError(RuntimeError):
    """Base for all sampling errors."""


class SamplingNotSupported(SamplingError):
    """Client does not implement the sampling capability."""


class SamplingTimeout(SamplingError):
    """Sampling call did not complete within the timeout."""


class SamplingRefused(SamplingError):
    """User refused sampling in the client."""


class SchemaValidationError(SamplingError):
    """LLM output did not match the requested schema."""
