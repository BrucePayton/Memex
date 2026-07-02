"""
Wiki extensions for Memex: version management, entity aliases,
dynamic ontology types, OKF interop, and edit protection.

These are lightweight extensions that enhance the core wiki without
requiring architectural changes to the ingest/lint pipeline.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from dashboard.models import FRONTMATTER_RE, SYSTEM_PAGES


# ─── Version Management ───

def get_version_chain(wiki_dir: Path, page_path: str) -> list[dict]:
    """Get version history chain for a wiki page.

    Traces derived_from and superseded_by links to build a timeline.
    Returns [{path, title, version, date, status}]
    """
    from dashboard.models import parse_fm

    chain = []
    visited = set()
    current = page_path

    while current and current not in visited:
        visited.add(current)
        md = wiki_dir / current
        if not md.exists():
            break
        meta, _ = parse_fm(md.read_text(encoding="utf-8"))
        chain.append({
            "path": current,
            "title": meta.get("title", current),
            "version": meta.get("version", 1),
            "date": meta.get("last_updated", meta.get("created", "")),
            "status": meta.get("status", "active"),
        })
        # Follow chain forward (newer versions)
        current = meta.get("superseded_by", "")

    return chain


def find_derived_pages(wiki_dir: Path, source_page: str) -> list[dict]:
    """Find all pages derived from a source page (reverse version chain)."""
    from dashboard.models import parse_fm

    derived = []
    if not wiki_dir.exists():
        return derived

    for md in wiki_dir.rglob("*.md"):
        rel = str(md.relative_to(wiki_dir))
        meta, _ = parse_fm(md.read_text(encoding="utf-8"))
        if meta.get("derived_from") == source_page:
            derived.append({
                "path": rel,
                "title": meta.get("title", rel),
                "version": meta.get("version", 1),
                "date": meta.get("last_updated", ""),
            })
    return derived


# ─── Entity Alias Disambiguation ───

def load_aliases(wiki_dir: Path) -> dict[str, str]:
    """Load entity alias registry from wiki/aliases.md.

    Format:
    ```markdown
    | Alias | Canonical |
    |-------|-----------|
    | 区经 | 区域经理 |
    | AI | 人工智能 |
    ```
    Returns {alias: canonical_entity}
    """
    aliases_file = wiki_dir / "aliases.md"
    if not aliases_file.exists():
        return {}

    content = aliases_file.read_text(encoding="utf-8")
    aliases = {}
    for line in content.split("\n"):
        match = re.match(r"\|\s*(.+?)\s*\|\s*(.+?)\s*\|", line)
        if match and match.group(1) not in ("Alias", "---", "别名"):
            alias = match.group(1).strip()
            canonical = match.group(2).strip()
            aliases[alias] = canonical
    return aliases


def suggest_alias_replacements(text: str, aliases: dict[str, str]) -> list[dict]:
    """Scan text for known aliases and suggest wikilink replacements.

    Returns [{alias, canonical, count}]
    """
    suggestions = []
    for alias, canonical in aliases.items():
        count = text.count(alias)
        if count > 0:
            suggestions.append({
                "alias": alias,
                "canonical": canonical,
                "count": count,
                "wikilink": f"[[{canonical}]]",
            })
    return sorted(suggestions, key=lambda x: -x["count"])


# ─── Dynamic Ontology Types (PESO emergent) ───

ALLOWED_TYPES = {"concept", "entity", "technique", "source-summary", "analysis"}
PENDING_TYPES_FILE = ".pending_types.json"


def load_pending_types(project_root: Path) -> list[dict]:
    """Load pending emergent type proposals."""
    pf = project_root / PENDING_TYPES_FILE
    if pf.exists():
        return json.loads(pf.read_text())
    return []


def save_pending_types(project_root: Path, types: list[dict]):
    """Persist pending type proposals."""
    pf = project_root / PENDING_TYPES_FILE
    pf.write_text(json.dumps(types, indent=2, ensure_ascii=False))


def propose_new_type(
    project_root: Path,
    type_name: str,
    description: str,
    proposed_by: str = "llm",
) -> dict:
    """Propose a new page type (PESO emergent mode).

    Returns the proposal for Dashboard review/approval.
    """
    if type_name in ALLOWED_TYPES:
        return {"ok": False, "error": f"Type '{type_name}' already exists"}

    pending = load_pending_types(project_root)
    # Deduplicate
    for p in pending:
        if p["type"] == type_name:
            return {"ok": True, "status": "already_pending", "proposal": p}

    proposal = {
        "type": type_name,
        "description": description,
        "proposed_by": proposed_by,
        "proposed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "pending",  # pending | approved | rejected
    }
    pending.append(proposal)
    save_pending_types(project_root, pending)
    return {"ok": True, "status": "pending", "proposal": proposal}


def approve_type(project_root: Path, type_name: str) -> dict:
    """Approve a pending type proposal."""
    pending = load_pending_types(project_root)
    for p in pending:
        if p["type"] == type_name:
            p["status"] = "approved"
            ALLOWED_TYPES.add(type_name)
            save_pending_types(project_root, pending)
            return {"ok": True, "type": type_name, "status": "approved"}
    return {"ok": False, "error": f"No pending proposal for '{type_name}'"}


def get_allowed_types() -> set[str]:
    """Get current allowed types including approved emergent types."""
    return set(ALLOWED_TYPES)


# ─── OKF Interop ───

def import_okf_bundle(bundle_dir: Path, wiki_dir: Path) -> list[dict]:
    """Import OKF v0.1 bundle into Memex wiki.

    An OKF bundle is a directory of markdown files with YAML frontmatter.
    Returns list of imported page paths.
    """
    from dashboard.models import parse_fm, make_slug

    imported = []
    if not bundle_dir.exists():
        return imported

    for md in sorted(bundle_dir.rglob("*.md")):
        rel = str(md.relative_to(bundle_dir))
        text = md.read_text(encoding="utf-8")
        meta, body = parse_fm(text)

        okf_type = meta.get("type", "concept")
        title = meta.get("title", md.stem)
        slug = make_slug(title)

        # Map OKF types to Memex types
        type_map = {
            "concept": "concept",
            "entity": "entity",
            "technique": "technique",
            "source": "source-summary",
            "analysis": "analysis",
        }
        page_type = type_map.get(okf_type, okf_type)

        # Build Memex frontmatter
        memex_fm = f"""---
