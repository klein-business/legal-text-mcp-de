# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""/zitation-checken — resolve a citation and format the result with Stand-Datum."""

import textwrap

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base


def register(app: FastMCP) -> None:
    @app.prompt()
    def zitation_checken(citation: str) -> list[base.Message]:
        """Prüfe eine deutsche Normzitation und gib den Stand-Datum aus."""
        body = textwrap.dedent(f"""
            Prüfe die folgende deutsche Normzitation und gib das Ergebnis strukturiert aus:

            **Zitation:** {citation}

            **Vorgehen:**
            1. Rufe das Tool `resolve_citation` mit der Zitation auf.
            2. Falls die Zitation aufgelöst werden kann:
               - Gib `canonical_id`, `title` und den Normentext kurz aus.
               - Zeige das **Stand-Datum** (`source.retrieved_at`) aus der Antwort.
               - Weise auf etwaige Unterschiede zwischen der eingegebenen und der
                 kanonischen Form hin (z. B. fehlende Absatzangabe).
            3. Falls die Zitation nicht aufgelöst werden kann:
               - Erkläre, warum (unbekanntes Gesetz, falsche Paragraphen-Nummer etc.).
               - Schlage ähnliche Normen vor, sofern vorhanden.

            **Ausgabeformat:**
            - Kanonische ID: `<canonical_id>`
            - Stand-Datum: `<retrieved_at>`
            - Kurztext der Norm (max. 3 Sätze)
            - Hinweis auf Abweichungen (falls vorhanden)
        """).strip()
        return [base.UserMessage(body)]
