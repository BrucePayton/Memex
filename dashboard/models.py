"""
Memex shared data models and parsing utilities.

Single source of truth for wiki page parsing, wikilink extraction,
frontmatter handling, and slug generation. Used by server.py,
memex_mcp.py, wiki_ops.py, and graph modules.
"""

import re
import time
import os
from dataclasses import dataclass, field
from typing import Optional

# ─── Regex patterns ───

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
WIKILINK_DETAILED_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]")
LOG_ENTRY_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] ([^\|]+?) \| (.+)$", re.MULTILINE)
# Cross-project wikilink: [[project-slug/page-path]] or [[project-slug/page|alias]]
CROSS_PROJECT_WIKILINK_RE = re.compile(
    r"\[\[([a-z0-9][a-z0-9-]*)/([^\]#|]+)(?:#([^\]|]*))?(?:\|([^\]]*))?\]\]"
)

# System pages excluded from graph nodes and treated as global hubs
SYSTEM_PAGES: frozenset[str] = frozenset({'index.md', 'log.md', 'overview.md'})


# ─── Dataclasses ───

@dataclass
class WikiPage:
    """Parsed wiki page with frontmatter and extracted metadata."""
    path: str
    title: str
    page_type: str  # concept|entity|technique|source-summary|analysis
    tags: list[str] = field(default_factory=list)
    status: str = "active"  # active|superseded|disputed
    confidence: str = "medium"  # high|medium|low
    created: str = ""
    last_updated: str = ""
    source_count: int = 0
    content: str = ""
    frontmatter: dict = field(default_factory=dict)
    links: list[str] = field(default_factory=list)  # outbound wikilinks
    citations: list[str] = field(default_factory=list)  # [^src-*] refs
    word_count: int = 0

    @property
    def filename(self) -> str:
        return os.path.basename(self.path)


@dataclass
class GraphNode:
    """Knowledge graph node representing a wiki page."""
    id: str
    label: str
    type: str
    word_count: int = 0
    tags: list[str] = field(default_factory=list)
    project: str = ""  # for cross-project graphs
    path: str = ""     # relative path within wiki/


@dataclass
class GraphEdge:
    """Knowledge graph edge representing a wikilink or inferred connection."""
    from_id: str
    to_id: str
    type: str = "wikilink"  # wikilink|inferred|bridge|cites|references|contradicts|defines


@dataclass
class SearchResult:
    """Unified search result from any search backend."""
    page_path: str
    title: str
    snippet: str
    score: float
    backend: str = "tfidf"  # tfidf|bm25|vector|hybrid
    page_type: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class ScheduleEntry:
    """Wiki maintenance schedule entry."""
    id: str
    name: str
    cron: str
    steps: list[str] = field(default_factory=list)
    enabled: bool = True
    project: str = ""
    include_ingest: bool = False
    reflect_window: str = "last-10-ingests"
    last_run: Optional[str] = None
    last_status: Optional[str] = None


# ─── Utility functions ───

def make_slug(title: str) -> str:
    """Convert title to filesystem-safe slug. Preserves Unicode (Korean/CJK)."""
    s = (title or "").strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        s = f"untitled-{int(time.time())}"
    return s


