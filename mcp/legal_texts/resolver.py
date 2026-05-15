from __future__ import annotations

import re
from typing import Any

from .dataset import NormalizedDataset
from .errors import invalid_citation, norm_not_found
from .models import canonical_norm_id, normalize_unit, normalize_value


VALUE_RE = re.compile(r"^[0-9]+[a-z]?$", re.IGNORECASE)
STRUCTURAL_VALUE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$", re.IGNORECASE)
CANONICAL_NORM_RE = re.compile(
    r"^(par|art|recital|chapter|section|annex|container):([a-z0-9][a-z0-9_-]*)(?:/(par):([0-9]+[a-z]?))?$",
    re.IGNORECASE,
)
SECTION_SHORTHAND_RE = re.compile(r"^§\s*([0-9]+[a-z]?)$", re.IGNORECASE)
ARTICLE_SHORTHAND_RE = re.compile(r"^Art\.?\s*([0-9]+[a-z]?)$", re.IGNORECASE)


def resolve_citation(
    dataset: NormalizedDataset,
    code: str,
    unit: str,
    paragraph_or_article: str,
    child_unit: str | None = None,
    child_value: str | None = None,
    absatz: str | None = None,
    satz: str | None = None,
    nummer: str | None = None,
    buchstabe: str | None = None,
) -> dict[str, Any]:
    try:
        normalized_unit = normalize_unit(unit)
    except ValueError as exc:
        raise invalid_citation(str(exc), {"unit": unit}) from exc
    value = _validate_value(normalized_unit, paragraph_or_article, "paragraph_or_article")

    child_norm_id = None
    if child_unit or child_value:
        if normalized_unit != "art":
            raise invalid_citation("Child unit is only valid for article citations.", {"unit": unit})
        if not child_unit or not child_value:
            raise invalid_citation("child_unit and child_value must be provided together.", {})
        try:
            normalized_child_unit = normalize_unit(child_unit)
        except ValueError as exc:
            raise invalid_citation(str(exc), {"child_unit": child_unit}) from exc
        if normalized_child_unit != "par":
            raise invalid_citation("Only paragraph child units are supported.", {"child_unit": child_unit})
        child_norm_id = f"par:{_validate_value('par', child_value, 'child_value')}"

    _validate_subdivision_hierarchy(absatz, satz, nummer, buchstabe)

    law = dataset.law_record(code)
    norm_id = canonical_norm_id(normalized_unit, value)
    if child_norm_id:
        norm_id = f"{norm_id}/{child_norm_id}"
    norm = dataset.get_norm_by_id(law["canonical_id"], norm_id)

    response = {
        "law": law,
        "norm": norm,
        "selection": None,
        "citation": {
            "requested": {
                "code": code,
                "unit": unit,
                "paragraph_or_article": paragraph_or_article,
                "child_unit": child_unit,
                "child_value": child_value,
                "absatz": absatz,
                "satz": satz,
                "nummer": nummer,
                "buchstabe": buchstabe,
            },
            "canonical": {
                "law_id": law["canonical_id"],
                "norm_id": norm["norm_id"],
                "canonical_id": norm["canonical_id"],
            },
            "label": _label(law["display_code"], norm),
        },
        "source": norm["source"],
    }

    requested_path = _subdivision_path(absatz, satz, nummer, buchstabe)
    if requested_path:
        response["selection"] = _select_subdivision(norm, requested_path)

    return response


def get_norm(dataset: NormalizedDataset, code: str, norm: str) -> dict[str, Any]:
    parsed = parse_norm_reference(norm)
    return resolve_citation(dataset, code=code, **parsed)


