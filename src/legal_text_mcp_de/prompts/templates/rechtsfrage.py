# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""/rechtsfrage — answer a German legal question with exact norm citations."""

import textwrap

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base


def register(app: FastMCP) -> None:
    @app.prompt()
    def rechtsfrage(frage: str, rechtsgebiet: str | None = None) -> list[base.Message]:
        """Beantworte eine deutsche Rechtsfrage mit exakten Norm-Zitaten."""
        rechtsgebiet_line = f"**Rechtsgebiet:** {rechtsgebiet}" if rechtsgebiet else ""
        body = textwrap.dedent(f"""
            Beantworte folgende deutsche Rechtsfrage präzise und mit exakten Norm-Zitaten:

            **Frage:** {frage}
            {rechtsgebiet_line}

            **Vorgehen:**
            1. Identifiziere die relevanten Gesetze. Nutze das Tool `list_laws` mit
               einer thematischen Such-Query oder lade direkt die passenden Codes.
            2. Lade die einschlägigen Normen über MCP-Resources
               (`legal://laws/{{code}}/norms/{{norm_id}}`) statt sie als Tool zu ziehen —
               du brauchst den Volltext im Kontext.
            3. Antworte mit:
               - Kurzer Antwort (1-3 Sätze)
               - Maßgebliche Normen mit canonical_id und Stand-Datum
               - Begründungs-Logik
               - Quellen-Hinweis (`source.retrieved_at`)
            4. **Wichtig:** Wenn die Frage außerhalb des aktuellen Korpus liegt,
               sage das klar und nenne den fehlenden Bereich.
        """).strip()
        return [base.UserMessage(body)]