title: "{title}"
type: {page_type}
tags: {json.dumps(meta.get('tags', []))}
created: {meta.get('created', datetime.now().strftime('%Y-%m-%d'))}
last_updated: {datetime.now().strftime('%Y-%m-%d')}
source_count: 1
confidence: medium
status: active
okf_source: "{rel}"
---

{body}
"""
        target = wiki_dir / f"{slug}.md"
        target.write_text(memex_fm, encoding="utf-8")
        imported.append({
            "path": f"{slug}.md",
            "title": title,
            "okf_source": rel,
        })

    return imported


def export_to_okf(wiki_dir: Path, output_dir: Path) -> dict:
    """Export Memex wiki to OKF v0.1 bundle format."""
    from dashboard.models import parse_fm

    output_dir.mkdir(parents=True, exist_ok=True)
    exported = []

    if not wiki_dir.exists():
        return {"ok": False, "error": "Wiki directory not found"}

    for md in sorted(wiki_dir.rglob("*.md")):
        rel = str(md.relative_to(wiki_dir))
        if rel in SYSTEM_PAGES or rel == "aliases.md":
            continue

        text = md.read_text(encoding="utf-8")
        meta, body = parse_fm(text)

        # Convert to OKF format (minimal transformation)
        okf_meta = {
            "type": meta.get("type", "concept"),
            "title": meta.get("title", md.stem),
            "description": meta.get("description", ""),
            "tags": meta.get("tags", []),
            "timestamp": meta.get("last_updated", meta.get("created", "")),
        }

        okf_text = "---\n"
        for k, v in okf_meta.items():
            if isinstance(v, list):
                okf_text += f"{k}:\n"
                for item in v:
                    okf_text += f"  - {item}\n"
            else:
                okf_text += f"{k}: {v}\n"
        okf_text += "---\n\n" + body

        target = output_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(okf_text, encoding="utf-8")
        exported.append(rel)

    return {"ok": True, "exported_count": len(exported), "files": exported}


# ─── Edit Protection ───

def is_human_edited(wiki_dir: Path, page_path: str) -> bool:
    """Check if a page was manually edited by a human."""
    from dashboard.models import parse_fm

    md = wiki_dir / page_path
    if not md.exists():
        return False
    meta, _ = parse_fm(md.read_text(encoding="utf-8"))
    return meta.get("edited_by_human") in (True, "true", "True")


def mark_human_edited(wiki_dir: Path, page_path: str) -> bool:
    """Mark a page as human-edited (protected from automatic overwrites)."""
    md = wiki_dir / page_path
    if not md.exists():
        return False

    text = md.read_text(encoding="utf-8")
    if "edited_by_human: true" not in text:
        # Insert after last_updated line
        text = re.sub(
            r"(last_updated:.*\n)",
            r"\1edited_by_human: true\n",
            text,
        )
        md.write_text(text, encoding="utf-8")
    return True