def parse_norm_reference(norm: str) -> dict[str, str | None]:
    value = norm.strip()
    if " bis " in value.casefold() or value.startswith("§§"):
        raise invalid_citation("Ranges are not valid exact norm references.", {"norm": norm})

    match = CANONICAL_NORM_RE.match(value)
    if match:
        unit, norm_value, child_unit, child_value = match.groups()
        return {
            "unit": unit.lower(),
            "paragraph_or_article": norm_value.lower(),
            "child_unit": child_unit.lower() if child_unit else None,
            "child_value": child_value.lower() if child_value else None,
        }

    match = SECTION_SHORTHAND_RE.match(value)
    if match:
        return {"unit": "par", "paragraph_or_article": match.group(1).lower(), "child_unit": None, "child_value": None}

    match = ARTICLE_SHORTHAND_RE.match(value)
    if match:
        return {"unit": "art", "paragraph_or_article": match.group(1).lower(), "child_unit": None, "child_value": None}

    if VALUE_RE.match(value):
        return {"unit": "par", "paragraph_or_article": value.lower(), "child_unit": None, "child_value": None}

    raise invalid_citation("Unsupported norm reference.", {"norm": norm})


def _validate_value(unit: str, value: str, field: str) -> str:
    normalized = normalize_value(value)
    if unit in {"par", "art", "recital"}:
        if not VALUE_RE.match(normalized):
            raise invalid_citation("Citation value is invalid.", {field: value})
        return normalized
    if unit in {"chapter", "section", "annex", "container"} and STRUCTURAL_VALUE_RE.match(normalized):
        return normalized
    if unit in {"chapter", "section", "annex", "container"}:
        raise invalid_citation("Structural citation value is invalid.", {field: value})
    if not VALUE_RE.match(normalized):
        raise invalid_citation("Citation value is invalid.", {field: value})
    return normalized


def _validate_subdivision_hierarchy(
    absatz: str | None,
    satz: str | None,
    nummer: str | None,
    buchstabe: str | None,
) -> None:
    if satz and not absatz:
        raise invalid_citation("satz requires absatz.", {"satz": satz})
    if nummer and not absatz:
        raise invalid_citation("nummer requires absatz.", {"nummer": nummer})
    if buchstabe and not nummer:
        raise invalid_citation("buchstabe requires nummer.", {"buchstabe": buchstabe})


def _subdivision_path(absatz: str | None, satz: str | None, nummer: str | None, buchstabe: str | None) -> str | None:
    parts: list[str] = []
    if absatz:
        parts.append(f"abs:{normalize_value(absatz)}")
    if satz:
        parts.append(f"satz:{normalize_value(satz)}")
    if nummer:
        parts.append(f"nr:{normalize_value(nummer)}")
    if buchstabe:
        parts.append(f"lit:{normalize_value(buchstabe)}")
    return "/".join(parts) if parts else None


def _select_subdivision(norm: dict[str, Any], requested_path: str) -> dict[str, Any]:
    subdivisions = norm.get("subdivisions") or []
    by_path = {item["path"]: item for item in subdivisions}
    if requested_path not in by_path:
        raise norm_not_found(
            norm["law_id"],
            norm["norm_id"],
            details={
                "missing_component": "subdivision",
                "parent_norm_id": norm["norm_id"],
                "subdivision_path": requested_path,
            },
        )
    selected_parts: list[dict[str, Any]] = []
    current: list[str] = []
    for part in requested_path.split("/"):
        current.append(part)
        path = "/".join(current)
        if path in by_path:
            selected_parts.append(by_path[path])
    selected = by_path[requested_path]
    return {
        "requested_path": requested_path,
        "resolved_path": requested_path,
        "subdivisions": selected_parts,
        "text": selected["text"],
        "known_issues": selected.get("known_issues", []),
    }


def _label(display_code: str, norm: dict[str, Any]) -> str:
    if "/par:" in norm["norm_id"]:
        article, section = norm["norm_id"].split("/par:", 1)
        return f"{display_code} Art. {article.split(':', 1)[1]} § {section}"
    if norm["unit"] == "par":
        return f"{display_code} § {norm['value']}"
    if norm["unit"] == "recital":
        return f"{display_code} ErwG {norm['value']}"
    labels = {
        "art": "Art.",
        "chapter": "Kapitel",
        "section": "Abschnitt",
        "annex": "Anhang",
        "container": "Container",
    }
    return f"{display_code} {labels.get(norm['unit'], norm['unit'])} {norm['value']}"
