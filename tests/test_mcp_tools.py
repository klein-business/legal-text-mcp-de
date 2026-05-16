# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from pathlib import Path

from legal_text_mcp_de.legal_texts.dataset import NormalizedDataset
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime
from legal_text_mcp_de.server import create_mcp_app


FIXTURE_DATASET = Path(__file__).parent / "fixtures" / "normalized"
GENERATED_PACKAGE = Path(__file__).parent / "fixtures" / "generated_package"


def app():
    dataset = NormalizedDataset.load(FIXTURE_DATASET, require_search_index=True)
    return create_mcp_app(LegalTextRuntime.from_dataset(dataset))


def generated_app():
    dataset = NormalizedDataset.load(GENERATED_PACKAGE, require_search_index=True)
    return create_mcp_app(LegalTextRuntime.from_dataset(dataset))


def call_tool(application, name, **kwargs):
    return application._tool_manager._tools[name].fn(**kwargs)


def test_tool_registry_has_only_supported_tools():
    names = set(app()._tool_manager._tools)
    assert names == {
        "list_laws",
        "get_law",
        "get_norm",
        "resolve_citation",
        "search_laws",
        "get_source_metadata",
        "get_corpus_coverage",
        "get_source_limitations",
        "get_related_norms",
    }
    assert "get_lawlibrary" not in names
    assert "get_paragraph" not in names


def test_tools_return_json_objects_not_serialized_strings():
    application = app()
    for name, kwargs in {
        "list_laws": {},
        "get_law": {"code": "BGB"},
        "get_norm": {"code": "BGB", "norm": "§ 355"},
        "resolve_citation": {
            "code": "EGBGB",
            "unit": "art",
            "paragraph_or_article": "246a",
            "child_unit": "par",
            "child_value": "1",
        },
        "search_laws": {"query": "Widerrufsrecht", "codes": ["BGB"]},
        "get_source_metadata": {"code": "DSGVO"},
        "get_corpus_coverage": {},
        "get_source_limitations": {},
        "get_related_norms": {"code": "BGB", "norm": "§ 355"},
    }.items():
        result = call_tool(application, name, **kwargs)
        assert isinstance(result, dict), name
        assert "{" not in result if isinstance(result, str) else True


def test_structured_errors_from_mcp_tools():
    result = call_tool(app(), "get_norm", code="BGB", norm="§ 999")
    assert result["error"]["code"] == "NORM_NOT_FOUND"


def test_egbgb_child_citation_parameters():
    result = call_tool(
        app(),
        "resolve_citation",
        code="EGBGB",
        unit="art",
        paragraph_or_article="246a",
        child_unit="par",
        child_value="1",
    )
    assert result["norm"]["canonical_id"] == "egbgb/art:246a/par:1"


def test_generated_package_relationship_tools():
    application = generated_app()
    coverage = call_tool(application, "get_corpus_coverage")
    limitations = call_tool(application, "get_source_limitations", source_family="state-law")
    relationships = call_tool(application, "get_related_norms", code="DSGVO", norm="art:5")

    assert coverage["generated_package_present"] is True
    assert limitations["count"] == 1
    assert relationships["relationships"][0]["relationship_id"] == "rel-dsgvo-art5-limitation"
