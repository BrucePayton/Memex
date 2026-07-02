"""
Graph builder: wikilink graph construction from wiki markdown files.

Single source of truth shared by dashboard/server.py and mcp-server/memex_mcp.py.
Supports both full rebuild and incremental (mtime-based) update modes.
"""

import json
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

from ..models import (
    WikiPage, GraphNode, GraphEdge,
    parse_fm, extract_links, extract_citations,
    make_slug, is_system_page, LOG_ENTRY_RE, SYSTEM_PAGES,
    display_title,
)


# ─── Full graph build ───

def build_wiki_data(
    wiki_dir: Path,
    raw_dir: Optional[Path] = None,
    project_slug: str = "",
    ui_lang: Optional[str] = None,
) -> dict:
    """Full wiki data build: pages, graph (nodes+edges), log, stats.

    Returns {
        project: project_slug (if provided),
        pages: [{filename, folder, title, type, created, updated, tags,
                 sources, links, word_count, content, status, confidence}],
        graph: {nodes: [{id, label, type}], edges: [{from, to}]},
        log: [{date, action, title}],
        stats: {total_pages, raw_sources, type_counts, total_links, last_updated}
    }
    """
    pages, nodes, edges = [], [], []
    type_counts = {}
    node_ids = set()

    if not wiki_dir.exists():
        return _empty_result(raw_dir or Path('.'))

    basename_candidates = defaultdict(list)
    filename_to_title = {}

    for md in sorted(wiki_dir.rglob("*.md")):
        rel = md.relative_to(wiki_dir)
        filename = str(rel)
        text = md.read_text(encoding="utf-8")
        meta, body = parse_fm(text)
        links = extract_links(body)
        citations = extract_citations(body)
        pt = meta.get("type", "unknown")
        type_counts[pt] = type_counts.get(pt, 0) + 1
        folder = str(rel.parent) if rel.parent != Path(".") else ""

        pages.append({
            "filename": filename, "folder": folder,
            "title": display_title(meta, md.stem, ui_lang),
            "type": pt,
            "created": meta.get("created", ""),
            "updated": meta.get("last_updated", ""),
            "tags": meta.get("tags", []),
            "sources": meta.get("sources", []),
            "links": links,
            "citations": citations,
            "word_count": len(body.split()),
            "content": body.strip(),
            "status": meta.get("status", "active"),
            "confidence": meta.get("confidence", ""),
        })
        node_ids.add(filename)
        nodes.append({"id": filename, "label": pages[-1]["title"], "type": pt})

        # Build basename lookup for collision resolution
        fn = os.path.basename(filename)
        stem = filename.replace('.md', '')
        basename_candidates[fn].append(filename)
        basename_candidates[stem].append(filename)
        filename_to_title[filename] = pages[-1]["title"]

        for lnk in links:
            edges.append({"from": filename, "to": lnk})

    # Resolve edge targets (handle basename collisions)
    for e in edges:
        target = e["to"]
        source_title = filename_to_title.get(e["from"], "")
        resolved = _resolve_target(target, node_ids, basename_candidates, filename_to_title, source_title)
        if resolved:
            e["to"] = resolved
        elif target not in node_ids and target.split("#", 1)[0] not in node_ids:
            stub_label = os.path.basename(target).replace(".md", "").replace("-", " ").title()
            nodes.append({"id": target, "label": stub_label, "type": "missing"})
            node_ids.add(target)

    # ─── Process step graph: scan wiki/steps/*/index.md ───
    steps_dir = wiki_dir / "steps"
    if steps_dir.is_dir():
        for step_index in sorted(steps_dir.glob("*/index.md")):
            step_name = step_index.parent.name
            try:
                step_text = step_index.read_text(encoding="utf-8")
                step_meta, _step_body = parse_fm(step_text)
                if step_meta.get("type") == "process-step":
                    step_id = f"steps/{step_name}/index.md"
                    if step_id not in node_ids:
                        nodes.append({
                            "id": step_id,
                            "label": step_meta.get("title", step_name),
                            "type": "process-step",
                        })
                        node_ids.add(step_id)
                    # upstream → depends_on edges (upstream → this)
                    for up in step_meta.get("upstream_steps", []) or []:
                        up_id = f"steps/{up}/index.md"
                        edges.append({"from": up_id, "to": step_id, "kind": "depends_on"})
                    # downstream → precedes edges (this → downstream)
                    for down in step_meta.get("downstream_steps", []) or []:
                        down_id = f"steps/{down}/index.md"
                        edges.append({"from": step_id, "to": down_id, "kind": "precedes"})
            except Exception:
                pass  # skip unparseable step files

    # Log entries
    log_entries = []
    lf = wiki_dir / "log.md"
    if lf.exists():
        _, lb = parse_fm(lf.read_text("utf-8"))
        log_entries = [
            {"date": m.group(1), "action": m.group(2), "title": m.group(3)}
            for m in LOG_ENTRY_RE.finditer(lb)
        ]

    raw_count = 0
    if raw_dir and raw_dir.exists():
        raw_count = sum(
            1 for f in raw_dir.rglob("*")
            if f.is_file() and not f.name.startswith(".") and "assets" not in f.parts
        )

    from datetime import datetime
    result = {
        "pages": pages,
        "graph": {"nodes": nodes, "edges": edges},
        "log": log_entries,
        "stats": {
            "total_pages": len(pages),
            "raw_sources": raw_count,
            "type_counts": type_counts,
            "total_links": len(edges),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        },
    }
    if project_slug:
        result["project"] = project_slug
    return result


