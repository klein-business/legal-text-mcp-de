# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSpec:
    canonical_id: str
    display_code: str
    source_kind: str
    source_identifier: str
    index_url: str | None
    source_url: str
    invalid_urls: tuple[str, ...] = ()
    metadata: dict[str, str] | None = None


GERMAN_SOURCES = {
    "bgb": ("BGB", "bgb"),
    "egbgb": ("EGBGB", "bgbeg"),
    "ddg": ("DDG", "ddg"),
    "uwg_2004": ("UWG", "uwg_2004"),
    "tdddg": ("TDDDG", "ttdsg"),
    "bdsg_2018": ("BDSG", "bdsg_2018"),
    "bfsg": ("BFSG", "bfsg"),
    "vsbg": ("VSBG", "vsbg"),
    "pangv_2022": ("PAngV", "pangv_2022"),
}


def _gii_spec(canonical_id: str, display_code: str, source_path: str) -> SourceSpec:
    invalid: tuple[str, ...] = ()
    if canonical_id == "tdddg":
        invalid = ("https://www.gesetze-im-internet.de/tddsg/index.html",)
    if canonical_id == "pangv_2022":
        invalid = ("https://www.gesetze-im-internet.de/pangv/index.html",)
    return SourceSpec(
        canonical_id=canonical_id,
        display_code=display_code,
        source_kind="gesetze-im-internet",
        source_identifier=source_path,
        index_url=f"https://www.gesetze-im-internet.de/{source_path}/index.html",
        source_url=f"https://www.gesetze-im-internet.de/{source_path}/xml.zip",
        invalid_urls=invalid,
        metadata={"source_path": source_path},
    )


SOURCE_SPECS: dict[str, SourceSpec] = {
    law_id: _gii_spec(law_id, display_code, source_path)
    for law_id, (display_code, source_path) in GERMAN_SOURCES.items()
}

SOURCE_SPECS["dsgvo_eu_2016_679"] = SourceSpec(
    canonical_id="dsgvo_eu_2016_679",
    display_code="DSGVO",
    source_kind="eur-lex-cellar",
    source_identifier="CELEX:32016R0679",
    index_url=None,
    source_url="https://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0004.02/DOC_2",
    metadata={
        "celex": "32016R0679",
        "cellar_work": "3e485e15-11bd-11e6-ba9a-01aa75ed71a1",
        "expression": "0004.02",
        "language": "DE",
        "document": "DOC_2",
    },
)


def get_source_spec(canonical_id: str) -> SourceSpec:
    return SOURCE_SPECS[canonical_id]
