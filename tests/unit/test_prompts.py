"""Unit tests for dashboard/llm/prompts.py — prompt template generation."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.llm.prompts import (
    ingest_prompt, lint_prompt, lint_fix_prompt,
    reflect_prompt, write_prompt, compare_prompt,
    loop_prompt, index_instruction,
)


class TestIngestPrompt:
    def test_basic(self):
        p = ingest_prompt(title="Test Doc", content="Hello world")
        assert "Test Doc" in p
        assert "Hello world" in p
        assert "frontmatter" in p
        assert "[^src-" in p
        assert "Contradiction Policy" in p

    def test_with_folder(self):
        p = ingest_prompt(title="X", content="Y", folder="concepts")
        assert "wiki/concepts/" in p

    def test_with_project(self):
        p = ingest_prompt(title="X", content="Y", project="my-project")
        assert "my-project" in p


class TestLintPrompt:
    def test_structure(self):
        p = lint_prompt("test")
        assert "Structure Checks" in p
        assert "Citation Checks" in p
        assert "Link Checks" in p
        assert "Freshness Checks" in p
        assert "Contradiction Checks" in p
        assert "Critical" in p or "critical" in p.lower()

    def test_lint_fix(self):
        p = lint_fix_prompt()
        assert "frontmatter" in p
        assert "wikilinks" in p


class TestReflectPrompt:
    def test_basic(self):
        p = reflect_prompt("last-10-ingests", "test")
        assert "analyze" in p.lower() or "Analyze" in p
        assert "patterns" in p.lower() or "Patterns" in p

    def test_default_window(self):
        p = reflect_prompt()
        assert "last-10-ingests" in p


class TestWritePrompt:
    def test_blog_style(self):
        p = write_prompt("AI", style="blog")
        assert "hook" in p.lower()
        assert "AI" in p

    def test_paper_style(self):
        p = write_prompt("AI", style="paper")
        assert "abstract" in p.lower()

    def test_explainer_style(self):
        p = write_prompt("AI", style="explainer")
        assert "educational" in p.lower() or "progressive" in p.lower()

    def test_length_short(self):
        p = write_prompt("AI", length="short")
        assert "500" in p

    def test_length_long(self):
        p = write_prompt("AI", length="long")
        assert "3000" in p


class TestComparePrompt:
    def test_basic(self):
        p = compare_prompt("page-a", "page-b")
        assert "page-a" in p
        assert "page-b" in p
        assert "Common Ground" in p
        assert "Differences" in p

    def test_with_save_as(self):
        p = compare_prompt("a", "b", save_as="comparison-result")
        assert "comparison-result" in p


class TestLoopPrompt:
    def test_basic(self):
        p = loop_prompt(["lint", "lint_fix", "reflect"])
        assert "lint" in p
        assert "lint_fix" in p
        assert "reflect" in p
        assert "Progress Tracking" in p

    def test_with_ingest(self):
        p = loop_prompt(["lint"], include_ingest=True)
        assert "ingest" in p.lower()


class TestIndexInstruction:
    def test_flat_mode(self):
        i = index_instruction("flat", 30)
        assert "30 pages" in i or "30" in i
        assert "index.md" in i

    def test_hierarchical_mode(self):
        i = index_instruction("hierarchical", 120)
        assert "120" in i
        assert "sub-indexes" in i or "index-concepts" in i

    def test_indexed_mode(self):
        i = index_instruction("indexed", 250)
        assert "250" in i
        assert "search" in i.lower()
