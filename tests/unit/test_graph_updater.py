"""
Unit tests for IncrementalGraphUpdater — mtime-based incremental graph updates.
"""

import pytest
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.graph.builder import (
    build_wiki_data, IncrementalGraphUpdater,
)


FIXTURES = Path(__file__).parent.parent / "fixtures" / "sample_wiki"


class TestIncrementalGraphUpdater:
    def test_force_rebuild(self):
        """Full rebuild should produce valid graph data."""
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp) / ".graph"
            updater = IncrementalGraphUpdater(FIXTURES, cache_dir)

            # Should auto-build on init
            assert len(updater.nodes) >= 3
            assert len(updater.edges) >= 2
            assert any(n["type"] == "concept" for n in updater.nodes)

    def test_mark_dirty_and_flush(self):
        """Marking a page dirty should trigger incremental update."""
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = Path(tmp) / "wiki"
            wiki_dir.mkdir()
            # Create a wiki page
            page = wiki_dir / "test.md"
            page.write_text(
                "---\ntitle: Test\ntype: concept\ntags: [a]\n---\nContent [[other-page]]"
            )

            cache_dir = Path(tmp) / ".graph"
            updater = IncrementalGraphUpdater(wiki_dir, cache_dir)
            # "other-page" wikilink creates a stub node, so we have 2 nodes
            assert len(updater.nodes) == 2

            # Modify the page
            time.sleep(0.01)  # ensure mtime changes
            page.write_text(
                "---\ntitle: Updated\ntype: concept\ntags: [a, b]\n---\nNew content [[other-page]] [[third-page]]"
            )

            updater.mark_dirty("test.md")
            updater.flush()

            # Find the updated node
            node = [n for n in updater.nodes if n["id"] == "test.md"][0]
            assert node["label"] == "Updated"
            assert "b" in node["tags"]

    def test_add_and_remove_node(self):
        """Adding then removing a page should update graph correctly."""
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = Path(tmp) / "wiki"
            wiki_dir.mkdir()
            page_a = wiki_dir / "a.md"
            page_a.write_text("---\ntitle: A\ntype: concept\n---\nContent")
            page_b = wiki_dir / "b.md"
            page_b.write_text("---\ntitle: B\ntype: entity\n---\nSee [[a]]")

            cache_dir = Path(tmp) / ".graph"
            updater = IncrementalGraphUpdater(wiki_dir, cache_dir)
            assert len(updater.nodes) == 2

            # Remove b.md
            page_b.unlink()
            updater.mark_dirty("b.md")
            updater.flush()
            assert len(updater.nodes) == 1
            assert all(n["id"] != "b.md" for n in updater.nodes)

    def test_stub_node_for_unresolved_link(self):
        """Unresolved wikilinks should create stub/missing nodes."""
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = Path(tmp) / "wiki"
            wiki_dir.mkdir()
            page = wiki_dir / "main.md"
            page.write_text("---\ntitle: Main\ntype: concept\n---\nLink to [[nonexistent]]")

            cache_dir = Path(tmp) / ".graph"
            updater = IncrementalGraphUpdater(wiki_dir, cache_dir)

            # Should have main + stub for nonexistent
            node_ids = {n["id"] for n in updater.nodes}
            assert "nonexistent.md" in node_ids
            stub = [n for n in updater.nodes if n["id"] == "nonexistent.md"][0]
            assert stub["type"] == "missing"

    def test_edge_resolution_after_update(self):
        """Edges should be properly resolved after node update."""
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = Path(tmp) / "wiki"
            wiki_dir.mkdir(parents=True)
            (wiki_dir / "concepts").mkdir()

            page_a = wiki_dir / "concepts" / "alpha.md"
            page_a.write_text("---\ntitle: Alpha\ntype: concept\n---\nSee [[beta]]")

            page_b = wiki_dir / "concepts" / "beta.md"
            page_b.write_text("---\ntitle: Beta\ntype: concept\n---\nRelated to [[alpha]]")

            cache_dir = Path(tmp) / ".graph"
            updater = IncrementalGraphUpdater(wiki_dir, cache_dir)
            assert len(updater.nodes) == 2
            assert len(updater.edges) >= 2

            # Verify edges point to correct resolved paths
            for e in updater.edges:
                assert e["to"].endswith(".md")
                assert e["from"].endswith(".md")

    def test_empty_wiki_dir(self):
        """Empty wiki dir should produce empty graph."""
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = Path(tmp) / "wiki"
            wiki_dir.mkdir()
            cache_dir = Path(tmp) / ".graph"
            updater = IncrementalGraphUpdater(wiki_dir, cache_dir)
            assert len(updater.nodes) == 0
            assert len(updater.edges) == 0

    def test_cache_persistence(self):
        """Mtime cache should be persisted across updater instances."""
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = Path(tmp) / "wiki"
            wiki_dir.mkdir()
            (wiki_dir / "page.md").write_text(
                "---\ntitle: P\ntype: concept\n---\nContent"
            )
            cache_dir = Path(tmp) / ".graph"

            # First instance — builds graph and caches mtime
            u1 = IncrementalGraphUpdater(wiki_dir, cache_dir)
            snapshot = u1._load_snapshot()
            assert len(snapshot) == 1

            # Second instance — rebuilds from wiki (cache exists but snapshot may be stale)
            u2 = IncrementalGraphUpdater(wiki_dir, cache_dir)
            assert len(u2.nodes) == 1
            assert u2.nodes[0]["label"] == "P"
