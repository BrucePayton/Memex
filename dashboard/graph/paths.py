"""
Shortest path, neighbor, and path-with-content queries for Memex knowledge graph.
"""

from collections import deque
from pathlib import Path
from typing import Optional

from .builder import build_graph_data
from dashboard.models import SYSTEM_PAGES


def shortest_path(
    wiki_dir: Path,
    source: str,
    target: str,
    raw_dir: Optional[Path] = None,
) -> dict:
    """BFS shortest path between two wiki pages.

    source/target can be filenames or page titles (case-insensitive).
    Returns {ok, path: [filenames], hops: int, edges: [{from, to}]}
    """
    nodes, edges, node_map = build_graph_data(wiki_dir, raw_dir)

    # Build lookup: filename → filename, title → filename
    node_lookup: dict[str, str] = {}
    for n in nodes:
        node_lookup[n["filename"].lower()] = n["filename"]
        node_lookup[n["title"].lower()] = n["filename"]

    src_id = node_lookup.get(source.lower())
    tgt_id = node_lookup.get(target.lower())
    if not src_id:
        return {"ok": False, "error": f"source node not found: {source}"}
    if not tgt_id:
        return {"ok": False, "error": f"target node not found: {target}"}
    if src_id == tgt_id:
        return {"ok": True, "path": [src_id], "hops": 0, "edges": []}

    # Build adjacency
    adj: dict[str, list[str]] = {n["filename"]: [] for n in nodes}
    for e in edges:
        if e["from"] in adj and e["to"] in adj:
            adj[e["from"]].append(e["to"])
            adj[e["to"]].append(e["from"])

    # BFS
    visited: dict[str, Optional[str]] = {src_id: None}
    queue = deque([src_id])
    while queue:
        u = queue.popleft()
        if u == tgt_id:
            break
        for v in adj[u]:
            if v not in visited:
                visited[v] = u
                queue.append(v)

    if tgt_id not in visited:
        return {"ok": False, "error": f"no path between '{source}' and '{target}'"}

    # Reconstruct path
    path = []
    cur = tgt_id
    while cur is not None:
        path.append(cur)
        cur = visited[cur]
    path.reverse()

    path_edges = []
    for i in range(len(path) - 1):
        path_edges.append({"from": path[i], "to": path[i + 1]})

    return {"ok": True, "path": path, "hops": len(path) - 1, "edges": path_edges}


def path_with_content(
    wiki_dir: Path,
    source: str,
    target: str,
) -> dict:
    """Shortest path with full content of each page along the path."""
    result = shortest_path(wiki_dir, source, target)
    if not result["ok"]:
        return result

    content = []
    for filename in result["path"]:
        md = wiki_dir / filename
        if md.exists():
            text = md.read_text(encoding="utf-8")
            from ...models import parse_fm
            meta, body = parse_fm(text)
            content.append({
                "filename": filename,
                "title": meta.get("title", md.stem),
                "type": meta.get("type", "unknown"),
                "snippet": body[:500],
                "word_count": len(body.split()),
            })
        else:
            content.append({
                "filename": filename, "title": filename,
                "type": "missing", "snippet": "", "word_count": 0,
            })

    result["content"] = content
    return result


def neighbors(
    wiki_dir: Path,
    node_id: str,
    raw_dir: Optional[Path] = None,
) -> dict:
    """Return direct neighbors of a wiki page node.

    node_id can be a filename or page title.
    """
    nodes, edges, node_map = build_graph_data(wiki_dir, raw_dir)

    # Resolve node_id
    node_lookup: dict[str, str] = {}
    for n in nodes:
        node_lookup[n["filename"].lower()] = n["filename"]
        node_lookup[n["title"].lower()] = n["filename"]

    resolved = node_lookup.get(node_id.lower())
    if not resolved:
        return {"ok": False, "error": f"node not found: {node_id}"}

    # Find neighbors
    neighbor_ids: set[str] = set()
    for e in edges:
        if e["from"] == resolved:
            neighbor_ids.add(e["to"])
        if e["to"] == resolved:
            neighbor_ids.add(e["from"])

    neighbor_list = []
    for nid in sorted(neighbor_ids):
        n = node_map.get(nid)
        neighbor_list.append({
            "id": nid,
            "label": n["title"] if n else nid,
            "type": n.get("type", "unknown") if n else "unknown",
        })

    return {"ok": True, "node": resolved, "neighbors": neighbor_list, "degree": len(neighbor_list)}


