from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any


PAR_RE = re.compile(r"§\s*([0-9]+[a-z]?)", re.IGNORECASE)
ART_RE = re.compile(r"Art\.?\s*([0-9]+[a-z]?)", re.IGNORECASE)
ABS_RE = re.compile(r"\((\d+)\)\s*")


def parse_gii_zip(zip_path: Path, law: dict[str, Any], source: dict[str, Any]) -> list[dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as archive:
        xml_names = [name for name in archive.namelist() if name.lower().endswith(".xml")]
        if not xml_names:
            return []
        data = archive.read(xml_names[0])
    root = ET.fromstring(data)
    source_path = source.get("source_metadata", {}).get("source_path", law["canonical_id"])
    norms = []
    current_article: str | None = None
    article_container_id: str | None = None
    for norm_el in root.iter():
        if _local(norm_el.tag) != "norm":
            continue
        enbez = _first_text(norm_el, "enbez")
        title = _first_text(norm_el, "titel") or _first_text(norm_el, "gliederungstitel")
        gliederungsbez = _first_text(norm_el, "gliederungsbez")
        content = _content_text(norm_el)
        article_value = _extract(ART_RE, gliederungsbez or enbez or "")
        par_value = _extract(PAR_RE, enbez or "")

        if article_value and not par_value:
            current_article = article_value.lower()
            article_container_id = f"art:{current_article}"
            norms.append(
                {
                    "canonical_id": f"{law['canonical_id']}/{article_container_id}",
                    "law_id": law["canonical_id"],
                    "norm_id": article_container_id,
                    "unit": "art",
                    "value": current_article,
                    "title": title,
                    "status": "container" if not content else "active",
                    "text": content or None,
                    "url": f"https://www.gesetze-im-internet.de/{source_path}/art_{current_article}.html",
                    "source": source,
                    "subdivisions": _subdivisions(content),
                    "children": [],
                }
            )
            continue

        if par_value:
            par_value = par_value.lower()
            if current_article and gliederungsbez and _extract(ART_RE, gliederungsbez):
                norm_id = f"art:{current_article}/par:{par_value}"
                url = f"https://www.gesetze-im-internet.de/{source_path}/art_{current_article}__{par_value}.html"
                if norms and norms[-1]["norm_id"] == article_container_id:
                    norms[-1].setdefault("children", []).append(f"{law['canonical_id']}/{norm_id}")
            else:
                norm_id = f"par:{par_value}"
                url = f"https://www.gesetze-im-internet.de/{source_path}/__{par_value}.html"
            norms.append(
                {
                    "canonical_id": f"{law['canonical_id']}/{norm_id}",
                    "law_id": law["canonical_id"],
                    "norm_id": norm_id,
                    "unit": "par",
                    "value": par_value,
                    "title": title,
                    "text": content,
                    "status": "active" if content else "known_issue",
                    "url": url,
                    "source": source,
                    "subdivisions": _subdivisions(content),
                }
            )
    return norms


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _first_text(root: ET.Element, name: str) -> str | None:
    for element in root.iter():
        if _local(element.tag) == name and element.text and element.text.strip():
            return " ".join(element.text.split())
    return None


def _content_text(root: ET.Element) -> str:
    content_nodes = [element for element in root.iter() if _local(element.tag) == "Content"]
    if not content_nodes:
        return ""
    text = " ".join(" ".join(" ".join(node.itertext()).split()) for node in content_nodes)
    return " ".join(text.split())


def _extract(pattern: re.Pattern[str], value: str) -> str | None:
    match = pattern.search(value)
    return match.group(1) if match else None


def _subdivisions(text: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    matches = list(ABS_RE.finditer(text or ""))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        value = match.group(1)
        abs_text = text[start:end].strip()
        path = f"abs:{value}"
        records.append({"kind": "abs", "value": value, "text": abs_text, "path": path})
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", abs_text) if part.strip()]
        for sentence_index, sentence in enumerate(sentences, start=1):
            records.append(
                {
                    "kind": "satz",
                    "value": str(sentence_index),
                    "text": sentence,
                    "path": f"{path}/satz:{sentence_index}",
                }
            )
    return records
