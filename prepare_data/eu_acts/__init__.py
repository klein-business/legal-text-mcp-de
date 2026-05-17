# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""EUR-Lex / Cellar adapters for EU acts."""

from prepare_data.eu_acts._normalize import adapt_eu_act
from prepare_data.eu_acts.cellar_client import CellarClient
from prepare_data.eu_acts.dma import DMAAct
from prepare_data.eu_acts.dsa import DSAAct
from prepare_data.eu_acts.eprivacy import EPrivacyAct

__all__ = ["CellarClient", "DMAAct", "DSAAct", "EPrivacyAct", "adapt_eu_act"]
