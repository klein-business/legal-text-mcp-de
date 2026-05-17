# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""/recherche — multi-step research (placeholder until E5 research_topic smart tool)."""

import textwrap

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base


def register(app: FastMCP) -> None:
    @app.prompt()
    def recherche(topic: str) -> list[base.Message]:
        """Führe eine mehrstufige Recherche zu einem Rechtsthema durch."""
        body = textwrap.dedent(f"""
            Führe eine strukturierte Rechtsrecherche zum folgenden Thema durch:

            **Thema:** {topic}

            **Hinweis:** Sobald das Tool `research_topic` (Phase E5) verfügbar ist,
            wird es diesen Workflow automatisieren. Bis dahin gehe manuell vor:

            **Vorgehen:**
            1. Suche relevante Gesetze mit `search_laws` (Query: `{topic}`).
               Notiere die Top-5-Treffer mit Relevanz-Score.
            2. Für jedes relevante Gesetz: lade die wichtigsten Normen über
               `get_norm` oder die MCP-Resource `legal://laws/{{code}}/norms/{{norm_id}}`.
            3. Identifiziere thematische Cluster:
               - Primärnormen (direkte Regelung des Themas)
               - Verweisende Normen (Bezugsregelungen)
               - Legaldefinitionen (falls vorhanden)
            4. Erstelle eine Recherche-Zusammenfassung:
               - Übersicht der einschlägigen Rechtsgebiete
               - Liste der relevanten Gesetze und Normen (mit canonical_id)
               - Offene Fragen / Regelungslücken
               - Quellen-Hinweise (`source.retrieved_at` je Gesetz)

            **Ergebnis-Format:**
            Markdown mit Abschnitten: Überblick | Einschlägige Normen | Verweise | Offene Fragen
        """).strip()
        return [base.UserMessage(body)]
