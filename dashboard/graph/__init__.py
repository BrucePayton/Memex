"""
Memex Knowledge Graph Package.

Provides:
- builder: wikilink graph construction from wiki markdown files
- community: community detection (BFS connected components, Leiden clustering)
- paths: shortest path, neighbor queries, god nodes
- universe: cross-project knowledge universe (in server.py, pending extraction)
- insights: bridge detection, isolated pages (in server.py, pending extraction)
- export: HTML/JSON graph visualization (in server.py, pending extraction)
"""

from .builder import (
    build_wiki_data, build_graph_data, build_nx_graph,
    IncrementalGraphUpdater,
)
from .community import (
    detect_communities, detect_communities_bfs, detect_communities_enhanced,
)
from .paths import (
    shortest_path, path_with_content, neighbors, god_nodes,
)

__all__ = [
    # builder
    "build_wiki_data",
    "build_graph_data",
    "build_nx_graph",
    "IncrementalGraphUpdater",
    # community
    "detect_communities",
    "detect_communities_bfs",
    "detect_communities_enhanced",
    # paths
    "shortest_path",
    "path_with_content",
    "neighbors",
    "god_nodes",
]
