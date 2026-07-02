"""Unit tests for wiki_extensions: version, aliases, types, OKF, edit protection."""

import pytest
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.wiki_extensions import (
    get_version_chain, find_derived_pages,
    load_aliases, suggest_alias_replacements,
    propose_new_type, approve_type, get_allowed_types,
    import_okf_bundle, export_to_okf,
    is_human_edited, mark_human_edited,
)


class TestVersionManagement:
    def test_version_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            # v1
            (wiki / "page.md").write_text(
                "---\ntitle: Page\ntype: concept\nversion: 1\nlast_updated: 2026-01-01\n"
                "superseded_by: page-v2.md\n---\nContent"
            )
            # v2
            (wiki / "page-v2.md").write_text(
                "---\ntitle: Page v2\ntype: concept\nversion: 2\nlast_updated: 2026-06-01\n"
                "status: active\n---\nUpdated content"
            )
            chain = get_version_chain(wiki, "page.md")
            assert len(chain) == 2
            assert chain[0]["version"] in (1, "1")
            assert chain[1]["version"] in (2, "2")

    def test_derived_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            (wiki / "original.md").write_text(
                "---\ntitle: Original\ntype: concept\nversion: 1\n---\nContent"
            )
            (wiki / "derived.md").write_text(
                "---\ntitle: Derived\ntype: concept\nversion: 1\nderived_from: original.md\n---\nContent"
            )
            derived = find_derived_pages(wiki, "original.md")
            assert len(derived) == 1
            assert derived[0]["path"] == "derived.md"


class TestAliases:
    def test_load_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            (wiki / "aliases.md").write_text(
                "| Alias | Canonical |\n|-------|----------|\n| AI | 人工智能 |\n| ML | 机器学习 |\n"
            )
            aliases = load_aliases(wiki)
            assert aliases["AI"] == "人工智能"
            assert aliases["ML"] == "机器学习"

    def test_no_aliases_file(self):
        aliases = load_aliases(Path("/nonexistent"))
        assert aliases == {}

    def test_suggest_replacements(self):
        aliases = {"AI": "人工智能", "ML": "机器学习"}
        text = "AI is transforming industries. ML is a subset of AI."
        suggestions = suggest_alias_replacements(text, aliases)
        assert len(suggestions) == 2
        ai_sug = [s for s in suggestions if s["alias"] == "AI"][0]
        assert ai_sug["count"] == 2


class TestDynamicTypes:
    def test_propose_new_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = propose_new_type(root, "benchmark", "Performance benchmark results")
            assert result["ok"]
            assert result["status"] == "pending"

    def test_duplicate_proposal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            propose_new_type(root, "benchmark", "desc")
            result = propose_new_type(root, "benchmark", "desc2")
            assert result["status"] == "already_pending"

    def test_approve_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            propose_new_type(root, "benchmark", "desc")
            result = approve_type(root, "benchmark")
            assert result["ok"]
            assert "benchmark" in get_allowed_types()

    def test_existing_type_rejected(self):
        result = propose_new_type(Path("/tmp"), "concept", "desc")
        assert not result["ok"]


class TestOKFInterop:
    def test_export_and_reimport(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            (wiki / "test.md").write_text(
                "---\ntitle: Test\ntype: concept\ntags: [a, b]\nlast_updated: 2026-07-01\n---\n\nBody content."
            )

            out_dir = Path(tmp) / "okf-export"
            result = export_to_okf(wiki, out_dir)
            assert result["ok"]
            assert result["exported_count"] == 1

            # Re-import
            wiki2 = Path(tmp) / "wiki2"
            wiki2.mkdir()
            imported = import_okf_bundle(out_dir, wiki2)
            assert len(imported) == 1
            assert imported[0]["title"] == "Test"

    def test_import_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            imported = import_okf_bundle(Path("/nonexistent"), wiki)
            assert len(imported) == 0


class TestEditProtection:
    def test_mark_and_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            page = wiki / "test.md"
            page.write_text(
                "---\ntitle: Test\ntype: concept\nlast_updated: 2026-07-01\n---\nContent"
            )
            assert not is_human_edited(wiki, "test.md")
            mark_human_edited(wiki, "test.md")
            assert is_human_edited(wiki, "test.md")

    def test_already_marked(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            page = wiki / "test.md"
            page.write_text(
                "---\ntitle: T\ntype: concept\nlast_updated: 2026-07-01\nedited_by_human: true\n---\nC"
            )
            assert is_human_edited(wiki, "test.md")
