"""Unit tests for search engine backends."""

import pytest
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.search.engine import (
    TFIDFBackend, HybridBackend, create_search_engine,
    _tokenize, SearchBackend,
)


FIXTURES = Path(__file__).parent.parent / "fixtures" / "sample_wiki"


class TestTokenizer:
    def test_english_words(self):
        tokens = _tokenize("hello world test")
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens

    def test_chinese_bigrams(self):
        tokens = _tokenize("测试页面内容")
        assert len(tokens) > 0  # Should produce bigrams

    def test_mixed_language(self):
        tokens = _tokenize("Attention机制 测试")
        assert "attention" in tokens
        assert len(tokens) > 1

    def test_short_words_filtered(self):
        tokens = _tokenize("a b c at")
        # Single chars are filtered, "at" is 2 chars so kept
        assert "at" in tokens


class TestTFIDFBackend:
    def test_build_and_search(self):
        backend = TFIDFBackend()
        backend.build_index(FIXTURES)

        # Search for a concept
        results = backend.search("测试概念", FIXTURES, top_k=5)
        assert len(results) >= 1
        assert results[0]["score"] > 0
        assert results[0]["backend"] == "tfidf"

    def test_no_results_for_nonexistent_term(self):
        backend = TFIDFBackend()
        backend.build_index(FIXTURES)
        results = backend.search("xyzzy_nonexistent_12345", FIXTURES)
        assert len(results) == 0

    def test_backend_name(self):
        backend = TFIDFBackend()
        assert backend.name == "tfidf"
        assert backend.available

    def test_empty_wiki(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "empty"
            wiki.mkdir()
            backend = TFIDFBackend()
            backend.build_index(wiki)
            results = backend.search("anything", wiki)
            assert len(results) == 0

    def test_mark_dirty_rebuild(self):
        backend = TFIDFBackend()
        backend._dirty = True
        results = backend.search("测试", FIXTURES)
        assert len(results) >= 1


class TestHybridBackend:
    def test_single_backend(self):
        tfidf = TFIDFBackend()
        hybrid = HybridBackend(backends=[tfidf])
        results = hybrid.search("测试概念", FIXTURES, top_k=3)
        assert len(results) >= 1
        # Single backend passes through results directly
        assert results[0]["backend"] in ("tfidf", "hybrid")

    def test_multiple_backends_dedup(self):
        tfidf1 = TFIDFBackend()
        tfidf2 = TFIDFBackend()
        hybrid = HybridBackend(backends=[tfidf1, tfidf2], weights=[1.0, 1.0])
        results = hybrid.search("测试概念", FIXTURES, top_k=5)
        # Same backend twice should deduplicate via RRF
        assert len(results) >= 1

    def test_available_when_any_available(self):
        class UnavailableBackend(SearchBackend):
            @property
            def name(self): return "unavailable"
            @property
            def available(self): return False
            def search(self, q, w, k): return []

        hybrid = HybridBackend(backends=[UnavailableBackend(), TFIDFBackend()])
        assert hybrid.available


class TestFactory:
    def test_create_default(self):
        engine = create_search_engine(qmd_available=False)
        assert isinstance(engine, TFIDFBackend)
        assert engine.available
