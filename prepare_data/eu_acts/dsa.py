# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Digital Services Act (CELEX 32022R2065) loader."""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass, field
from typing import Callable

from prepare_data.eu_acts._normalize import adapt_eu_act, parse_cellar_xml
from prepare_data.eu_acts.cellar_client import CellarClient
from prepare_data.state_law.base import NormalizedLaw


CELEX = "32022R2065"
DISPLAY_CODE = "DSA"
DISPLAY_NAME = "Verordnung (EU) 2022/2065 (Digital Services Act)"


def _default_http_get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310
        return bytes(resp.read())


def _default_resolve(celex: str, lang: str) -> str:
    return CellarClient().resolve_xml_url(celex=celex, lang=lang)


@dataclass
class DSAAct:
    """Digital Services Act (CELEX 32022R2065) loader.

    Parameters
    ----------
    lang:
        ISO 639-1 language code for the requested XML version. Defaults to
        ``"DE"`` (German).
    resolve_xml_url:
        ``(celex, lang) -> url`` callable. Tests inject a fake; production
        uses :class:`~prepare_data.eu_acts.cellar_client.CellarClient`.
    http_get:
        ``(url) -> bytes`` callable. Tests inject a fake; production uses
        ``urllib.request.urlopen``.
    """

    lang: str = "DE"
    resolve_xml_url: Callable[[str, str], str] = field(default=_default_resolve)
    http_get: Callable[[str], bytes] = field(default=_default_http_get)

    def fetch_and_normalise(self) -> NormalizedLaw:
        """Resolve, fetch, parse, and return the DSA as a NormalizedLaw."""
        url = self.resolve_xml_url(CELEX, self.lang)
        body = self.http_get(url)
        parsed_norms = parse_cellar_xml(body)
        return adapt_eu_act(
            canonical_id=f"eu/{CELEX.lower()}",
            display_code=DISPLAY_CODE,
            display_name=DISPLAY_NAME,
            source_url=url,
            parsed_norms=parsed_norms,
        )
