#!/usr/bin/env python3
"""Regression tests for /api/wiki graph generation."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))

import server  # noqa: E402


class _DummyProject:
    def __init__(self, slug: str, wiki_dir: Path, raw_dir: Path):
        self.slug = slug
        self.wiki_dir = wiki_dir
        self.raw_dir = raw_dir


class TestWikiGraphRegression(unittest.TestCase):
    def test_missing_link_with_anchor_builds_stub_node(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            wiki_dir = base / "wiki"
            raw_dir = base / "raw"
            wiki_dir.mkdir()
            raw_dir.mkdir()
            (wiki_dir / "index.md").write_text(
                "---\n"
                "type: overview\n"
                "---\n\n"
                "See [[ghost-page#section-1]].\n",
                encoding="utf-8",
            )
            proj = _DummyProject("tmp", wiki_dir, raw_dir)
            old_resolve = server._resolve_project
            server._resolve_project = lambda _slug=None: proj
            try:
                out = server.build_wiki_data(project_slug="tmp", ui_lang="en")
            finally:
                server._resolve_project = old_resolve

        self.assertEqual(out["project"], "tmp")
        missing_nodes = [n for n in out["graph"]["nodes"] if n.get("type") == "missing"]
        self.assertEqual(len(missing_nodes), 1)
        self.assertEqual(missing_nodes[0]["id"], "ghost-page.md")
        self.assertEqual(missing_nodes[0]["label"], "Ghost Page")


if __name__ == "__main__":
    unittest.main()
