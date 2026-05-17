# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""MCP tool registrations."""

from legal_text_mcp_de.tools.research_topic import register_research_topic
from legal_text_mcp_de.tools.v1_tools import register_v1_tools

__all__ = ["register_v1_tools", "register_research_topic"]
