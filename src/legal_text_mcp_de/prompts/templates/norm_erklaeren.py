# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""/norm-erklaeren — load a norm + relationships, plain-language explanation."""

import textwrap

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base


def register(app: FastMCP) -> None:
    @app.prompt()
    def norm_erklaeren(code: str, norm: str) -> list[base.Message]:
        """Erkläre eine Norm in verständlicher Sprache mit Kontext und Verweisen."""
        body = textwrap.dedent(f"""
            Erkläre die folgende Norm in einfacher, verständlicher Sprache:

            **Gesetz (Code):** {code}
            **Norm:** {norm}

            **Vorgehen:**
            1. Lade den Volltext der Norm über die MCP-Resource:
               `legal://laws/{code}/norms/{norm}`
            2. Lade die Beziehungen (Verweise, Querverweise) über:
               `legal://laws/{code}/norms/{norm}/relationships`
            3. Erstelle eine **Erklärung** in Plain Language (Laiensprache):
               - Was regelt diese Norm? (1-2 Sätze)
               - Für wen gilt sie? (Adressaten)
               - Was sind die wichtigsten Rechtsfolgen?
               - Welche anderen Normen sind eng verwandt (aus den Relationships)?
            4. Schließe mit einem kurzen juristischen Einordnungs-Absatz ab, der
               Fachbegriffe erklärt und den systematischen Kontext im Gesetz erläutert.

            **Format:**
            - Überschrift: `{code} {norm} — Erklärung`
            - Abschnitte: Überblick | Adressaten | Rechtsfolgen | Verwandte Normen | Juristische Einordnung
        """).strip()
        return [base.UserMessage(body)]
