"""
qmd search adapter for Memex.

Wraps qmd (https://github.com/tobi/qmd) as a Memex SearchBackend.
qmd provides hybrid BM25+vector+RRF+LLM reranking search for markdown files.

Detection: checks for qmd CLI on PATH or qmd MCP server availability.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

# Import SearchBackend from dashboard if available
try:
    from dashboard.search.engine import SearchBackend
except ImportError:
    SearchBackend = object  # type: ignore


class QMDAdapter:
    """Adapter for qmd hybrid search.

    Can operate in two modes:
    1. CLI mode: `qmd query <terms>` (subprocess)
    2. MCP mode: via Claude Code MCP (future)

    The adapter handles qmd availability detection and index management.
    """

    def __init__(self, wiki_dir: Optional[Path] = None):
        self._available = None  # lazy detection
        self._cli_path = None
        self.wiki_dir = wiki_dir

    @property
    def available(self) -> bool:
        if self._available is None:
            self._available = self._detect()
        return self._available

    @property
    def cli_path(self) -> Optional[str]:
        if self._cli_path is None:
            self._cli_path = shutil.which("qmd")
        return self._cli_path

    def _detect(self) -> bool:
        """Check if qmd is available on this system."""
        return self.cli_path is not None

    def search(
        self,
        query: str,
        wiki_dir: Path,
        top_k: int = 10,
        min_score: float = 0.1,
    ) -> list[dict]:
        """Execute hybrid search via qmd CLI.

        Returns results in Memex SearchResult-compatible format.
        Falls back to empty list on any error.
        """
        if not self.available:
            return []

        try:
            result = subprocess.run(
                [
                    self.cli_path, "query", query,
                    "--max-results", str(top_k),
                    "--min-score", str(min_score),
                    "--json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(wiki_dir),
            )
            if result.returncode != 0:
                return []

            data = json.loads(result.stdout)
            return self._convert_results(data, top_k)
        except (subprocess.TimeoutExpired, json.JSONDecodeError,
                FileNotFoundError, OSError):
            return []

    def _convert_results(self, raw: dict, top_k: int) -> list[dict]:
        """Convert qmd JSON output to Memex SearchResult format."""
        results = []
        for item in raw.get("results", [])[:top_k]:
            path = item.get("path", item.get("file", ""))
            results.append({
                "page_path": path,
                "title": item.get("title", path),
                "snippet": item.get("snippet", item.get("text", ""))[:300],
                "score": round(item.get("score", 0), 4),
                "backend": "qmd",
                "page_type": item.get("type", "unknown"),
                "tags": item.get("tags", []),
            })
        return results

    def is_indexed(self, wiki_dir: Path) -> bool:
        """Check if qmd has already indexed this wiki directory."""
        cache_dir = Path.home() / ".cache" / "qmd"
        return cache_dir.exists()


# ─── QMD as Memex SearchBackend ───

class QMDSearchBackend(SearchBackend):
    """Memex SearchBackend wrapping qmd adapter.

    When qmd is unavailable, available=False triggers fallback to TF-IDF
    in HybridBackend.
    """

    def __init__(self, wiki_dir: Optional[Path] = None):
        self._adapter = QMDAdapter(wiki_dir)

    @property
    def name(self) -> str:
        return "qmd"

    @property
    def available(self) -> bool:
        return self._adapter.available

    def search(self, query: str, wiki_dir: Path, top_k: int = 10) -> list[dict]:
        return self._adapter.search(query, wiki_dir, top_k)


def detect_qmd() -> bool:
    """Quick check: is qmd CLI available?"""
    return shutil.which("qmd") is not None
