from pathlib import Path


PRODUCTION_FILES = [
    Path("Dockerfile"),
    Path("mcp/config.py"),
    Path("mcp/server.py"),
    Path("mcp/http_api.py"),
]


def test_no_production_bundestag_dependency():
    for path in PRODUCTION_FILES:
        text = path.read_text(encoding="utf-8")
        assert "github.com/bundestag/gesetze.git" not in text
        assert "raw.githubusercontent.com/bundestag/gesetze" not in text
    for path in Path("mcp/legal_texts").rglob("*.py"):
        assert "bundestag/gesetze" not in path.read_text(encoding="utf-8")


def test_no_default_app_gesetze_serving_path():
    assert "/app/gesetze" not in Path("mcp/config.py").read_text(encoding="utf-8")
    assert "/app/gesetze" not in Path("Dockerfile").read_text(encoding="utf-8")


def test_no_saas_scope_added():
    production_text = "\n".join(path.read_text(encoding="utf-8").casefold() for path in PRODUCTION_FILES)
    for forbidden in ["billing", "tenant", "subscription", "user account"]:
        assert forbidden not in production_text
