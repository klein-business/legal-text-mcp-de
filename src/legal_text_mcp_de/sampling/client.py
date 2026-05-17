# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""safe_sample: typed, retried, schema-validated MCP Sampling helper."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from pydantic import BaseModel, ValidationError

from legal_text_mcp_de.sampling.errors import (
    SamplingError,
    SamplingNotSupported,
    SamplingRefused,
    SamplingTimeout,
    SchemaValidationError,
)
from legal_text_mcp_de.sampling.schemas import SampleResult


async def safe_sample(
    ctx: Any,
    *,
    system: str,
    user_message: str,
    schema: type[BaseModel] | None = None,
    max_tokens: int = 2000,
    temperature: float = 0.3,
    timeout_s: float = 30.0,
    retries: int = 2,
) -> SampleResult:
    """Run a sampling call with retry, timeout, optional schema validation.

    Returns a SampleResult; raises a SamplingError subclass on failure.
    """
    supports = getattr(ctx, "client_supports_sampling", lambda: True)
    if not supports():
        raise SamplingNotSupported("Client does not support MCP Sampling")

    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            raw_result = await asyncio.wait_for(
                ctx.sample(
                    messages=[{"role": "user", "content": user_message}],
                    system=system,
                    max_tokens=max_tokens,
                    temperature=temperature,
                ),
                timeout=timeout_s,
            )
        except asyncio.TimeoutError:
            last_exc = SamplingTimeout(f"timeout after {timeout_s}s on attempt {attempt + 1}")
            continue
        except SamplingRefused:
            raise
        except Exception as exc:  # noqa: BLE001
            last_exc = SamplingError(f"sampling call failed on attempt {attempt + 1}: {exc}")
            continue

        raw_text = getattr(raw_result, "content", "") or ""
        tokens = getattr(getattr(raw_result, "usage", None), "total_tokens", None)
        model = getattr(raw_result, "model", None)

        if schema is None:
            return SampleResult(content=raw_text, raw=raw_text, tokens_used=tokens, model_used=model)
        try:
            parsed = schema.model_validate_json(raw_text)
            return SampleResult(content=parsed, raw=raw_text, tokens_used=tokens, model_used=model)
        except (ValidationError, json.JSONDecodeError) as exc:
            last_exc = SchemaValidationError(f"schema validation failed on attempt {attempt + 1}: {exc}")
            continue

    raise last_exc or SamplingError("unknown sampling failure")
