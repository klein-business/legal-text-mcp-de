# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Focused tests for mcp.legal_texts.normalizer — normalize_snapshot."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from legal_texts.normalizer import normalize_snapshot
from legal_texts.registry import LawRegistry


# Minimal GII XML for a single norm
_MINIMAL_GII_XML = """<dokumente>
  <norm>
    <metadaten>
      <enbez>§ 1</enbez>
      <titel>Allgemeines</titel>
    </metadaten>
    <textdaten>
      <text>
        <Content>
          <P>(1) Dieser Paragraph gilt allgemein.</P>
        </Content>
      </text>
    </textdaten>
  </norm>
</dokumente>"""

# Minimal EUR-Lex XML for a single DSGVO article
_MINIMAL_EURLEX_XML = """<ROOT>
  <LG.DOC>DE</LG.DOC>
  <ACT>
    <ARTICLE IDENTIFIER="001">
      <TI.ART>Artikel 1</TI.ART>
      <P>Gegenstand und Ziele.</P>
    </ARTICLE>
  </ACT>
</ROOT>"""


def _make_gii_zip(directory: Path, filename: str = "xml.zip") -> Path:
    """Create a GII-format zip with one XML file."""
    zip_path = directory / filename
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("law.xml", _MINIMAL_GII_XML)
    return zip_path


def _make_registry(canonical_id: str = "bgb", source_kind: str = "gesetze-im-internet") -> LawRegistry:
    """Build a minimal registry with one law entry."""
    return LawRegistry.from_entries(
        [
            {
                "canonical_id": canonical_id,
                "display_code": canonical_id.upper(),
                "display_name": f"Test {canonical_id.upper()} law",
                "source_kind": source_kind,
                "source_identifier": canonical_id,
                "source_url": f"https://www.gesetze-im-internet.de/{canonical_id}/xml.zip",
                "aliases": [],
            }
        ],
        validate=False,
    )


def _make_manifest(raw_path: Path, canonical_id: str, source_kind: str = "gesetze-im-internet") -> dict:
    """Build a minimal manifest dict."""
    return {
        "entries": [
            {
                "canonical_id": canonical_id,
                "raw_path": str(raw_path),
                "source": {
                    "source_kind": source_kind,
                    "source_identifier": canonical_id,
                    "source_url": f"https://www.gesetze-im-internet.de/{canonical_id}/xml.zip",
                    "retrieved_at": "2026-01-01T00:00:00Z",
                    "stand_date": "2026-01-01",
                    "stand_date_status": "exact",
                    "content_hash": "sha256:aabbccdd",
                    "source_metadata": {"source_path": canonical_id},
                },
            }
        ]
    }


def test_normalize_snapshot_gii_single_norm(tmp_path: Path) -> None:
    """normalize_snapshot writes laws.json, norms.json, readiness.json for a GII law."""
    zip_path = _make_gii_zip(tmp_path)
    registry = _make_registry("bgb")
    manifest = _make_manifest(zip_path, "bgb")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output_dir = tmp_path / "output"

    readiness = normalize_snapshot(manifest_path, output_dir, registry=registry)

    assert readiness["stage"] == "normalized_dataset"
    assert readiness["state"] == "ready"
    assert readiness["details"]["law_count"] == 1
    assert readiness["details"]["norm_count"] >= 1

    laws = json.loads((output_dir / "laws.json").read_text(encoding="utf-8"))
    assert len(laws) == 1
    assert laws[0]["canonical_id"] == "bgb"

    norms = json.loads((output_dir / "norms.json").read_text(encoding="utf-8"))
    assert len(norms) >= 1
    assert norms[0]["law_id"] == "bgb"

    ready_data = json.loads((output_dir / "readiness.json").read_text(encoding="utf-8"))
    assert ready_data["state"] == "ready"


def test_normalize_snapshot_creates_output_directory(tmp_path: Path) -> None:
    """normalize_snapshot creates output_dir if it does not exist."""
    zip_path = _make_gii_zip(tmp_path)
    registry = _make_registry("uwg_2004")
    manifest = _make_manifest(zip_path, "uwg_2004")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output_dir = tmp_path / "nested" / "output"

    assert not output_dir.exists()
    normalize_snapshot(manifest_path, output_dir, registry=registry)
    assert output_dir.is_dir()


def test_normalize_snapshot_empty_entries(tmp_path: Path) -> None:
    """normalize_snapshot with no entries produces empty laws/norms files."""
    manifest = {"entries": []}
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output_dir = tmp_path / "output"
    registry = LawRegistry.from_entries([], validate=False)

    readiness = normalize_snapshot(manifest_path, output_dir, registry=registry)

    assert readiness["details"]["law_count"] == 0
    assert readiness["details"]["norm_count"] == 0
    laws = json.loads((output_dir / "laws.json").read_text(encoding="utf-8"))
    assert laws == []


def test_normalize_snapshot_stand_date_propagated(tmp_path: Path) -> None:
    """stand_date from source is propagated to the law record."""
    zip_path = _make_gii_zip(tmp_path)
    registry = _make_registry("vsbg")
    manifest = _make_manifest(zip_path, "vsbg")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output_dir = tmp_path / "output"

    normalize_snapshot(manifest_path, output_dir, registry=registry)

    laws = json.loads((output_dir / "laws.json").read_text(encoding="utf-8"))
    assert laws[0]["stand_date"] == "2026-01-01"


def test_normalize_snapshot_eurlex_law(tmp_path: Path) -> None:
    """normalize_snapshot delegates to parse_dsgvo_xml for eur-lex-cellar source_kind."""
    xml_path = tmp_path / "dsgvo.xml"
    xml_path.write_text(_MINIMAL_EURLEX_XML, encoding="utf-8")

    registry = _make_registry("dsgvo_eu_2016_679", source_kind="eur-lex-cellar")
    manifest = {
        "entries": [
            {
                "canonical_id": "dsgvo_eu_2016_679",
                "raw_path": str(xml_path),
                "source": {
                    "source_kind": "eur-lex-cellar",
                    "source_identifier": "CELEX:32016R0679",
                    "source_url": "https://publications.europa.eu/resource/cellar/3e485e15-11bd.0004.02/DOC_2",
                    "retrieved_at": "2026-01-01T00:00:00Z",
                    "stand_date": None,
                    "stand_date_status": "unknown",
                    "content_hash": "sha256:aabbccdd",
                    "source_metadata": {"document": "DOC_2"},
                },
            }
        ]
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output_dir = tmp_path / "output"

    readiness = normalize_snapshot(manifest_path, output_dir, registry=registry)

    assert readiness["details"]["law_count"] == 1
    norms = json.loads((output_dir / "norms.json").read_text(encoding="utf-8"))
    assert len(norms) >= 1
    assert norms[0]["law_id"] == "dsgvo_eu_2016_679"


def test_normalize_snapshot_default_registry(tmp_path: Path) -> None:
    """normalize_snapshot loads the default registry when none is passed."""
    manifest = {"entries": []}
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output_dir = tmp_path / "output"

    # Should not raise — uses the real registry file bundled with the package
    readiness = normalize_snapshot(manifest_path, output_dir)
    assert readiness["state"] == "ready"
