# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""/dsgvo-check — GDPR compliance walkthrough for a described processing activity."""

import textwrap

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base


def register(app: FastMCP) -> None:
    @app.prompt()
    def dsgvo_check(aktivitaet: str) -> list[base.Message]:
        """Prüfe eine Verarbeitungstätigkeit gegen die relevanten DSGVO-Artikel."""
        body = textwrap.dedent(f"""
            Prüfe die folgende Verarbeitungstätigkeit auf DSGVO-Konformität:

            **Verarbeitungstätigkeit:** {aktivitaet}

            **Checkliste — prüfe jeden Artikel:**

            **Art. 5 — Grundsätze der Verarbeitung**
            Lade `legal://laws/DSGVO/norms/Art. 5` und prüfe:
            - Rechtmäßigkeit, Verarbeitung nach Treu und Glauben, Transparenz
            - Zweckbindung, Datenminimierung, Richtigkeit
            - Speicherbegrenzung, Integrität und Vertraulichkeit, Rechenschaftspflicht

            **Art. 6 — Rechtmäßigkeit der Verarbeitung**
            Lade `legal://laws/DSGVO/norms/Art. 6` und bestimme:
            - Welche Rechtsgrundlage greift (Einwilligung, Vertrag, rechtl. Verpflichtung,
              lebenswichtige Interessen, öffentl. Aufgabe, berechtigte Interessen)?
            - Begründe die Auswahl; prüfe ob Alternativen vorliegen.

            **Art. 7 — Bedingungen für die Einwilligung** (falls Art. 6 Abs. 1 lit. a)
            Lade `legal://laws/DSGVO/norms/Art. 7` und prüfe:
            - Nachweisbarkeit, Widerrufbarkeit, Freiwilligkeit

            **Art. 9 — Besondere Kategorien** (falls relevant)
            Lade `legal://laws/DSGVO/norms/Art. 9` und prüfe ob besondere Kategorien
            betroffen sind und welche Ausnahme greift.

            **Art. 13 — Informationspflichten (Direkterhebung)**
            Lade `legal://laws/DSGVO/norms/Art. 13` und prüfe:
            - Welche Pflichtangaben muss der Verantwortliche bereitstellen?

            **Art. 14 — Informationspflichten (Dritterhebung)**
            Lade `legal://laws/DSGVO/norms/Art. 14` und prüfe:
            - Gilt Art. 14 für diese Aktivität (Daten nicht direkt bei Betroffenen erhoben)?

            **Ergebnis-Format:**
            Für jeden Artikel: Status (✓ erfüllt / ✗ nicht erfüllt / ? unklar), Begründung,
            erforderliche Maßnahmen. Abschließende Gesamtbewertung mit Handlungsempfehlungen.
        """).strip()
        return [base.UserMessage(body)]