def step_dependency_path(
    wiki_dir: Path,
    step_name: str = "",
) -> dict:
    """Return the dependency chain for a given process step.

    Follows upstream_steps and downstream_steps declared in
    wiki/steps/*/index.md frontmatter to build the full chain.

    Returns {ok, step, chain: [step_ids], upstream: [...], downstream: [...]}
    """
    nodes, edges, _ = build_graph_data(wiki_dir)

    # Find all step nodes
    step_nodes = {
        n["filename"]: n
        for n in nodes
        if n.get("type") == "process-step"
    }

    if not step_nodes:
        return {"ok": False, "error": "no process-step nodes found in graph"}

    # Build adjacency from dependency edges
    upstream_of: dict[str, list[str]] = {}
    downstream_of: dict[str, list[str]] = {}
    for e in edges:
        kind = e.get("kind", "")
        if kind == "depends_on":
            downstream_of.setdefault(e["from"], []).append(e["to"])
            upstream_of.setdefault(e["to"], []).append(e["from"])
        elif kind == "precedes":
            downstream_of.setdefault(e["from"], []).append(e["to"])
            upstream_of.setdefault(e["to"], []).append(e["from"])

    # Resolve target step
    target_id = None
    search = step_name.lower().strip()
    for sid, sn in step_nodes.items():
        if search in sid.lower() or search in sn.get("label", "").lower():
            target_id = sid
            break

    if not target_id and step_nodes:
        # Return all steps if no specific step requested
        step_list = [
            {"id": sid, "label": sn.get("label", sid), "type": "process-step"}
            for sid, sn in sorted(step_nodes.items())
        ]
        return {
            "ok": True,
            "step": None,
            "chain": [s["id"] for s in step_list],
            "upstream": [],
            "downstream": [],
            "all_steps": step_list,
        }

    if not target_id:
        return {"ok": False, "error": f"step not found: {step_name}"}

    # Walk upstream
    upstream_chain = []
    visited = set()
    queue = deque([target_id])
    while queue:
        cur = queue.popleft()
        if cur in visited:
            continue
        visited.add(cur)
        for up in upstream_of.get(cur, []):
            if up not in visited:
                upstream_chain.append(up)
                queue.append(up)

    # Walk downstream
    downstream_chain = []
    visited.add(target_id)
    queue = deque([target_id])
    while queue:
        cur = queue.popleft()
        for down in downstream_of.get(cur, []):
            if down not in visited:
                visited.add(down)
                downstream_chain.append(down)
                queue.append(down)

    chain = upstream_chain[::-1] + [target_id] + downstream_chain

    return {
        "ok": True,
        "step": target_id,
        "chain": chain,
        "upstream": upstream_chain,
        "downstream": downstream_chain,
    }


def god_nodes(
    wiki_dir: Path,
    top_n: int = 10,
    raw_dir: Optional[Path] = None,
) -> dict:
    """Return most-connected wiki pages (highest degree), excluding system pages."""
    nodes, edges, node_map = build_graph_data(wiki_dir, raw_dir)
    sys_pages = SYSTEM_PAGES

    degree = {n["filename"]: 0 for n in nodes if n["filename"] not in sys_pages}
    for e in edges:
        if e["from"] in degree:
            degree[e["from"]] += 1
        if e["to"] in degree:
            degree[e["to"]] += 1

    sorted_nodes = sorted(degree.items(), key=lambda x: -x[1])
    result = []
    for nid, deg in sorted_nodes[:top_n]:
        n = node_map.get(nid)
        result.append({
            "id": nid,
            "label": n["title"] if n else nid,
            "degree": deg,
            "type": n.get("type", "unknown") if n else "unknown",
        })
    return {"god_nodes": result}
