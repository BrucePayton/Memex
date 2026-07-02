"""
Unit tests for dashboard/models.py — frontmatter parsing, wikilink extraction,
slug generation, and data model validation.
"""

import pytest
import sys
from pathlib import Path

# Add parent to path so we can import dashboard modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.models import (
    make_slug, parse_fm, extract_links, extract_citations,
    is_system_page, WikiPage, GraphNode, GraphEdge, SearchResult,
    FRONTMATTER_RE, WIKILINK_RE,
)


class TestMakeSlug:
    def test_english_title(self):
        assert make_slug("Hello World") == "hello-world"

    def test_chinese_title(self):
        result = make_slug("测试页面")
        assert "测试页面" in result

    def test_korean_title(self):
        result = make_slug("한글 페이지")
        assert "한글" in result

    def test_special_characters(self):
        assert make_slug("Hello! @World#") == "hello-world"

    def test_empty_title(self):
        result = make_slug("")
        assert result.startswith("untitled-")


class TestParseFM:
    def test_basic_frontmatter(self):
        text = "---\ntitle: Test Page\ntype: concept\n---\n\n# Content"
        meta, body = parse_fm(text)
        assert meta["title"] == "Test Page"
        assert meta["type"] == "concept"
        assert body.strip() == "# Content"

    def test_list_tags(self):
        text = "---\ntitle: Test\ntags:\n  - tag1\n  - tag2\n---\n\nBody"
        meta, _ = parse_fm(text)
        assert meta["tags"] == ["tag1", "tag2"]

    def test_inline_list(self):
        text = "---\ntitle: Test\ntags: [tag1, tag2]\n---\n\nBody"
        meta, _ = parse_fm(text)
        assert meta["tags"] == ["tag1", "tag2"]

    def test_no_frontmatter(self):
        text = "# Just a heading\n\nContent"
        meta, body = parse_fm(text)
        assert meta == {}
        assert body == text

    def test_multi_language_titles(self):
        text = "---\ntitle: English\ntitle_zh: 中文\ntitle_en: English\ntype: concept\n---\n\nContent"
        meta, _ = parse_fm(text)
        assert meta["title"] == "English"
        assert meta["title_zh"] == "中文"


class TestExtractLinks:
    def test_simple_wikilink(self):
        links = extract_links("See [[target-page]] for more.")
        assert "target-page.md" in links

    def test_wikilink_with_alias(self):
        links = extract_links("See [[target-page|display text]] for more.")
        assert "target-page.md" in links

    def test_wikilink_with_anchor(self):
        links = extract_links("See [[target-page#section]] for more.")
        assert "target-page.md" in links

    def test_multiple_links(self):
        body = "Link to [[page-a]] and [[page-b]] and [[concepts/page-c]]."
        links = extract_links(body)
        assert len(links) == 3
        assert "page-a.md" in links
        assert "page-b.md" in links
        assert "concepts/page-c.md" in links

    def test_no_links(self):
        links = extract_links("Plain text without any wikilinks.")
        assert links == []


class TestExtractCitations:
    def test_single_citation(self):
        body = "Some claim. [^src-test-source]"
        refs = extract_citations(body)
        assert "test-source" in refs

    def test_multiple_citations(self):
        body = "Claim one [^src-source-a] and claim two [^src-source-b]."
        refs = extract_citations(body)
        assert len(refs) == 2

    def test_no_citations(self):
        body = "No citations here."
        refs = extract_citations(body)
        assert refs == []


class TestIsSystemPage:
    def test_index_is_system(self):
        assert is_system_page("index.md")

    def test_log_is_system(self):
        assert is_system_page("log.md")

    def test_overview_is_system(self):
        assert is_system_page("overview.md")

    def test_normal_page_not_system(self):
        assert not is_system_page("concepts/test.md")


class TestDataModels:
    def test_wiki_page_creation(self):
        page = WikiPage(
            path="concepts/test.md",
            title="Test",
            page_type="concept",
        )
        assert page.filename == "test.md"
        assert page.status == "active"
        assert page.confidence == "medium"

    def test_graph_node(self):
        node = GraphNode(id="test.md", label="Test", type="concept")
        assert node.word_count == 0
        assert node.tags == []

    def test_graph_edge(self):
        edge = GraphEdge(from_id="a.md", to_id="b.md")
        assert edge.type == "wikilink"

    def test_search_result(self):
        result = SearchResult(
            page_path="concepts/test.md",
            title="Test",
            snippet="A test page...",
            score=0.95,
        )
        assert result.backend == "tfidf"


class TestRegexPatterns:
    def test_frontmatter_re(self):
        text = "---\ntitle: X\n---\nBody"
        assert FRONTMATTER_RE.match(text)

    def test_wikilink_re(self):
        match = WIKILINK_RE.search("See [[target]] here")
        assert match
        assert match.group(1) == "target"

    def test_wikilink_with_alias_re(self):
        match = WIKILINK_RE.search("See [[target|alias]] here")
        assert match
        assert match.group(1) == "target"