def parse_fm(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown text. Returns (meta_dict, body_string)."""
    meta: dict = {}
    body = text
    m = FRONTMATTER_RE.match(text)
    if not m:
        return meta, body
    body = text[m.end():]
    raw = m.group(1)
    # List values (indented '- ' items)
    for ml in re.finditer(r"^(\w+):\s*\n((?:\s+-\s+.+\n?)+)", raw, re.MULTILINE):
        meta[ml.group(1)] = [x.strip().strip("'\"") for x in re.findall(r"-\s+(.+)", ml.group(2))]
    for line in raw.strip().split("\n"):
        if ":" not in line or line.startswith("  "):
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if k in meta:
            continue
        lm = re.search(r"\[(.*?)\]", v)
        if lm:
            meta[k] = [x.strip().strip("'\"") for x in lm.group(1).split(",") if x.strip()]
        elif v:
            meta[k] = v.strip("'\"")
    return meta, body


def extract_links(body: str) -> list[str]:
    """Extract wikilink targets from markdown body. Strips anchors, adds .md suffix.

    [[page]]           → page.md
    [[page#section]]   → page.md
    [[page|alias]]     → page.md
    """
    results: set[str] = set()
    for m in WIKILINK_RE.finditer(body):
        link = m.group(1).strip()
        # Strip #anchor portion — graph edges point to pages, not sections
        link = link.split('#')[0]
        if not link.endswith('.md'):
            link += '.md'
        results.add(link)
    return sorted(results)


def extract_links_detailed(body: str) -> list[dict]:
    """Extract wikilinks with full metadata: target, alias, anchor (preserved)."""
    """Extract wikilinks with full metadata: target, alias, anchor.

    Returns list of {target: str, alias: str, anchor: str}.
    Uses WIKILINK_DETAILED_RE to capture the optional display alias.
    """
    results: list[dict] = []
    seen: set[str] = set()
    for m in WIKILINK_DETAILED_RE.finditer(body):
        target = m.group(1).strip()
        alias = (m.group(2) or "").strip()
        anchor = ""
        if '#' in target:
            target, anchor = target.split('#', 1)
            target = target.strip()
            anchor = anchor.strip()
        if not target.endswith('.md'):
            target += '.md'
        key = f"{target}#{anchor}"
        if key not in seen:
            seen.add(key)
            results.append({"target": target, "alias": alias, "anchor": anchor})
    return results


def resolve_wikilink_target(
    target: str,
    known_files: set[str],
    title_hint: str = "",
) -> Optional[str]:
    """Resolve a wikilink target to a canonical filename using basename matching.

    Handles exact match, basename lookup, and collision resolution via
    title similarity. Used by both graph builder and link validation.

    Returns the resolved full-path filename or None.
    """
    import os
    # Strip fragment for resolution
    clean = target.split('#', 1)[0]
    if clean in known_files:
        return clean
    if target in known_files:
        return target

    # Build basename index from known files
    candidates: dict[str, list[str]] = {}
    for f in known_files:
        bn = os.path.basename(f)
        stem = f.replace('.md', '')
        candidates.setdefault(bn, []).append(f)
        candidates.setdefault(stem, []).append(f)

    basename = os.path.basename(clean)
    matches = candidates.get(clean) or candidates.get(basename)
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]

    # Collision: prefer title hint similarity
    if title_hint:
        hint_lower = title_hint.lower().replace(" ", "-").replace("_", "-")
        for m in matches:
            m_lower = m.lower().replace(" ", "-").replace("_", "-")
            if hint_lower == m_lower:
                return m
        for m in matches:
            m_lower = m.lower().replace(" ", "-").replace("_", "-")
            if hint_lower in m_lower or m_lower in hint_lower:
                return m
        # Count shared words
        hw = set(hint_lower.split("-"))
        best = max(matches, key=lambda m: len(hw & set(
            m.lower().replace(" ", "-").replace("_", "-").split("-"))), default=None)
        return best
    return matches[0]


def extract_citations(body: str) -> list[str]:
    """Extract [^src-*] citation references from markdown body."""
    cite_ref_re = re.compile(r"\[\^src-([^\]]+)\]")
    return sorted(set(m.group(1) for m in cite_ref_re.finditer(body)))


def is_system_page(filename: str) -> bool:
    """Check if page is a system page (index, log, overview)."""
    return filename in SYSTEM_PAGES


def is_cross_project_link(target: str, known_slugs: set[str] | None = None) -> bool:
    """Check if a wikilink target uses cross-project syntax (project-slug/page).

    If known_slugs is provided, verifies the project slug is recognized.
    Otherwise, just checks the syntactic pattern.
    """
    m = CROSS_PROJECT_WIKILINK_RE.match(target) or CROSS_PROJECT_WIKILINK_RE.match(
        f"[[{target}]]" if not target.startswith("[[") else target)
    if not m:
        return False
    if known_slugs is not None:
        return m.group(1) in known_slugs
    return True


def parse_cross_project_link(target: str) -> Optional[dict]:
    """Parse a cross-project wikilink into {project_slug, page_path, anchor, alias}.

    Returns None if not a valid cross-project link.
    """
    raw = target
    if raw.startswith("[[") and raw.endswith("]]"):
        raw = raw[2:-2]
    m = CROSS_PROJECT_WIKILINK_RE.match(raw)
    if not m:
        # Try wrapping: the raw might be just the inner content
        m = CROSS_PROJECT_WIKILINK_RE.match(f"[[{raw}]]") if not raw.startswith("[[") else None
        if not m:
            return None
    return {
        "project_slug": m.group(1),
        "page_path": m.group(2).strip(),
        "anchor": (m.group(3) or "").strip(),
        "alias": (m.group(4) or "").strip(),
    }


def display_title(meta: dict, fallback_stem: str, ui_lang: Optional[str] = None) -> str:
    """Pick visible title with i18n support.

    Priority: language-specific title (title_zh/title_en/title_ko)
    → frontmatter title → stem with hyphens replaced by spaces.
    """
    stem_display = fallback_stem.replace("-", " ").title()
    if ui_lang in ("en", "ko", "zh"):
        lk = {"en": "title_en", "ko": "title_ko", "zh": "title_zh"}.get(ui_lang)
        if lk:
            tv = meta.get(lk)
            if isinstance(tv, str) and tv.strip():
                return tv.strip()
    bt = meta.get("title")
    if isinstance(bt, str) and bt.strip():
        return bt.strip()
    return stem_display


def append_log_entry(wiki_dir: "Path", action: str, title: str, description: str = "") -> None:
    """Atomically append an entry to wiki/log.md.

    Uses file-level locking (fcntl.flock) to coordinate with concurrent
    writers (scheduler, server threads, external LLM processes).

    Entry format: ## [YYYY-MM-DD] action | title\\ndescription\\n
    """
    import fcntl
    from datetime import datetime

    log_file = wiki_dir / "log.md"
    today = datetime.now().strftime("%Y-%m-%d")
    entry = f"\n## [{today}] {action} | {title}"
    if description:
        entry += f"\n{description.strip()}"
    entry += "\n"

    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(str(log_file), "a", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            if not log_file.exists() or log_file.stat().st_size == 0:
                f.seek(0)
                f.write("---\ntitle: Log\ntype: overview\nstatus: active\n---\n")
            f.write(entry)
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
