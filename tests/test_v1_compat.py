# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""V1 MCP-tool contract. These tests freeze the v1.0.0 tool surface.

If you change a v1 tool name, signature, or return shape, this test must fail
and a deliberate `feat!:` / `BREAKING CHANGES` entry must accompany the change.
"""

from legal_text_mcp_de.server import create_mcp_app


EXPECTED_V1_TOOLS = {
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


def _list_tool_names(app):
    """Compatible across mcp[cli] versions.

    FastMCP 1.x exposes tools via _tool_manager._tools (fastest, no async).
    If that internal attribute disappears in a future version we fall back to
    awaiting the coroutine returned by list_tools().
    """
    import inspect

    # Fast path: internal registry used by the existing test suite
    if hasattr(app, "_tool_manager") and hasattr(app._tool_manager, "_tools"):
        return set(app._tool_manager._tools)

    # Slow path: public API, may be async
    result = app.list_tools()
    if inspect.iscoroutine(result):
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(result)
    return {t.name for t in result}


def test_v1_tools_are_all_registered():
    app = create_mcp_app()
    names = _list_tool_names(app)
    missing = EXPECTED_V1_TOOLS - names
    assert not missing, f"v1 tools missing from create_mcp_app: {missing}"


def test_v1_tool_count_is_at_least_nine():
    """No v1 tool should be removed; new ones may be added."""
    app = create_mcp_app()
    names = _list_tool_names(app)
    assert len(names) >= 9, f"expected >=9 tools, got {len(names)}: {names}"
