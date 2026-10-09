# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import asyncio

from legal_text_mcp_de.server import create_mcp_app


def _list_prompts(app):
    return asyncio.run(app.list_prompts())


def test_prompts_module_registers_module_without_error():
    app = create_mcp_app()
    # Stubs may return empty list; just verify the module loads
    prompts = _list_prompts(app)
    assert isinstance(prompts, list)
