# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from pathlib import Path

import pytest

from scripts.verify_release import check_docs_links, check_no_stale_workflow_refs, selected_tests


PRODUCTION_FILES = [
    Path("Dockerfile"),
    Path("src/legal_text_mcp_de/config.py"),
    Path("src/legal_text_mcp_de/server.py"),
    Path("src/legal_text_mcp_de/http_api.py"),
]


def test_no_production_bundestag_dependency():
    for path in PRODUCTION_FILES:
        text = path.read_text(encoding="utf-8")
        assert "github.com/bundestag/gesetze.git" not in text
        assert "raw.githubusercontent.com/bundestag/gesetze" not in text
    for path in Path("src/legal_text_mcp_de/legal_texts").rglob("*.py"):
        assert "bundestag/gesetze" not in path.read_text(encoding="utf-8")


def test_no_default_app_gesetze_serving_path():
    assert "/app/gesetze" not in Path("src/legal_text_mcp_de/config.py").read_text(encoding="utf-8")
    assert "/app/gesetze" not in Path("Dockerfile").read_text(encoding="utf-8")


def test_no_saas_scope_added():
    production_text = "\n".join(path.read_text(encoding="utf-8").casefold() for path in PRODUCTION_FILES)
    for forbidden in ["billing", "tenant", "subscription", "user account"]:
        assert forbidden not in production_text


def test_known_issues_page_is_documented_as_scope_and_invariants():
    known_issues_doc = Path("docs/features/known-issues.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    overview = Path("docs/overview.md").read_text(encoding="utf-8")

    assert 'feature: "scope-and-invariants"' in known_issues_doc
    assert "# Feature: scope-and-invariants" in known_issues_doc
    assert "## Current Limits" not in known_issues_doc
    assert "## Known Invalid Source Paths" not in known_issues_doc
    assert "structured source-anomaly metadata" in known_issues_doc

    assert "[Known issues]" not in readme
    # Docs section now links to the docs site; the known-issues page content is still valid
    assert "klein-business.github.io/legal-text-mcp-de" in readme
    assert "| known-issues |" not in overview
    assert "| scope-and-invariants |" in overview


def test_docs_link_checker_scans_required_document_roots():
    import scripts.verify_release as verify_release

    roots = {str(path) for path in verify_release.DOC_CHECK_ROOTS}
    assert roots == {"README.md", "docs", "docs-legacy", "plans"}


def test_stale_workflow_checker_scans_docs_legacy_and_plans():
    import scripts.verify_release as verify_release

    roots = {str(path) for path in verify_release.STALE_WORKFLOW_CHECK_ROOTS}
    assert {"docs-legacy", "plans"}.issubset(roots)


def test_stale_workflow_checker_rejects_direct_python3_invocations(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text("PYTHONPATH=mcp " + "python3 -m pytest mcp/tests\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        check_no_stale_workflow_refs([doc])

    assert "unsupported direct" in str(exc.value)


def test_docs_link_checker_rejects_broken_local_markdown_links_and_images(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Docs",
                "[missing](docs/missing.md)",
                "![missing image](assets/missing.png)",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as exc:
        check_docs_links([readme])

    message = str(exc.value)
    assert "broken local Markdown link" in message
    assert "broken local Markdown image" in message


def test_docs_link_checker_rejects_broken_local_html_images(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text('<img src="missing.png" alt="missing">\n', encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        check_docs_links([doc])

    assert "broken local HTML image" in str(exc.value)


def test_docs_link_checker_skips_remote_targets_and_validates_local_anchors(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    page = docs / "page.md"
    target = docs / "target.md"
    page.write_text(
        "\n".join(
            [
                "# Page",
                "[remote](https://example.com/missing)",
                "![remote image](https://example.com/image.png)",
                '<img src="https://example.com/image.png" alt="remote">',
                "[local anchor](target.md#generated-package-flow)",
            ]
        ),
        encoding="utf-8",
    )
    target.write_text("# Generated Package Flow\n", encoding="utf-8")

    check_docs_links([docs])


def test_docs_link_checker_rejects_broken_local_anchor(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    page = docs / "page.md"
    target = docs / "target.md"
    page.write_text("[bad anchor](target.md#missing-section)\n", encoding="utf-8")
    target.write_text("# Existing Section\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        check_docs_links([docs])

    assert "broken local Markdown link anchor" in str(exc.value)


def test_live_source_matrix_remains_opt_in(monkeypatch):
    monkeypatch.delenv("RUN_LIVE_SOURCE_MATRIX", raising=False)
    assert "tests/test_source_matrix_live.py" not in selected_tests()

    monkeypatch.setenv("RUN_LIVE_SOURCE_MATRIX", "true")
    assert "tests/test_source_matrix_live.py" in selected_tests()
