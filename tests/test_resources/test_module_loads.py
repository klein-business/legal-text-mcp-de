# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import asyncio

from legal_text_mcp_de.server import create_mcp_app


def _list_resources(app):
    try:
        result = app.list_resources()
    except TypeError:
        result = asyncio.get_event_loop().run_until_complete(app.list_resources())
    if asyncio.iscoroutine(result):
        result = asyncio.get_event_loop().run_until_complete(result)
    return result


def test_resources_module_registers_at_least_one_resource():
    app = create_mcp_app()
    resources = _list_resources(app)
    uris = [str(r.uri) for r in resources]
    assert any(u.startswith("legal://") for u in uris), f"no legal:// uri in {uris}"
