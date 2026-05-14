from pathlib import Path

from legal_texts.dataset import NormalizedDataset
from legal_texts.runtime import LegalTextRuntime
from server import create_mcp_app


FIXTURE_DATASET = Path(__file__).parent / "fixtures" / "normalized"


def app():
    dataset = NormalizedDataset.load(FIXTURE_DATASET, require_search_index=True)
    return create_mcp_app(LegalTextRuntime.from_dataset(dataset))


def call_tool(application, name, **kwargs):
    return application._tool_manager._tools[name].fn(**kwargs)


def test_tool_registry_has_only_supported_tools():
    names = set(app()._tool_manager._tools)
    assert names == {"list_laws", "get_law", "get_norm", "resolve_citation", "search_laws", "get_source_metadata"}
    assert "get_lawlibrary" not in names
    assert "get_paragraph" not in names


def test_tools_return_json_objects_not_serialized_strings():
    application = app()
    for name, kwargs in {
        "list_laws": {},
        "get_law": {"code": "BGB"},
        "get_norm": {"code": "BGB", "norm": "§ 355"},
        "resolve_citation": {"code": "EGBGB", "unit": "art", "paragraph_or_article": "246a", "child_unit": "par", "child_value": "1"},
        "search_laws": {"query": "Widerrufsrecht", "codes": ["BGB"]},
        "get_source_metadata": {"code": "DSGVO"},
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
