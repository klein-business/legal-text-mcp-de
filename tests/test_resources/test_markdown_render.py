# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from legal_text_mcp_de.resources.markdown_render import render_norm, render_law


def test_render_norm_produces_h1_and_provenance_and_text():
    norm_data = {
        "law": {"display_code": "BGB", "canonical_id": "bgb"},
        "norm": {
            "display_id": "§ 1",
            "title": "Beginn der Rechtsfähigkeit",
            "text": "Die Rechtsfähigkeit des Menschen beginnt mit der Vollendung der Geburt.",
        },
        "source": {
            "retrieved_at": "2026-05-17T00:00:00Z",
            "source_url": "https://gesetze-im-internet.de/bgb/__1.html",
            "stand_date": "2026-04-30",
        },
        "related": [],
    }
    md = render_norm(norm_data)
    assert md.startswith("# § 1 BGB")
    assert "Beginn der Rechtsfähigkeit" in md
    assert "Stand:" in md
    assert "Retrieved:" in md
    assert "Die Rechtsfähigkeit des Menschen" in md
    assert "https://gesetze-im-internet.de/bgb/__1.html" in md


def test_render_norm_lists_querverweise_when_related_present():
    norm_data = {
        "law": {"display_code": "BGB", "canonical_id": "bgb"},
        "norm": {"display_id": "§ 433", "title": "x", "text": "y"},
        "source": {"retrieved_at": "x", "source_url": "x", "stand_date": "x"},
        "related": [
            {"canonical_id": "bgb/par:280"},
            {"canonical_id": "bgb/par:437"},
        ],
    }
    md = render_norm(norm_data)
    assert "Querverweise" in md
    assert "bgb/par:280" in md
    assert "bgb/par:437" in md


def test_render_norm_handles_missing_optional_fields():
    minimal = {
        "law": {"display_code": "BGB", "canonical_id": "bgb"},
        "norm": {"display_id": "§ 1", "title": "", "text": ""},
        "source": {},
        "related": [],
    }
    md = render_norm(minimal)
    # Should not raise and should still produce a heading
    assert md.startswith("# § 1 BGB")


def test_render_law_includes_norm_index_with_resource_uris():
    law_data = {
        "law": {
            "display_code": "BGB",
            "display_name": "Bürgerliches Gesetzbuch",
            "canonical_id": "bgb",
            "stand_date": "2026-04-30",
            "norm_count": 2,
        },
        "norms": [
            {"display_id": "§ 1", "norm_id": "par:1", "title": "Beginn"},
            {"display_id": "§ 2", "norm_id": "par:2", "title": "Volljährigkeit"},
        ],
    }
    md = render_law(law_data)
    assert md.startswith("# BGB — Bürgerliches Gesetzbuch")
    assert "Anzahl Normen" in md
    assert "legal://laws/bgb/norms/par:1" in md
    assert "legal://laws/bgb/norms/par:2" in md
    assert "Beginn" in md
    assert "Volljährigkeit" in md
