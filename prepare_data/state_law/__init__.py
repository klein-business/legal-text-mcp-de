# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""State-law scrapers (per-Bundesland implementations of StateLawSource)."""

from prepare_data.state_law.base import (
    NormalizedLaw,
    NormalizedNorm,
    StateLawRaw,
    StateLawSource,
    StateLawSummary,
)
from prepare_data.state_law.bayern import BayernStateLaw
from prepare_data.state_law.bw import BWStateLaw
from prepare_data.state_law.he import HEStateLaw
from prepare_data.state_law.nds import NDSStateLaw
from prepare_data.state_law.nrw import NRWStateLaw

__all__ = [
    "BWStateLaw",
    "BayernStateLaw",
    "HEStateLaw",
    "NDSStateLaw",
    "NRWStateLaw",
    "NormalizedLaw",
    "NormalizedNorm",
    "StateLawRaw",
    "StateLawSource",
    "StateLawSummary",
]
