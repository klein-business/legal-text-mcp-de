# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .gii_xml import _subdivisions


def parse_dsgvo_xml(xml_path: Path, law: dict[str, Any], source: dict[str, Any]) -> list[dict[str, Any]]:
    return parse_eurlex_act_xml(xml_path, law, source, error_label="DSGVO source")


def parse_eurlex_act_xml(
    xml_path: Path,
    law: dict[str, Any],
    source: dict[str, Any],
    *,
    error_label: str = "EUR-Lex source",
) -> list[dict[str, Any]]:
    data = xml_path.read_text(encoding="utf-8", errors="replace")
    if "<LG.DOC>DE</LG.DOC>" not in data or "<ACT" not in data:
        raise ValueError(f"{error_label} must be German article-bearing DOC_2 XML")
    root = ET.fromstring(data)
    norms = []
    for article in root.iter():
        if _local(article.tag) != "ARTICLE":
            continue
        value = _article_value(article)
        if not value:
            continue
        text = " ".join(" ".join(article.itertext()).split())
        title = _article_title(article)
        norm_id = f"art:{value}"
        norms.append(
            {
                "canonical_id": f"{law['canonical_id']}/{norm_id}",
                "law_id": law["canonical_id"],
                "norm_id": norm_id,
                "unit": "art",
                "value": value,
                "title": title,
                "text": text,
                "status": "active",
                "url": f"{source['source_url']}#art_{value}",
                "source": source,
                "subdivisions": _subdivisions(text),
            }
        )
    for recital in root.iter():
        if not _is_recital_element(recital):
            continue
        value = _recital_value(recital)
        if not value:
            continue
        text = " ".join(" ".join(recital.itertext()).split())
        title = f"Erwaegungsgrund {value}"
        norm_id = f"recital:{value}"
        norms.append(
            {
                "canonical_id": f"{law['canonical_id']}/{norm_id}",
                "law_id": law["canonical_id"],
                "norm_id": norm_id,
                "unit": "recital",
                "value": value,
                "title": title,
                "text": text,
                "status": "active",
                "url": f"{source['source_url']}#rct_{value}",
                "source": source,
                "subdivisions": [],
            }
        )
    return norms


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _is_recital_element(element: ET.Element) -> bool:
    return _local(element.tag) in {"CONSID", "RECITAL"}


def _article_value(article: ET.Element) -> str | None:
    identifier = article.attrib.get("IDENTIFIER")
    if identifier and identifier.isdigit():
        return str(int(identifier))
    text = " ".join(article.itertext())
    match = re.search(r"Artikel\s+([0-9]+[a-z]?)", text, re.IGNORECASE)
    return match.group(1).lower() if match else None


def _article_title(article: ET.Element) -> str | None:
    for element in article.iter():
        if _local(element.tag) in {"TI.ART", "STI.ART", "TITLE"}:
            text = " ".join(" ".join(element.itertext()).split())
            if text:
                return text
    return None


def _recital_value(recital: ET.Element) -> str | None:
    identifier = recital.attrib.get("IDENTIFIER")
    if identifier and identifier.isdigit():
        return str(int(identifier))
    for element in recital.iter():
        if _local(element.tag) in {"NO.P", "NO", "NUM"}:
            text = " ".join(" ".join(element.itertext()).split())
            match = re.search(r"([0-9]+)", text)
            if match:
                return str(int(match.group(1)))
    text = " ".join(recital.itertext())
    match = re.search(r"\(?([0-9]+)\)?", text)
    return str(int(match.group(1))) if match else None