def build_graph_data(wiki_dir: Path, raw_dir: Optional[Path] = None) -> tuple[list, list, dict]:
    """Build {nodes, edges} from wiki pages. Returns (nodes, edges, node_map)."""
    data = build_wiki_data(wiki_dir, raw_dir)
    nodes = []
    edges_list = []
    node_map = {}

    for n in data["graph"]["nodes"]:
        fn = n["id"]
        pg = next((p for p in data["pages"] if p["filename"] == fn), None)
        if pg:
            node_entry = dict(pg)
        else:
            stem = os.path.basename(fn).replace(".md", "").replace("-", " ").title()
            node_entry = {
                "filename": fn, "folder": "", "title": stem,
                "type": n.get("type", "missing"),
                "created": "", "updated": "", "tags": [], "sources": [],
                "links": [], "word_count": 0, "content": "",
            }
        nodes.append(node_entry)
        node_map[fn] = node_entry

    for e in data["graph"]["edges"]:
        edges_list.append({"from": e["from"], "to": e["to"]})

    return nodes, edges_list, node_map


def build_nx_graph(wiki_dir: Path):
    """Build networkx.Graph from wiki pages. Optional dependency."""
    import networkx as nx  # type: ignore

    nodes, edges, node_map = build_graph_data(wiki_dir)
    sys_pages = SYSTEM_PAGES
    G = nx.Graph()
    for n in nodes:
        fn = n["filename"]
        if fn not in sys_pages:
            G.add_node(
                fn, label=n["title"], type=n.get("type", "unknown"),
                word_count=n.get("word_count", 0), tags=n.get("tags", []),
            )
    for e in edges:
        src, tgt = e["from"], e["to"]
        if src in G and tgt in G:
            G.add_edge(src, tgt)
    return G, node_map


# ─── Incremental graph update (T24, inspired by MiroFish mtime tracking) ───

