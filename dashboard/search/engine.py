"""
Pluggable search backends for Memex.

Provides:
- SearchBackend (ABC): interface for all search backends
- TFIDFBackend: built-in TF-IDF keyword search (stdlib, always available)
- QMDBackend: qmd hybrid search via MCP subprocess stub
- HybridBackend: multi-backend orchestrator with RRF fusion
- create_search_engine(): factory function with automatic backend selection
"""

import math
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Optional


# ─── ABC ───

class SearchBackend(ABC):
    """Interface for pluggable search backends."""

    @abstractmethod
    def search(self, query: str, wiki_dir: Path, top_k: int = 10) -> list[dict]:
        """Search wiki pages. Returns [{page_path, title, snippet, score, backend}]."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable backend name."""
        ...

    @property
    def available(self) -> bool:
        """Whether this backend is currently operational."""
        return True


# ─── TF-IDF Backend ───

class TFIDFBackend(SearchBackend):
    """Built-in TF-IDF keyword search. stdlib-only, always available.

    Tokenizes Korean (Hangul bigrams) and English (word boundaries).
    Falls back gracefully on unavailable dependencies.
    """

    def __init__(self):
        self._index: dict[str, dict[str, float]] = {}  # term -> {page: tfidf}
        self._pages: dict[str, dict] = {}  # page_path -> metadata
        self._dirty = True

    @property
    def name(self) -> str:
        return "tfidf"

    def build_index(self, wiki_dir: Path):
        """Build TF-IDF index from all wiki markdown files."""
        from ..models import parse_fm
        self._index.clear()
        self._pages.clear()

        if not wiki_dir.exists():
            return

        # Collect documents
        docs: dict[str, str] = {}  # page_path -> body text
        for md in wiki_dir.rglob("*.md"):
            rel = str(md.relative_to(wiki_dir))
            text = md.read_text(encoding="utf-8")
            meta, body = parse_fm(text)
            docs[rel] = body
            self._pages[rel] = {
                "path": rel,
                "title": meta.get("title", md.stem),
                "type": meta.get("type", "unknown"),
                "tags": meta.get("tags", []),
            }

        n_docs = len(docs)
        if n_docs == 0:
            return

        # Tokenize and compute TF
        doc_tokens: dict[str, dict[str, int]] = {}
        for path, body in docs.items():
            tokens = _tokenize(body)
            doc_tokens[path] = defaultdict(int)
            for t in tokens:
                doc_tokens[path][t] += 1

        # Compute IDF
        df: dict[str, int] = defaultdict(int)
        for tokens in doc_tokens.values():
            for term in tokens:
                df[term] += 1

        # Build index
        for path, tokens in doc_tokens.items():
            self._index[path] = {}
            for term, tf in tokens.items():
                idf = math.log((n_docs + 1) / (df[term] + 1)) + 1
                self._index[path][term] = tf * idf

        self._dirty = False

    def search(self, query: str, wiki_dir: Path, top_k: int = 10) -> list[dict]:
        if self._dirty:
            self.build_index(wiki_dir)

        query_terms = _tokenize(query)
        if not query_terms:
            return []

        # Score each page
        scores: dict[str, float] = {}
        for path, term_weights in self._index.items():
            score = sum(term_weights.get(t, 0) for t in query_terms)
            if score > 0:
                # Normalize by page length
                scores[path] = score / (math.sqrt(len(term_weights)) + 1)

        # Sort and return top-k
        ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
        results = []
        for path, score in ranked:
            info = self._pages.get(path, {})
            results.append({
                "page_path": path,
                "title": info.get("title", path),
                "snippet": info.get("snippet", ""),
                "score": round(score, 4),
                "backend": self.name,
                "page_type": info.get("type", "unknown"),
                "tags": info.get("tags", []),
            })
        return results


# ─── Hybrid Backend ───

class HybridBackend(SearchBackend):
    """Multi-backend orchestrator with Reciprocal Rank Fusion (RRF).

    Combines results from multiple backends (e.g., TF-IDF + qmd).
    Each backend can have a weight for score blending.
    """

    RRF_K = 60  # RRF smoothing constant

    def __init__(self, backends: list[SearchBackend] = None, weights: list[float] = None):
        self._backends = backends or []
        self._weights = weights or [1.0] * len(self._backends)

    @property
    def name(self) -> str:
        return "hybrid"

    @property
    def available(self) -> bool:
        return any(b.available for b in self._backends)

    def add_backend(self, backend: SearchBackend, weight: float = 1.0):
        self._backends.append(backend)
        self._weights.append(weight)

    def search(self, query: str, wiki_dir: Path, top_k: int = 10) -> list[dict]:
        """Run all backends and fuse results via RRF."""
        all_results: list[list[dict]] = []
        for backend in self._backends:
            if backend.available:
                try:
                    results = backend.search(query, wiki_dir, top_k * 2)
                    all_results.append(results)
                except Exception:
                    continue

        if not all_results:
            return []

        if len(all_results) == 1:
            return all_results[0][:top_k]

        # RRF fusion
        fused: dict[str, float] = {}
        meta: dict[str, dict] = {}
        for backend_idx, results in enumerate(all_results):
            weight = self._weights[backend_idx] if backend_idx < len(self._weights) else 1.0
            for rank, r in enumerate(results):
                path = r["page_path"]
                rrf_score = weight / (self.RRF_K + rank + 1)
                fused[path] = fused.get(path, 0) + rrf_score
                meta[path] = r

        ranked = sorted(fused.items(), key=lambda x: -x[1])[:top_k]
        return [
            {**meta.get(path, {}),
             "page_path": path, "score": round(score, 4), "backend": self.name}
            for path, score in ranked
        ]


# ─── Factory ───

def create_search_engine(qmd_available: bool = False) -> SearchBackend:
    """Create search engine with automatic backend selection.

    Priority: Hybrid(qmd + TF-IDF) > TF-IDF alone.
    Auto-detects qmd CLI on PATH if qmd_available not explicitly set.
    """
    tfidf = TFIDFBackend()

    # Auto-detect qmd
    if not qmd_available:
        import shutil
        qmd_available = shutil.which("qmd") is not None

    if qmd_available:
        try:
            from mcp_server.adapters.search import QMDSearchBackend
            qmd = QMDSearchBackend()
            if qmd.available:
                return HybridBackend(backends=[qmd, tfidf], weights=[2.0, 1.0])
        except ImportError:
            pass

    return tfidf


# ─── Tokenizer ───

def _tokenize(text: str) -> list[str]:
    """Tokenize text for TF-IDF indexing.

    Handles:
    - Korean: character bigrams (effective for Hangul without KoNLPy)
    - CJK: single characters
    - English: word boundaries (2+ alphanumeric chars)
    """
    tokens = []
    text = text.lower()

    # English words (2+ chars)
    for m in re.finditer(r"[a-z0-9]{2,}", text):
        tokens.append(m.group())

    # Korean/CJK: bigrams for contiguous Unicode blocks
    korean_run = []
    for ch in text:
        if "一" <= ch <= "鿿":
            korean_run.append(ch)
        else:
            if len(korean_run) >= 2:
                for i in range(len(korean_run) - 1):
                    tokens.append(korean_run[i] + korean_run[i + 1])
            elif korean_run:
                tokens.append(korean_run[0])
            korean_run = []
    # Flush remaining
    if len(korean_run) >= 2:
        for i in range(len(korean_run) - 1):
            tokens.append(korean_run[i] + korean_run[i + 1])
    elif korean_run:
        tokens.append(korean_run[0])

    return tokens
