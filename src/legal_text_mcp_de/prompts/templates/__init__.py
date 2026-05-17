# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Curated prompt templates."""

from mcp.server.fastmcp import FastMCP

from legal_text_mcp_de.prompts.templates import (
    dsgvo_check,
    norm_erklaeren,
    recherche,
    rechtsfrage,
    zitation_checken,
)


def register_prompts(app: FastMCP) -> None:
    rechtsfrage.register(app)
    zitation_checken.register(app)
    norm_erklaeren.register(app)
    recherche.register(app)
    dsgvo_check.register(app)