class IncrementalGraphUpdater:
    """Incremental graph updater using mtime snapshot comparison.

    Inspired by MiroFish's file position tracking + batch accumulation.
    Accumulates dirty pages and flushes in batches (5 pages or 30s timeout).

    Maintains an in-memory graph state that is incrementally updated,
    avoiding full rebuilds on every ingest.
    """

    BATCH_SIZE = 5
    FLUSH_TIMEOUT = 30  # seconds

    def __init__(self, wiki_dir: Path, cache_dir: Path):
        self.wiki_dir = wiki_dir
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_file = cache_dir / "mtime_snapshot.json"
        self._pending: list[str] = []
        self._last_flush = time.time()

        # In-memory graph state (incrementally maintained)
        self._nodes: dict[str, dict] = {}   # filename -> node dict
        self._edges: list[dict] = []         # [{from, to}]
        self._node_ids: set[str] = set()
        self._basename_candidates: dict[str, list[str]] = {}
        self._filename_to_title: dict[str, str] = {}

        # Initialize from cache or full rebuild
        snapshot = self._load_snapshot()
        if not snapshot or not self.wiki_dir.exists():
            self.force_rebuild()
        else:
            current = self._scan_wiki()
            if current != snapshot:
                self.force_rebuild()
            else:
                # Wiki unchanged — try loading persisted graph state
                if not self._try_load_state():
                    self.force_rebuild()

    @property
    def nodes(self) -> list[dict]:
        return list(self._nodes.values())

    @property
    def edges(self) -> list[dict]:
        return list(self._edges)

    @property
    def node_map(self) -> dict[str, dict]:
        return dict(self._nodes)

    def mark_dirty(self, page_path: str):
        """Mark a page as needing graph update. Auto-flushes at threshold."""
        self._pending.append(page_path)
        if len(self._pending) >= self.BATCH_SIZE or \
           time.time() - self._last_flush > self.FLUSH_TIMEOUT:
            self.flush()

    def flush(self):
        """Batch update graph: diff mtime snapshots, update only changed nodes/edges."""
        if not self._pending:
            return

        old = self._load_snapshot()
        new = self._scan_wiki()

        changed = {p for p in self._pending if p in old and p in new}
        added = {p for p in new if p not in old}
        deleted = {p for p in old if p not in new}

        for path in changed:
            self._update_node(path)
        for path in added:
            self._add_node(path)
        for path in deleted:
            self._remove_node(path)

        self._save_snapshot(new)
        self._save_state()
        self._pending.clear()
        self._last_flush = time.time()

    def force_rebuild(self) -> dict:
        """Full rebuild from disk. Returns complete graph data."""
        data = build_wiki_data(self.wiki_dir)
        self._rebuild_from_data(data)
        if self.wiki_dir.exists():
            self._scan_wiki_and_save()
        self._save_state()
        return data

    # ─── Internal: node/edge manipulation ───

    def _update_node(self, path: str):
        """Re-parse a changed page: update node metadata + replace outbound edges."""
        md = self.wiki_dir / path
        if not md.exists():
            return
        text = md.read_text(encoding="utf-8")
        meta, body = parse_fm(text)
        links = extract_links(body)
        citations = extract_citations(body)
        pt = meta.get("type", "unknown")

        # Remove old outbound edges from this node
        self._edges = [e for e in self._edges if e["from"] != path]

        # Update node metadata
        self._nodes[path] = {
            "id": path,
            "label": meta.get("title", md.stem.replace("-", " ").title()),
            "type": pt,
            "word_count": len(body.split()),
            "tags": meta.get("tags", []),
            "status": meta.get("status", "active"),
            "confidence": meta.get("confidence", ""),
        }

        # Add new edges
        for lnk in links:
            self._edges.append({"from": path, "to": lnk})

        # Resolve new edges
        self._resolve_edges()

    def _add_node(self, path: str):
        """Add a new node with edges for a newly created page."""
        self._update_node(path)

    def _remove_node(self, path: str):
        """Remove a node and all its connected edges."""
        self._nodes.pop(path, None)
        self._node_ids.discard(path)
        self._edges = [e for e in self._edges
                       if e["from"] != path and e["to"] != path]

    def _resolve_edges(self):
        """Resolve edge targets using basename lookup. Creates stub nodes for
        unresolved targets (preserving non-existent references in the graph)."""
        # Rebuild index after changes
        self._rebuild_basename_index()

        for e in self._edges:
            target = e["to"]
            resolved = _resolve_target(
                target, self._node_ids,
                self._basename_candidates,
                self._filename_to_title,
                self._filename_to_title.get(e["from"], ""),
            )
            if resolved:
                e["to"] = resolved
            elif target not in self._node_ids and target.split("#", 1)[0] not in self._node_ids:
                stub_label = os.path.basename(target).replace(".md", "").replace("-", " ").title()
                self._nodes[target] = {
                    "id": target, "label": stub_label, "type": "missing",
                    "word_count": 0, "tags": [], "status": "missing",
                    "confidence": "",
                }
                self._node_ids.add(target)

    def _rebuild_basename_index(self):
        """Rebuild basename collision lookup for edge resolution."""
        self._basename_candidates = defaultdict(list)
        self._filename_to_title = {}
        self._node_ids = set()
        for fid, node in self._nodes.items():
            fn = os.path.basename(fid)
            stem = fid.replace('.md', '')
            self._basename_candidates[fn].append(fid)
            self._basename_candidates[stem].append(fid)
            self._filename_to_title[fid] = node.get("label", "")
            self._node_ids.add(fid)

    # ─── Internal: data loading ───

    def _rebuild_from_data(self, data: dict):
        """Rebuild in-memory state from a full build_wiki_data() result."""
        self._nodes = {}
        for n in data["graph"]["nodes"]:
            fn = n["id"]
            pg = next((p for p in data["pages"] if p["filename"] == fn), None)
            self._nodes[fn] = {
                "id": fn,
                "label": n["label"],
                "type": n.get("type", "unknown"),
                "word_count": pg.get("word_count", 0) if pg else 0,
                "tags": pg.get("tags", []) if pg else [],
                "status": pg.get("status", "active") if pg else "active",
                "confidence": pg.get("confidence", "") if pg else "",
            }
        self._edges = [{"from": e["from"], "to": e["to"]} for e in data["graph"]["edges"]]
        self._rebuild_basename_index()

    def _scan_wiki(self) -> dict[str, float]:
        """Scan all wiki .md files, returning {relative_path: mtime}."""
        snapshot = {}
        if self.wiki_dir.exists():
            for md in self.wiki_dir.rglob("*.md"):
                rel = str(md.relative_to(self.wiki_dir))
                snapshot[rel] = md.stat().st_mtime
        return snapshot

    def _scan_wiki_and_save(self):
        """Scan and persist mtime snapshot."""
        self._save_snapshot(self._scan_wiki())

    def _load_snapshot(self) -> dict[str, float]:
        if self._cache_file.exists():
            try:
                return json.loads(self._cache_file.read_text())
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_snapshot(self, snapshot: dict[str, float]):
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache_file.write_text(json.dumps(snapshot, indent=2))

    def _save_state(self):
        """Persist in-memory graph state to disk for fast cold start."""
        state_file = self.cache_dir / "graph_state.json"
        state = {
            "nodes": self._nodes,
            "edges": self._edges,
        }
        state_file.write_text(
            json.dumps(state, ensure_ascii=False, default=str), encoding="utf-8"
        )

    def _try_load_state(self) -> bool:
        """Try loading persisted graph state. Returns True on success."""
        state_file = self.cache_dir / "graph_state.json"
        if not state_file.exists():
            return False
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            self._nodes = state.get("nodes", {})
            self._edges = state.get("edges", [])
            self._rebuild_basename_index()
            return bool(self._nodes)
        except (json.JSONDecodeError, IOError, KeyError):
            return False


