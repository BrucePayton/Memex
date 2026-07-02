"""
Unit tests for dashboard/graph/builder.py — graph construction from wiki files.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.graph.builder import build_wiki_data, build_graph_data


FIXTURES = Path(__file__).parent.parent / "fixtures" / "sample_wiki"


class TestGraphBuilder:
    def test_build_wiki_data(self):
        data = build_wiki_data(FIXTURES)
        pages = data["pages"]
        graph = data["graph"]
        stats = data["stats"]

        # Should find 3 content pages (excluding index.md)
        assert len(pages) >= 3
        assert stats["total_pages"] >= 3
        assert "concept" in str(stats["type_counts"])
        assert "entity" in str(stats["type_counts"])

        # Graph should have nodes and edges
        assert len(graph["nodes"]) >= 3
        assert len(graph["edges"]) >= 2  # test-concept -> test-entity, test-concept -> source

    def test_node_types(self):
        data = build_wiki_data(FIXTURES)
        types = {n["type"] for n in data["graph"]["nodes"]}
        assert "concept" in types or any(
            n["label"] == "测试概念页面" for n in data["graph"]["nodes"]
        )

    def test_edge_resolution(self):
        """Wikilinks should be resolved to proper filenames."""
        data = build_wiki_data(FIXTURES)
        edges = data["graph"]["edges"]
        # Find edge from test-concept
        concept_edges = [e for e in edges if "test-concept" in e["from"]]
        assert len(concept_edges) >= 1

    def test_build_graph_data(self):
        nodes, edges, node_map = build_graph_data(FIXTURES)
        assert len(nodes) >= 3
        assert len(edges) >= 2
        assert len(node_map) >= 3
        # All filenames should be in node_map
        for n in nodes:
            assert n["filename"] in node_map

    def test_empty_wiki_dir(self):
        data = build_wiki_data(Path("/nonexistent/wiki/path"))
        assert data["pages"] == []
        assert data["graph"]["nodes"] == []
        assert data["stats"]["total_pages"] == 0

    def test_stub_nodes_for_unresolved_links(self):
        """When a wikilink target doesn't exist, a stub/missing node should be created."""
        # Create a temp wiki with a broken link
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            page = tmp_path / "test.md"
            page.write_text("---\ntitle: Test\ntype: concept\n---\nLink: [[missing-page]]")
            data = build_wiki_data(tmp_path)
            node_ids = {n["id"] for n in data["graph"]["nodes"]}
            # Should have the real page + a stub/missing node
            assert len(data["graph"]["nodes"]) == 2
