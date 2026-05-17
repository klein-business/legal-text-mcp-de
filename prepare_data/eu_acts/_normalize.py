# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Shared adapter: Cellar XML bytes -> NormalizedLaw.

The v1 eurlex_xml parser (src/legal_text_mcp_de/legal_texts/eurlex_xml.py)
operates on file paths and requires `law` / `source` dicts that are coupled
to the v1 runtime shape, so we cannot reuse it directly here. Instead this
module provides a self-contained XML parser using the same stdlib
xml.etree.ElementTree (no extra dependency) and the same element-tag logic
used by the v1 parser, then adapts the result to NormalizedLaw.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from prepare_data.state_law.base import NormalizedLaw, NormalizedNorm


# ---------------------------------------------------------------------------
# XML parsing helpers (mirrors the logic in eurlex_xml.py)
# ---------------------------------------------------------------------------


def _local(tag: str) -> str:
    """Strip namespace prefix from an ElementTree tag."""
    return tag.rsplit("}", 1)[-1]


def _article_value(article: ET.Element) -> str | None:
    identifier = article.attrib.get("IDENTIFIER")
    if identifier and identifier.isdigit():
        return str(int(identifier))
    text = " ".join(article.itertext())
    match = re.search(r"Artikel\s+([0-9]+[a-z]?)", text, re.IGNORECASE)
    return match.group(1).lower() if match else None


def _article_title(article: ET.Element) -> str:
    for element in article.iter():
        if _local(element.tag) in {"TI.ART", "STI.ART", "TITLE"}:
            text = " ".join(" ".join(element.itertext()).split())
            if text:
                return text
    return ""


def parse_cellar_xml(xml: bytes) -> list[dict[str, str]]:
    """Parse Cellar DOC_2 XML bytes and return a list of norm dicts.

    Each dict has: norm_id (str), title (str), text (str).

    Articles and recitals are extracted; the same approach as the v1 parser
    is used (iter over the whole tree, match on local tag names).
    """
    root = ET.fromstring(xml.decode("utf-8", errors="replace"))
    norms: list[dict[str, str]] = []

    for article in root.iter():
        if _local(article.tag) != "ARTICLE":
            continue
        value = _article_value(article)
        if not value:
            continue
        norms.append(
            {
                "norm_id": f"art:{value}",
                "title": _article_title(article),
                "text": " ".join(" ".join(article.itertext()).split()),
            }
        )

    return norms


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


def adapt_eu_act(
    *,
    canonical_id: str,
    display_code: str,
    display_name: str,
    source_url: str,
    parsed_norms: list[dict[str, str]],
) -> NormalizedLaw:
    """Turn per-article dicts from parse_cellar_xml into a NormalizedLaw.

    Parameters
    ----------
    canonical_id:
        e.g. ``"eu/32002l0058"``
    display_code:
        Short label, e.g. ``"ePrivacy"``
    display_name:
        Human-readable full name of the act.
    source_url:
        The Cellar XML URL the bytes were fetched from.
    parsed_norms:
        Output of :func:`parse_cellar_xml`.
    """
    norms = tuple(
        NormalizedNorm(
            norm_id=p["norm_id"],
            title=p["title"],
            text=p["text"],
        )
        for p in parsed_norms
    )
    return NormalizedLaw(
        canonical_id=canonical_id,
        display_code=display_code,
        display_name=display_name,
        state_code="eu",
        source_url=source_url,
        norms=norms,
    )