# ─── Helpers ───

def _empty_result(raw_dir: Path) -> dict:
    from datetime import datetime
    return {
        "pages": [], "graph": {"nodes": [], "edges": []}, "log": [],
        "stats": {
            "total_pages": 0, "raw_sources": 0, "type_counts": {},
            "total_links": 0, "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        },
    }


def _resolve_target(
    target: str,
    node_ids: set[str],
    basename_candidates: dict[str, list[str]],
    filename_to_title: dict[str, str],
    title_hint: str = "",
) -> Optional[str]:
    """Resolve a wikilink target to its canonical full-path filename."""
    if target in node_ids:
        return target
    clean = target.split("#", 1)[0]
    if clean in node_ids:
        return clean
    candidates = basename_candidates.get(clean) or basename_candidates.get(os.path.basename(clean))
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    if title_hint:
        hint_lower = title_hint.lower().replace(" ", "-").replace("_", "-")
        scores = []
        for c in candidates:
            ct = filename_to_title.get(c, "").lower().replace(" ", "-").replace("_", "-")
            if hint_lower == ct:
                return c
            if hint_lower in ct or ct in hint_lower:
                scores.append((c, 2))
            else:
                hw = set(hint_lower.split("-"))
                cw = set(ct.split("-"))
                shared = len(hw & cw)
                if shared > 0:
                    scores.append((c, shared))
        if scores:
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[0][0]
    return candidates[0]
