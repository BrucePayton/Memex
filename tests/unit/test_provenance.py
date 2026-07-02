"""
Unit tests for improved claim detection in dashboard/provenance.py.
Tests Markdown-aware parsing vs old regex-only approach.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.provenance import (
    _extract_prose_claims, _strip_frontmatter,
    parse_citations, _count_claims, validate_page,
    CITE_REF_RE, CITE_DEF_RE,
)


FIXTURES = Path(__file__).parent.parent / "fixtures" / "sample_wiki"


class TestStripFrontmatter:
    def test_strips_yaml(self):
        text = "---\ntitle: X\ntype: concept\n---\n\nBody content."
        body = _strip_frontmatter(text)
        assert "Body content" in body
        assert "title:" not in body

    def test_no_frontmatter_passthrough(self):
        text = "# Heading\nBody."
        body = _strip_frontmatter(text)
        assert body == text


class TestExtractProseClaims:
    def test_basic_claim(self):
        body = "This is a factual claim about AI."
        claims = _extract_prose_claims(body)
        assert len(claims) == 1
        assert "factual claim" in claims[0]

    def test_heading_excluded(self):
        body = "# This is a heading."
        claims = _extract_prose_claims(body)
        assert len(claims) == 0

    def test_blockquote_excluded(self):
        body = "> This is a quote."
        claims = _extract_prose_claims(body)
        assert len(claims) == 0

    def test_list_item_excluded(self):
        body = "- This is a list item."
        claims = _extract_prose_claims(body)
        assert len(claims) == 0

    def test_ordered_list_excluded(self):
        body = "1. First item."
        claims = _extract_prose_claims(body)
        assert len(claims) == 0

    def test_code_block_excluded(self):
        body = "```\nprint('hello.')\n```\nReal claim."
        claims = _extract_prose_claims(body)
        assert len(claims) == 1
        assert "Real claim" in claims[0]

    def test_table_row_excluded(self):
        body = "| Namespace  | Strategy   |"
        claims = _extract_prose_claims(body)
        assert len(claims) == 0

    def test_chinese_claims(self):
        body = "这是第一个声明。\n这是第二个声明。"
        claims = _extract_prose_claims(body)
        assert len(claims) == 2

    def test_mixed_claims(self):
        body = """# Heading

This is a valid claim with [^src-test].

> This is a blockquote.

- This is a list item.

Another valid claim here.

```
Code block with periods.
```

Final claim here."""
        claims = _extract_prose_claims(body)
        assert len(claims) == 3
        assert any("valid claim" in c for c in claims)
        assert any("Final claim" in c for c in claims)

    def test_empty_line_ignored(self):
        body = "\n\n\n"
        claims = _extract_prose_claims(body)
        assert len(claims) == 0


class TestParseCitations:
    def test_inline_citation(self):
        body = "Attention is all you need[^src-attention-paper]."
        refs = parse_citations(body)
        assert "src-attention-paper" in refs

    def test_multiple_citations(self):
        body = "Claim one[^src-a]. Claim two[^src-b]. Claim three[^src-a]."
        refs = parse_citations(body)
        assert len(refs["src-a"]) == 2
        assert len(refs["src-b"]) == 1

    def test_definition_not_counted_as_ref(self):
        """[^src-x]: ... definitions should not be counted as inline refs."""
        body = "Claim[^src-a].\n\n[^src-a]: [[source-a]]"
        refs = parse_citations(body)
        # CITE_REF_RE uses (?!:) to avoid matching definitions
        assert len(refs["src-a"]) == 1


class TestCountClaims:
    def test_basic_counting(self):
        text = """---
title: Test
type: concept
---

This is a claim with citation[^src-test].

This claim has no citation.

# Heading excluded.

- List excluded.

Another cited claim[^src-test]."""
        total, cited = _count_claims(text)
        # Should find 3 prose claims (excludes heading, list)
        assert total == 3
        assert cited == 2


class TestValidatePage:
    def test_sample_concept_page(self):
        page_path = FIXTURES / "concepts" / "test-concept.md"
        result = validate_page(page_path, FIXTURES)
        # The sample page has 1 prose claim (no citation) + list items (excluded)
        assert result["total_claims"] >= 1
        assert result["coverage"] <= 100.0
        assert "undefined_refs" in result

    def test_page_with_citations(self):
        """Page with inline prose citations should have high coverage."""
        text = """---
title: Cited Page
type: concept
---

This is a factual claim with evidence[^src-ref-a].

Another important point supported by research[^src-ref-b].

- List items should be excluded[^src-ref-c]

# Headings should be excluded.

[^src-ref-a]: [[source-a]]
[^src-ref-b]: [[source-b]]
[^src-ref-c]: [[source-c]]"""
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            wiki = tmp_path / "wiki"
            wiki.mkdir()
            page = wiki / "cited.md"
            page.write_text(text)
            (wiki / "source-a.md").write_text("---\ntitle: Src A\ntype: source-summary\n---\n.")
            (wiki / "source-b.md").write_text("---\ntitle: Src B\ntype: source-summary\n---\n.")
            (wiki / "source-c.md").write_text("---\ntitle: Src C\ntype: source-summary\n---\n.")
            result = validate_page(page, wiki)
            # 2 prose claims, both cited (list items excluded)
            assert result["total_claims"] == 2
            assert result["cited_claims"] == 2
            assert result["coverage"] == 100.0
