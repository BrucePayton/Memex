"""
Community detection for Memex knowledge graph.

Provides BFS connected components with greedy splitting for large communities,
plus optional graphify-enhanced Leiden clustering.
"""

from collections import deque
from pathlib import Path
from typing import Optional

from .builder import build_graph_data, build_nx_graph


def detect_communities_bfs(
    wiki_dir: Path,
    raw_dir: Optional[Path] = None,
) -> dict:
    """BFS connected components with greedy splitting for communities > 10 nodes.

    Returns {communities: {id: [filenames]}, cohesion: {id: score}, community_count: int}
    """
    nodes, edges, node_map = build_graph_data(wiki_dir, raw_dir)
    node_ids = [n["filename"] for n in nodes]
    id_idx = {nid: i for i, nid in enumerate(node_ids)}
    n = len(node_ids)

    # Build adjacency
    adj = [set() for _ in range(n)]
    for e in edges:
        if e["from"] in id_idx and e["to"] in id_idx:
            u, v = id_idx[e["from"]], id_idx[e["to"]]
            adj[u].add(v)
            adj[v].add(u)

    # BFS connected components
    visited = [False] * n
    components = []
    for start in range(n):
        if visited[start]:
            continue
        comp = []
        queue = deque([start])
        visited[start] = True
        while queue:
            u = queue.popleft()
            comp.append(node_ids[u])
            for v in adj[u]:
                if not visited[v]:
                    visited[v] = True
                    queue.append(v)
        components.append(comp)

    # Split large components (>10 nodes) greedily
    final_components = []
    for comp in components:
        if len(comp) <= 10:
            final_components.append(comp)
        else:
            sub = _split_large_component(comp, edges)
            final_components.extend(sub)

    final_components.sort(key=len, reverse=True)
    cohesion = {
        str(i): _cohesion_score(c, edges) for i, c in enumerate(final_components)
    }

    return {
        "communities": {str(i): c for i, c in enumerate(final_components)},
        "cohesion": cohesion,
        "community_count": len(final_components),
    }


def detect_communities_enhanced(wiki_dir: Path) -> dict:
    """Leiden algorithm via graphify (optional). Falls back to BFS on failure."""
    try:
        from graphify.cluster import cluster
    except ImportError:
        return detect_communities_bfs(wiki_dir)

    G, node_map = build_nx_graph(wiki_dir)
    try:
        comms_raw = cluster(G)
    except Exception:
        return detect_communities_bfs(wiki_dir)

    nodes, edges, _ = build_graph_data(wiki_dir)
    final_comms = sorted(comms_raw.values(), key=len, reverse=True)
    cohesion = {
        str(i): _cohesion_score(c, edges) for i, c in enumerate(final_comms)
    }
    return {
        "communities": {str(i): c for i, c in enumerate(final_comms)},
        "cohesion": cohesion,
        "community_count": len(final_comms),
    }


def detect_communities(
    wiki_dir: Path,
    use_enhanced: bool = False,
) -> dict:
    """Community detection router."""
    if use_enhanced:
        return detect_communities_enhanced(wiki_dir)
    return detect_communities_bfs(wiki_dir)


# ─── Helpers ───

def _cohesion_score(node_ids: list[str], edges: list[dict]) -> float:
    """Compute internal edge density for a set of nodes."""
    nc = len(node_ids)
    if nc <= 1:
        return 1.0
    comp_set = set(node_ids)
    actual = sum(1 for e in edges if e["from"] in comp_set and e["to"] in comp_set)
    possible = nc * (nc - 1) / 2
    return round(actual / possible, 2) if possible > 0 else 0.0


def _split_large_component(comp: list[str], edges: list[dict]) -> list[list[str]]:
    """Greedily split a component > 10 nodes into sub-communities."""
    comp_set = set(comp)
    comp_idx = {nid: i for i, nid in enumerate(comp)}
    comp_adj = [set() for _ in range(len(comp))]
    for e in edges:
        if e["from"] in comp_idx and e["to"] in comp_idx:
            u, v = comp_idx[e["from"]], comp_idx[e["to"]]
            comp_adj[u].add(v)
            comp_adj[v].add(u)
    # Pick top-2 highest-degree nodes as seeds
    degrees = sorted(range(len(comp)), key=lambda i: len(comp_adj[i]), reverse=True)
    seeds = degrees[:min(2, len(degrees))]
    clusters = [[] for _ in seeds]
    for i in range(len(comp)):
        if i in seeds:
            continue
        best = max(
            range(len(seeds)),
            key=lambda si: len(comp_adj[i] & comp_adj[seeds[si]]),
            default=0,
        )
        clusters[best].append(comp[i])
    for si, seed in enumerate(seeds):
        clusters[si].append(comp[seed])
    return [c for c in clusters if c]
