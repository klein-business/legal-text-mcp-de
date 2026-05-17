# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import asyncio

from legal_text_mcp_de.server import create_mcp_app


def _list_prompts(app):
    try:
        result = app.list_prompts()
    except TypeError:
        result = asyncio.get_event_loop().run_until_complete(app.list_prompts())
    if asyncio.iscoroutine(result):
        result = asyncio.get_event_loop().run_until_complete(result)
    return result


def test_prompts_module_registers_module_without_error():
    app = create_mcp_app()
    # Stubs may return empty list; just verify the module loads
    prompts = _list_prompts(app)
    assert isinstance(prompts, list)
