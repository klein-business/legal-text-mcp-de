from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


LAW_NOT_FOUND = "LAW_NOT_FOUND"
NORM_NOT_FOUND = "NORM_NOT_FOUND"
AMBIGUOUS_LAW_ALIAS = "AMBIGUOUS_LAW_ALIAS"
SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
DATASET_NOT_READY = "DATASET_NOT_READY"
INVALID_CITATION = "INVALID_CITATION"
INVALID_QUERY = "INVALID_QUERY"


HTTP_STATUS_BY_CODE = {
    LAW_NOT_FOUND: 404,
    NORM_NOT_FOUND: 404,
    AMBIGUOUS_LAW_ALIAS: 409,
    SOURCE_UNAVAILABLE: 503,
    DATASET_NOT_READY: 503,
    INVALID_CITATION: 422,
    INVALID_QUERY: 422,
}


@dataclass
class LegalTextError(Exception):
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    suggestions: list[Any] | None = None
    source: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)

    def to_dict(self) -> dict[str, Any]:
        error: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }
        if self.suggestions:
            error["suggestions"] = self.suggestions[:10]
        if self.source:
            error["source"] = self.source
        return {"error": error}

    @property
    def http_status(self) -> int:
        return HTTP_STATUS_BY_CODE.get(self.code, 500)


def law_not_found(code: str, suggestions: list[Any] | None = None) -> LegalTextError:
    return LegalTextError(
        LAW_NOT_FOUND,
        f"Law '{code}' was not found.",
        {"code": code},
        suggestions=suggestions,
    )


def ambiguous_law_alias(code: str, candidates: list[Any]) -> LegalTextError:
    return LegalTextError(
        AMBIGUOUS_LAW_ALIAS,
        f"Law alias '{code}' is ambiguous.",
        {"code": code, "candidate_count": len(candidates)},
        suggestions=candidates[:10],
    )


def norm_not_found(
    law_id: str,
    norm_id: str,
    *,
    requested_code: str | None = None,
    suggestions: list[Any] | None = None,
    details: dict[str, Any] | None = None,
) -> LegalTextError:
    payload = {"law_id": law_id, "norm_id": norm_id}
    if requested_code is not None:
        payload["requested_code"] = requested_code
    if details:
        payload.update(details)
    return LegalTextError(
        NORM_NOT_FOUND,
        f"Norm '{norm_id}' was not found in law '{law_id}'.",
        payload,
        suggestions=suggestions,
    )


def invalid_citation(message: str, details: dict[str, Any] | None = None) -> LegalTextError:
    return LegalTextError(INVALID_CITATION, message, details or {})


def invalid_query(message: str, details: dict[str, Any] | None = None) -> LegalTextError:
    return LegalTextError(INVALID_QUERY, message, details or {})


def dataset_not_ready(message: str, details: dict[str, Any] | None = None) -> LegalTextError:
    return LegalTextError(DATASET_NOT_READY, message, details or {})


def source_unavailable(
    message: str,
    details: dict[str, Any] | None = None,
    source: dict[str, Any] | None = None,
) -> LegalTextError:
    return LegalTextError(SOURCE_UNAVAILABLE, message, details or {}, source=source)


def as_error_dict(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, LegalTextError):
        return exc.to_dict()
    return LegalTextError("INTERNAL_ERROR", str(exc), {}).to_dict()
