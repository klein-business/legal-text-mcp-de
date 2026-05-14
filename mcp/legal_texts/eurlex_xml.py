from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .gii_xml import _subdivisions


def parse_dsgvo_xml(xml_path: Path, law: dict[str, Any], source: dict[str, Any]) -> list[dict[str, Any]]:
    data = xml_path.read_text(encoding="utf-8", errors="replace")
    if "<LG.DOC>DE</LG.DOC>" not in data or "<ACT" not in data:
        raise ValueError("DSGVO source must be German article-bearing DOC_2 XML")
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
    return norms


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


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
