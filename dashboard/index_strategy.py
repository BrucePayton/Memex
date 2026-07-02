"""
index_strategy.py — determines index strategy based on page count and
auto-generates/updates index files.

Strategies:
  flat         (< 50 pages)  — single wiki/index.md
  hierarchical (50~200)      — per-type sub-indexes
  indexed      (> 200)       — sub-indexes + BM25 recommended
"""

import re
from datetime import datetime
from pathlib import Path

from dashboard.models import FRONTMATTER_RE, SYSTEM_PAGES

THRESHOLDS = {"flat": 50, "hierarchical": 200}

# type -> sub-index filename mapping
TYPE_INDEX = {
    "concept": "index-concepts.md",
    "technique": "index-techniques.md",
    "entity": "index-entities.md",
    "source-summary": "index-sources.md",
    "analysis": "index-analyses.md",
}

# these files are excluded from normal page counts
SYSTEM_FILES = SYSTEM_PAGES | set(TYPE_INDEX.values())


def _parse_type(text: str) -> str:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return "unknown"
    for line in m.group(1).split("\n"):
        if line.strip().startswith("type:"):
            return line.split(":", 1)[1].strip().strip("'\"")
    return "unknown"


def _parse_title(text: str, stem: str) -> str:
    m = FRONTMATTER_RE.match(text)
    if m:
        for line in m.group(1).split("\n"):
            if line.strip().startswith("title:"):
                return line.split(":", 1)[1].strip().strip("'\"")
    return stem.replace("-", " ").title()


def count_wiki_pages(wiki_dir: Path) -> int:
    """Actual wiki page count excluding system files"""
    count = 0
    for md in wiki_dir.rglob("*.md"):
        if md.name not in SYSTEM_FILES:
            count += 1
    return count


def get_strategy(wiki_dir: Path) -> dict:
    """Return current strategy + meta info"""
    n = count_wiki_pages(wiki_dir)
    if n < THRESHOLDS["flat"]:
        mode = "flat"
        next_threshold = THRESHOLDS["flat"]
        warning = None
    elif n <= THRESHOLDS["hierarchical"]:
        mode = "hierarchical"
        next_threshold = THRESHOLDS["hierarchical"]
        warning = None
    else:
        mode = "indexed"
        next_threshold = None
        warning = "200+ pages reached. Consider introducing qmd or vector search."

    # threshold proximity warning (within 5)
    proximity_warning = None
    if mode == "flat" and next_threshold - n <= 5:
        proximity_warning = f"pages until flat -> hierarchical transition {next_threshold - n}pages"
    elif mode == "hierarchical" and next_threshold and next_threshold - n <= 10:
        proximity_warning = f"pages until indexed transition {next_threshold - n}pages"

    return {
        "mode": mode,
        "page_count": n,
        "next_threshold": next_threshold,
        "warning": warning,
        "proximity_warning": proximity_warning,
    }


def _collect_pages(wiki_dir: Path) -> dict[str, list[tuple[str, str]]]:
    """Collect (filename, title) list per type"""
    by_type: dict[str, list[tuple[str, str]]] = {}
    for md in sorted(wiki_dir.rglob("*.md")):
        if md.name in SYSTEM_FILES:
            continue
        text = md.read_text("utf-8")
        ptype = _parse_type(text)
        title = _parse_title(text, md.stem)
        rel = str(md.relative_to(wiki_dir))
        by_type.setdefault(ptype, []).append((rel, title))
    return by_type


def _one_line(title: str, filename: str) -> str:
    stem = filename.replace(".md", "")
    return f"- [[{stem}|{title}]]"


