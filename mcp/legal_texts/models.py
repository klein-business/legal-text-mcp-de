from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


SourceKind = Literal["gesetze-im-internet", "eur-lex-cellar"]
NormUnit = Literal["par", "art"]
NormStatus = Literal["active", "repealed", "container", "known_issue"]
ReadinessState = Literal["ready", "missing", "invalid", "source_unavailable"]
ReadinessStage = Literal["normalized_dataset", "serving_dataset"]


def drop_none(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


@dataclass
class SourceMetadata:
    source_kind: SourceKind
    source_identifier: str
    source_url: str
    retrieved_at: str
    stand_date: str | None
    stand_date_status: str
    content_hash: str
    stand_date_issue: str | None = None
    source_metadata: dict[str, Any] | None = None
    known_issues: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        return drop_none(asdict(self))


@dataclass
class LawRecord:
    canonical_id: str
    display_code: str
    display_name: str
    source: dict[str, Any]
    aliases: list[str]
    norm_count: int
    stand_date: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return drop_none(asdict(self))


@dataclass
class SubdivisionRecord:
    kind: str
    value: str
    text: str
    path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NormRecord:
    canonical_id: str
    law_id: str
    norm_id: str
    unit: NormUnit
    value: str
    title: str | None
    text: str | None
    status: NormStatus
    url: str
    source: dict[str, Any]
    subdivisions: list[dict[str, Any]] = field(default_factory=list)
    children: list[str] = field(default_factory=list)
    known_issues: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if not data["children"]:
            data.pop("children")
        if not data["subdivisions"]:
            data.pop("subdivisions")
        if not data["known_issues"]:
            data.pop("known_issues")
        if data["text"] is None:
            data.pop("text")
        return data


@dataclass
class CitationSelection:
    requested_path: str
    resolved_path: str
    subdivisions: list[dict[str, Any]]
    text: str
    known_issues: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        return drop_none(asdict(self))


@dataclass
class Readiness:
    stage: ReadinessStage
    state: ReadinessState
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"stage": self.stage, "state": self.state, "details": self.details}


def canonical_norm_id(unit: str, value: str) -> str:
    normalized_unit = normalize_unit(unit)
    return f"{normalized_unit}:{normalize_value(value)}"


def canonical_citation_id(law_id: str, norm_id: str) -> str:
    return f"{law_id}/{norm_id}"


def normalize_unit(unit: str) -> NormUnit:
    value = unit.strip().lower().replace(".", "")
    if value in {"§", "par", "section"}:
        return "par"
    if value in {"art", "article"}:
        return "art"
    raise ValueError(f"Unsupported unit: {unit}")


def normalize_value(value: str) -> str:
    return value.strip().lower().replace(" ", "")


def norm_summary(norm: dict[str, Any]) -> dict[str, Any]:
    return {
        "norm_id": norm["norm_id"],
        "canonical_id": norm["canonical_id"],
        "unit": norm["unit"],
        "value": norm["value"],
        "title": norm.get("title"),
        "status": norm["status"],
        "url": norm["url"],
    }