def build_flat_index(wiki_dir: Path):
    """Generate single index.md (< 50 pages)"""
    by_type = _collect_pages(wiki_dir)
    today = datetime.now().strftime("%Y-%m-%d")

    sections = []
    # overview pages
    if (wiki_dir / "overview.md").exists():
        sections.append("## Overview\n- [[overview]] — wiki scope and current state")

    type_order = [
        ("source-summary", "Sources"),
        ("entity", "Entities"),
        ("concept", "Concepts"),
        ("technique", "Techniques"),
        ("analysis", "Analyses"),
    ]
    for ptype, heading in type_order:
        pages = by_type.get(ptype, [])
        if not pages:
            continue
        lines = [f"## {heading}"]
        for fn, title in sorted(pages, key=lambda x: x[1].lower()):
            lines.append(_one_line(title, fn))
        sections.append("\n".join(lines))

    # uncategorized
    known = {t for t, _ in type_order}
    for ptype, pages in sorted(by_type.items()):
        if ptype in known:
            continue
        lines = [f"## {ptype.title()}"]
        for fn, title in sorted(pages, key=lambda x: x[1].lower()):
            lines.append(_one_line(title, fn))
        sections.append("\n".join(lines))

    content = f"""---
title: Index
type: overview
created: 2026-04-22
last_updated: {today}
tags:
  - meta
---

# Wiki Index

All wiki pages, organized by type. Updated on every ingest.

{chr(10).join(sections)}
"""
    (wiki_dir / "index.md").write_text(content, "utf-8")


def build_hierarchical_index(wiki_dir: Path):
    """Generate per-type sub-indexes + summary index.md (50~200 pages)"""
    by_type = _collect_pages(wiki_dir)
    today = datetime.now().strftime("%Y-%m-%d")

    type_order = [
        ("source-summary", "Sources", "index-sources.md"),
        ("entity", "Entities", "index-entities.md"),
        ("concept", "Concepts", "index-concepts.md"),
        ("technique", "Techniques", "index-techniques.md"),
        ("analysis", "Analyses", "index-analyses.md"),
    ]

    summary_sections = []
    if (wiki_dir / "overview.md").exists():
        summary_sections.append("## Overview\n- [[overview]] — wiki scope and current state")

    for ptype, heading, idx_file in type_order:
        pages = by_type.get(ptype, [])
        count = len(pages)

        # generate sub-index
        lines = []
        for fn, title in sorted(pages, key=lambda x: x[1].lower()):
            lines.append(_one_line(title, fn))

        sub_content = f"""---
title: "Index — {heading}"
type: overview
created: {today}
last_updated: {today}
tags:
  - meta
  - index
---

# {heading} ({count})

{chr(10).join(lines) if lines else '(none yet)'}
"""
        (wiki_dir / idx_file).write_text(sub_content, "utf-8")

        # link in summary index
        idx_stem = idx_file.replace(".md", "")
        summary_sections.append(
            f"## {heading} ({count})\nSee [[{idx_stem}|full list]]"
        )

    # uncategorized
    known = {t for t, _, _ in type_order}
    for ptype, pages in sorted(by_type.items()):
        if ptype in known:
            continue
        lines = [f"## {ptype.title()} ({len(pages)})"]
        for fn, title in sorted(pages, key=lambda x: x[1].lower()):
            lines.append(_one_line(title, fn))
        summary_sections.append("\n".join(lines))

    content = f"""---
title: Index
type: overview
created: 2026-04-22
last_updated: {today}
tags:
  - meta
---

# Wiki Index (hierarchical)

> [!info] This wiki uses hierarchical indexing.
> Each type has its own sub-index page for faster navigation.

{chr(10).join(summary_sections)}
"""
    (wiki_dir / "index.md").write_text(content, "utf-8")


def rebuild_index(wiki_dir: Path) -> dict:
    """Force regeneration of index matching current strategy"""
    strategy = get_strategy(wiki_dir)
    mode = strategy["mode"]

    if mode == "flat":
        build_flat_index(wiki_dir)
        # delete sub-indexes if present
        for fn in TYPE_INDEX.values():
            f = wiki_dir / fn
            if f.exists():
                f.unlink()
    else:
        # hierarchical or indexed
        build_hierarchical_index(wiki_dir)

    return {"ok": True, "mode": mode, "page_count": strategy["page_count"]}


def get_index_instruction(wiki_dir: Path) -> str:
    """Index-navigation instructions embedded in LLM prompts (English)."""
    strategy = get_strategy(wiki_dir)
    mode = strategy["mode"]

    if mode == "flat":
        return "Read wiki/index.md first, then locate related pages."
    else:
        return """Read wiki/index.md to understand structure, then open the sub-index that matches the task:
- Sources: wiki/index-sources.md
- Entities: wiki/index-entities.md
- Concepts: wiki/index-concepts.md
- Techniques: wiki/index-techniques.md
- Analyses: wiki/index-analyses.md
Only read the sub-indexes you need."""
