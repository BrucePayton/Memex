#!/usr/bin/env python3
"""Memex MCP server.

Exposes the Memex wiki vault as a set of MCP tools so Claude (Desktop, Code,
or any MCP client) can read, search, and maintain the wiki directly.

Design notes
------------
- Standalone: this file is the only entry point. It runs over stdio so it is
  registered with `claude mcp add memex -- python <abs path>/memex_mcp.py`.
- Reuses `dashboard/project_registry.py` (no side effects) to resolve the
  project layout (legacy or multi-project under `projects/<slug>/`).
- Does NOT import `dashboard/server.py` to avoid its top-level side effects
  (git init, CLI PATH walking, `claude -p` subprocess machinery). Read/search
  helpers are duplicated here in small form.
- raw/ is immutable: `add_raw_source` refuses to overwrite. wiki/ is writable.
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# ─── locate repo + bring dashboard/ onto sys.path ────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = REPO_ROOT / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

import project_registry  # type: ignore  # noqa: E402
import wiki_ops  # type: ignore  # noqa: E402

# ─── MCP SDK ─────────────────────────────────────────────────────────────────

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    sys.stderr.write(
        "memex-mcp: missing dependency. Install with:\n"
        "  pip install --user 'mcp>=1.0' \n"
        "or use the bundled install script:\n"
        f"  bash {Path(__file__).parent / 'install.sh'}\n"
    )
    raise

mcp = FastMCP(
    "memex",
    instructions=(
        "Memex is a self-maintaining LLM wiki backed by an Obsidian vault. "
        "Use `get_instructions` once per session to load the wiki schema "
        "(frontmatter rules, citation format, contradiction policy). "
        "Then use the read tools (list_pages, read_page, search) to browse "
        "and the write tools (add_raw_source, create_page, update_page) to "
        "maintain. Never modify files under any raw/ directory; raw is "
        "immutable. Commit groups of related changes with git_commit. "
        "Semantic wiki operation tools (wiki_ingest, wiki_lint, wiki_lint_fix, "
        "wiki_reflect, wiki_compare, wiki_write, wiki_validate_links, wiki_loop) "
        "trigger LLM CLI operations for full wiki maintenance. "
        "Schedule management tools (schedule_list, schedule_create, schedule_delete, "
        "schedule_toggle, schedule_run_now, schedule_get) let you manage recurring "
        "wiki maintenance tasks."
    ),
)

# ─── small helpers (duplicated from server.py to keep this server lean) ──────

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
WORD_RE = re.compile(r"[\w가-힣]+")


def parse_fm(text: str) -> tuple[dict, str]:
    """Parse YAML-ish frontmatter, returning (meta, body).

    Mirrors `dashboard/server.py:parse_fm`. Supports scalar and list values.
    """
    meta: dict[str, Any] = {}
    m = FRONTMATTER_RE.match(text)
    if not m:
        return meta, text
    body = text[m.end():]
    raw = m.group(1)
    for ml in re.finditer(r"^(\w+):\s*\n((?:\s+-\s+.+\n?)+)", raw, re.MULTILINE):
        meta[ml.group(1)] = [
            x.strip().strip("'\"") for x in re.findall(r"-\s+(.+)", ml.group(2))
        ]
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
    return sorted({
        m.group(1).strip() + (".md" if not m.group(1).strip().endswith(".md") else "")
        for m in WIKILINK_RE.finditer(body)
    })


def _resolve(project: str | None) -> "project_registry.Project":
    """Resolve project slug → Project. Empty/None falls back to active/legacy."""
    slug = (project or "").strip() or None
    return project_registry.get_project(slug)


def _rel_to_repo(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(p)


def _safe_wiki_path(proj, filename: str) -> Path:
    """Resolve filename under wiki_dir and reject path traversal."""
    base = proj.wiki_dir.resolve()
    target = (proj.wiki_dir / filename).resolve()
    if base != target and base not in target.parents:
        raise ValueError(f"path escapes wiki/: {filename}")
    return target


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# ─── tools: project ──────────────────────────────────────────────────────────


@mcp.tool()
def list_projects() -> dict:
    """List all Memex projects (multi-project) plus legacy if present.

    Returns the active project slug and an array of {slug, title, is_legacy,
    description, model, wiki_dir, raw_dir}. Use the slug as `project` in
    other tools, or pass an empty string to use the active project.
    """
    out: list[dict] = []
    for p in project_registry.list_projects():
        out.append({
            "slug": p.slug,
            "title": p.title,
            "is_legacy": p.is_legacy,
            "description": p.description,
            "model": p.model,
            "wiki_dir": _rel_to_repo(p.wiki_dir),
            "raw_dir": _rel_to_repo(p.raw_dir),
        })
    legacy_info: dict | None = None
    if project_registry.LEGACY_WIKI.exists():
        try:
            lp = project_registry._legacy_project()  # type: ignore[attr-defined]
            legacy_info = {
                "slug": "",
                "title": lp.title,
                "is_legacy": True,
                "description": "Legacy single-project layout",
                "model": lp.model,
                "wiki_dir": _rel_to_repo(lp.wiki_dir),
                "raw_dir": _rel_to_repo(lp.raw_dir),
            }
        except Exception:
            pass
    return {
        "active": project_registry.get_active_slug(),
        "projects": out,
        "legacy": legacy_info,
        "has_projects": project_registry.has_projects(),
    }


@mcp.tool()
def get_instructions(project: str = "") -> dict:
    """Return the project's CLAUDE.md (wiki schema, citation rules, ingest workflow).

    Read this once at session start so you follow the wiki conventions for
    frontmatter, inline citations [^src-*], and contradiction resolution.
    """
    proj = _resolve(project)
    if not proj.claude_md.exists():
        return {"project": proj.slug, "found": False, "content": ""}
    return {
        "project": proj.slug,
        "found": True,
        "path": _rel_to_repo(proj.claude_md),
        "content": proj.claude_md.read_text("utf-8"),
    }


# ─── tools: wiki read ────────────────────────────────────────────────────────


@mcp.tool()
def stats(project: str = "") -> dict:
    """Return wiki counts: total pages, type distribution, raw source count, total links."""
    proj = _resolve(project)
    type_counts: dict[str, int] = {}
    pages = 0
    links = 0
    if proj.wiki_dir.exists():
        for md in proj.wiki_dir.rglob("*.md"):
            pages += 1
            text = md.read_text("utf-8")
            meta, body = parse_fm(text)
            t = meta.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
            links += len(WIKILINK_RE.findall(body))
    raw_count = 0
    if proj.raw_dir.exists():
        for f in proj.raw_dir.rglob("*"):
            if f.is_file() and not f.name.startswith(".") and "assets" not in f.parts:
                raw_count += 1
    return {
        "project": proj.slug,
        "total_pages": pages,
        "raw_sources": raw_count,
        "type_counts": type_counts,
        "total_links": links,
    }


@mcp.tool()
def list_pages(
    project: str = "",
    type_filter: str = "",
    folder: str = "",
    limit: int = 200,
) -> dict:
    """List wiki pages with frontmatter summary.

    Args:
        project: Project slug. Empty for active/legacy.
        type_filter: Optional type to filter ("concept", "entity", "technique",
            "source-summary", "analysis", or any custom type).
        folder: Optional folder under wiki/ (relative). E.g. "concepts".
        limit: Cap on number of pages returned (default 200).
    """
    proj = _resolve(project)
    base = proj.wiki_dir / folder if folder else proj.wiki_dir
    if not base.exists():
        return {"project": proj.slug, "pages": [], "truncated": False}
    items: list[dict] = []
    for md in sorted(base.rglob("*.md")):
        if len(items) >= limit:
            break
        text = md.read_text("utf-8")
        meta, body = parse_fm(text)
        if type_filter and meta.get("type") != type_filter:
            continue
        rel = str(md.relative_to(proj.wiki_dir))
        items.append({
            "filename": rel,
            "title": meta.get("title", md.stem.replace("-", " ").title()),
            "type": meta.get("type", "unknown"),
            "status": meta.get("status", "active"),
            "tags": meta.get("tags", []),
            "last_updated": meta.get("last_updated") or meta.get("updated", ""),
            "word_count": len(body.split()),
        })
    truncated = False
    if len(items) >= limit:
        # one more file would have existed; rough check
        all_count = sum(1 for _ in base.rglob("*.md"))
        truncated = all_count > limit
    return {"project": proj.slug, "pages": items, "truncated": truncated}


@mcp.tool()
def read_page(filename: str, project: str = "") -> dict:
    """Read a wiki page by filename (relative to wiki/, e.g. "concepts/scaling-laws.md").

    Returns frontmatter, body, links, and outbound link targets.
    """
    proj = _resolve(project)
    target = _safe_wiki_path(proj, filename)
    if not target.exists():
        return {"ok": False, "error": f"page not found: {filename}", "project": proj.slug}
    text = target.read_text("utf-8")
    meta, body = parse_fm(text)
    return {
        "ok": True,
        "project": proj.slug,
        "filename": str(target.relative_to(proj.wiki_dir)),
        "frontmatter": meta,
        "body": body,
        "links": extract_links(body),
        "word_count": len(body.split()),
    }


@mcp.tool()
def search(query: str, top_k: int = 10, project: str = "") -> dict:
    """TF-IDF search across wiki pages. Returns ranked snippets.

    Args:
        query: Search query (Korean and English supported).
        top_k: Number of results (default 10).
        project: Project slug (empty = active/legacy).
    """
    proj = _resolve(project)
    q_tokens = WORD_RE.findall(query.lower())
    if not q_tokens or not proj.wiki_dir.exists():
        return {"project": proj.slug, "results": []}

    docs: dict[str, dict] = {}
    for md in proj.wiki_dir.rglob("*.md"):
        rel = str(md.relative_to(proj.wiki_dir))
        text = md.read_text("utf-8")
        _, body = parse_fm(text)
        tokens = WORD_RE.findall(body.lower())
        if tokens:
            docs[rel] = {"tokens": tokens, "body": body}
    if not docs:
        return {"project": proj.slug, "results": []}

    df: dict[str, int] = {}
    for d in docs.values():
        for tok in set(d["tokens"]):
            df[tok] = df.get(tok, 0) + 1
    n = len(docs)

    scores: list[tuple[str, float]] = []
    for path, d in docs.items():
        tf: dict[str, int] = {}
        for tok in d["tokens"]:
            tf[tok] = tf.get(tok, 0) + 1
        score = 0.0
        for qt in q_tokens:
            if qt in tf and qt in df:
                score += (tf[qt] / len(d["tokens"])) * math.log(n / df[qt])
        if score > 0:
            scores.append((path, score))

    scores.sort(key=lambda x: -x[1])
    top = scores[: max(1, top_k)]
    results: list[dict] = []
    for path, sc in top:
        body = docs[path]["body"]
        snippet = ""
        low = body.lower()
        for qt in q_tokens:
            i = low.find(qt)
            if i >= 0:
                start = max(0, i - 80)
                end = min(len(body), i + 120)
                snippet = body[start:end].replace("\n", " ")
                break
        results.append({"filename": path, "score": round(sc, 4), "snippet": snippet})
    return {"project": proj.slug, "results": results}


@mcp.tool()
def folder_tree(project: str = "") -> dict:
    """Return the folder structure under wiki/ (folders + page filenames)."""
    proj = _resolve(project)
    tree: dict[str, Any] = {"project": proj.slug, "name": "wiki", "path": "", "children": [], "pages": []}
    wd = proj.wiki_dir
    if not wd.exists():
        return tree
    for f in sorted(wd.glob("*.md")):
        tree["pages"].append(f.name)
    for d in sorted(wd.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            sub: dict[str, Any] = {"name": d.name, "path": d.name, "children": [], "pages": []}
            for f in sorted(d.rglob("*.md")):
                sub["pages"].append(str(f.relative_to(wd)))
            for sd in sorted(d.iterdir()):
                if sd.is_dir() and not sd.name.startswith("."):
                    sub["children"].append({
                        "name": sd.name,
                        "path": str(sd.relative_to(wd)),
                        "pages": [str(f.relative_to(wd)) for f in sorted(sd.rglob("*.md"))],
                    })
            tree["children"].append(sub)
    return tree


@mcp.tool()
def recent_log(n: int = 20, project: str = "") -> dict:
    """Return the most recent N entries from wiki/log.md."""
    proj = _resolve(project)
    lf = proj.wiki_dir / "log.md"
    if not lf.exists():
        return {"project": proj.slug, "entries": []}
    text = lf.read_text("utf-8")
    _, body = parse_fm(text)
    entries: list[dict] = []
    pat = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] (\w+) \| (.+)$", re.MULTILINE)
    for m in pat.finditer(body):
        entries.append({"date": m.group(1), "action": m.group(2), "title": m.group(3)})
    entries.reverse()
    return {"project": proj.slug, "entries": entries[: max(1, n)]}


@mcp.tool()
def list_raw_sources(project: str = "") -> dict:
    """List files under raw/ (read-only — raw is immutable).

    Returns relative paths and sizes. Use `add_raw_source` to add new sources.
    """
    proj = _resolve(project)
    out: list[dict] = []
    if proj.raw_dir.exists():
        for f in sorted(proj.raw_dir.rglob("*")):
            if f.is_file() and not f.name.startswith(".") and "assets" not in f.parts:
                out.append({
                    "path": str(f.relative_to(proj.raw_dir)),
                    "size_bytes": f.stat().st_size,
                })
    return {"project": proj.slug, "sources": out}


# ─── tools: write ────────────────────────────────────────────────────────────


@mcp.tool()
def add_raw_source(filename: str, content: str, project: str = "") -> dict:
    """Add a new immutable source file to raw/.

    Filename may include a subfolder (e.g. "papers/attention.md"). If a file
    with the same name already exists, this returns an error rather than
    overwriting — raw/ is append-only.

    After adding, follow the CLAUDE.md ingest workflow: read the source,
    update or create wiki pages with inline [^src-*] citations, update
    wiki/index.md and wiki/log.md, and call `git_commit`.
    """
    proj = _resolve(project)
    proj.raw_dir.mkdir(parents=True, exist_ok=True)
    target = (proj.raw_dir / filename).resolve()
    base = proj.raw_dir.resolve()
    if base != target and base not in target.parents:
        return {"ok": False, "error": f"path escapes raw/: {filename}"}
    if target.exists():
        return {"ok": False, "error": f"raw/ file exists (immutable): {filename}"}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {
        "ok": True,
        "project": proj.slug,
        "raw_path": str(target.relative_to(REPO_ROOT)),
        "src_slug": f"src-{target.stem}",
    }


@mcp.tool()
def create_page(
    title: str,
    page_type: str,
    content: str = "",
    folder: str = "",
    tags: list[str] | None = None,
    sources: list[str] | None = None,
    project: str = "",
) -> dict:
    """Create a new wiki page with proper Memex frontmatter.

    Args:
        title: Page title (used to derive slug).
        page_type: One of "concept", "entity", "technique", "source-summary",
            "analysis", or any custom type used in this wiki.
        content: Body markdown (without frontmatter). Caller must include
            inline [^src-*] citations and link footnote definitions if making
            factual claims.
        folder: Optional subfolder under wiki/.
        tags: Optional tag list.
        sources: Optional list of source slugs (without "src-" prefix).
        project: Project slug.
    """
    if not title.strip():
        return {"ok": False, "error": "title required"}
    proj = _resolve(project)
    proj.wiki_dir.mkdir(parents=True, exist_ok=True)
    slug = project_registry.make_slug(title)
    base = proj.wiki_dir / folder if folder else proj.wiki_dir
    base.mkdir(parents=True, exist_ok=True)
    target = base / f"{slug}.md"
    n = 2
    while target.exists():
        target = base / f"{slug}-{n}.md"
        n += 1

    today = _today()
    tag_lines = "\n".join(f"  - {t}" for t in (tags or []))
    src_lines = "\n".join(f"  - {s}" for s in (sources or []))
    fm_parts = [
        "---",
        f'title: "{title}"',
        f"type: {page_type}",
        f"created: {today}",
        f"last_updated: {today}",
        f"source_count: {len(sources or [])}",
        "confidence: medium",
        "status: active",
    ]
    if tags:
        fm_parts.append("tags:")
        fm_parts.append(tag_lines)
    else:
        fm_parts.append("tags: []")
    if sources:
        fm_parts.append("sources:")
        fm_parts.append(src_lines)
    fm_parts.append("---\n")
    body = content or f"# {title}\n\n<!-- TODO: add content with inline [^src-*] citations -->"
    target.write_text("\n".join(fm_parts) + "\n" + body + "\n", encoding="utf-8")
    return {
        "ok": True,
        "project": proj.slug,
        "filename": str(target.relative_to(proj.wiki_dir)),
        "path": str(target.relative_to(REPO_ROOT)),
    }


@mcp.tool()
def update_page(filename: str, content: str, project: str = "") -> dict:
    """Overwrite a wiki page's content. Caller is responsible for keeping
    frontmatter present (include the `---` block at the top).

    Refuses if the resolved path is outside wiki/ or under raw/.
    """
    proj = _resolve(project)
    try:
        target = _safe_wiki_path(proj, filename)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    if project_registry.is_protected_raw(target):
        return {"ok": False, "error": f"raw/ is immutable: {filename}"}
    if not target.exists():
        return {"ok": False, "error": f"page not found: {filename}"}
    target.write_text(content, encoding="utf-8")
    return {
        "ok": True,
        "project": proj.slug,
        "filename": str(target.relative_to(proj.wiki_dir)),
    }


@mcp.tool()
def create_folder(name: str, parent: str = "", project: str = "") -> dict:
    """Create a folder under wiki/ (or under wiki/<parent>/)."""
    proj = _resolve(project)
    proj.wiki_dir.mkdir(parents=True, exist_ok=True)
    base = proj.wiki_dir / parent if parent else proj.wiki_dir
    base = base.resolve()
    if proj.wiki_dir.resolve() != base and proj.wiki_dir.resolve() not in base.parents:
        return {"ok": False, "error": f"parent escapes wiki/: {parent}"}
    target = (base / name).resolve()
    if base != target.parent and base not in target.parents:
        return {"ok": False, "error": f"name escapes parent: {name}"}
    target.mkdir(parents=True, exist_ok=True)
    return {
        "ok": True,
        "project": proj.slug,
        "path": str(target.relative_to(proj.wiki_dir)),
    }


@mcp.tool()
def git_commit(message: str, project: str = "") -> dict:
    """Stage wiki/, raw/, ingest-reports/ and commit with the given message.

    Use Conventional Commit format, e.g. "ingest: attention is all you need"
    or "lint: fix orphaned pages". Returns the new commit hash, or no_op
    if there was nothing staged.
    """
    if not message.strip():
        return {"ok": False, "error": "message required"}
    proj = _resolve(project)
    cwd = str(REPO_ROOT)

    if not (REPO_ROOT / ".git").is_dir():
        return {"ok": False, "error": "repository is not a git repo"}

    if proj.is_legacy:
        paths = ["wiki", "raw", "ingest-reports"]
    else:
        rel = str(proj.root.relative_to(REPO_ROOT))
        paths = [
            f"{rel}/wiki",
            f"{rel}/raw",
            f"{rel}/ingest-reports",
            f"{rel}/CLAUDE.md",
            f"{rel}/.settings.json",
            "projects.json",
        ]
    for p in paths:
        if (REPO_ROOT / p).exists():
            subprocess.run(["git", "add", p], cwd=cwd, capture_output=True, text=True)

    diff = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=cwd, capture_output=True, text=True,
    )
    files = [f for f in diff.stdout.strip().split("\n") if f]
    if not files:
        return {"ok": True, "no_op": True, "project": proj.slug, "files": []}

    r = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=cwd, capture_output=True, text=True,
    )
    if r.returncode != 0:
        return {
            "ok": False,
            "project": proj.slug,
            "error": (r.stderr or r.stdout)[:500],
        }
    log = subprocess.run(
        ["git", "log", "-1", "--format=%H"],
        cwd=cwd, capture_output=True, text=True,
    )
    return {
        "ok": True,
        "project": proj.slug,
        "hash": log.stdout.strip(),
        "files": files,
    }


# ─── tools: project management ─────────────────────────────────────────────────


@mcp.tool()
def list_template_names() -> dict:
    """List available project template names.

    Templates are stored in templates/<name>/ with a CLAUDE.md file.
    Use one of these names as the `template` argument in `create_project`.
    """
    return {"templates": project_registry.list_template_names()}


@mcp.tool()
def create_project(
    slug_hint: str,
    title: str,
    description: str = "",
    model: str = "default",
    template: str = "",
) -> dict:
    """Create a new Memex project.

    Creates projects/<slug>/ directory with wiki/, raw/, and other standard
    folders, plus CLAUDE.md from the selected template. The new project becomes
    active.

    Args:
        slug_hint: Used to derive the project slug. May contain spaces, will
            be normalized to lowercase hyphen-separated.
        title: Project title (display name).
        description: Optional project description (for your reference).
        model: Optional model to use for this project ("default", or a model
            from the available list).
        template: Optional template name from `list_template_names()` to use.
            Empty for generic template.
    """
    try:
        proj = project_registry.create_project(
            slug_hint=slug_hint,
            title=title,
            description=description,
            model=model,
            template=template,
        )
    except ValueError as e:
        return {"ok": False, "error": str(e)}

    # Try to git-commit the new project
    cwd = str(REPO_ROOT)
    if (REPO_ROOT / ".git").is_dir():
        rel = str(proj.root.relative_to(REPO_ROOT))
        subprocess.run(["git", "add", rel, "projects.json"], cwd=cwd, capture_output=True, text=True)
        r = subprocess.run(
            ["git", "commit", "-m", f"init: create project {proj.slug}"],
            cwd=cwd, capture_output=True, text=True,
        )

    return {
        "ok": True,
        "slug": proj.slug,
        "title": proj.title,
        "description": proj.description,
        "model": proj.model,
        "template": template,
        "root": str(proj.root.relative_to(REPO_ROOT)),
    }


@mcp.tool()
def switch_project(slug: str) -> dict:
    """Switch active project to the given slug.

    Returns the project info and updates the last_used timestamp.
    """
    try:
        proj = project_registry.switch_project(slug)
        return {
            "ok": True,
            "slug": proj.slug,
            "title": proj.title,
            "description": proj.description,
            "model": proj.model,
        }
    except KeyError as e:
        return {"ok": False, "error": str(e)}


@mcp.tool()
def update_project_settings(
    slug: str,
    model: str | None = None,
    title: str | None = None,
    description: str | None = None,
) -> dict:
    """Update project settings (model, title, description).

    Args:
        slug: The project to update.
        model: Optional new model for this project (if omitted, not changed).
        title: Optional new title for this project (if omitted, not changed).
        description: Optional new description for this project (if omitted,
            not changed).
    """
    try:
        proj = project_registry.update_project_settings(
            slug=slug,
            model=model,
            title=title,
            description=description,
        )
        return {
            "ok": True,
            "slug": proj.slug,
            "title": proj.title,
            "description": proj.description,
            "model": proj.model,
        }
    except (KeyError, ValueError) as e:
        return {"ok": False, "error": str(e)}


@mcp.tool()
def delete_project(slug: str, confirm: bool = False) -> dict:
    """Delete a project.

    The project is moved to projects/.trash/<slug>-<timestamp> (soft delete)
    rather than immediately removed. Confirm=True is required.

    Args:
        slug: Project to delete.
        confirm: Must be True to proceed (safety check).
    """
    result = project_registry.delete_project(slug, confirm=confirm)
    if not result.get("ok"):
        return result

    # Try to git-commit the removal
    cwd = str(REPO_ROOT)
    if (REPO_ROOT / ".git").is_dir():
        subprocess.run(["git", "add", "-u", "projects.json"], cwd=cwd, capture_output=True, text=True)
        subprocess.run(
            ["git", "commit", "-m", f"delete: remove project {slug}"],
            cwd=cwd, capture_output=True, text=True,
        )

    return result


# ─── tools: graph analysis ───────────────────────────────────────────────────

# Graph tools port graphify's core capabilities into Memex using pure Python
# stdlib (no networkx).  They operate on the wiki/ wikilink graph.

# Optional graphify integration (enhanced features if available)
_GRAPHIFY_AVAILABLE = False
try:
    from graphify.cluster import cluster
    from graphify.analyze import god_nodes, surprising_connections, suggest_questions
except ImportError:
    cluster = god_nodes = surprising_connections = suggest_questions = None
try:
    from graphify.export import generate_html as graphify_export_html
except ImportError:
    graphify_export_html = None
if cluster is not None:
    _GRAPHIFY_AVAILABLE = True

# Graph persistence directory
def _get_graph_dir(proj):
    """Get the .graph directory for a project, creating it if needed."""
    graph_dir = proj.root / ".graph"
    graph_dir.mkdir(exist_ok=True)
    return graph_dir

def _load_persisted_graph(proj):
    """Load persisted graph data if available, returns None otherwise."""
    graph_dir = _get_graph_dir(proj)
    graph_file = graph_dir / "graph.json"
    labels_file = graph_dir / "community_labels.json"

    if not graph_file.exists():
        return None

    import json
    try:
        data = json.loads(graph_file.read_text(encoding="utf-8"))
        if labels_file.exists():
            data["community_labels"] = json.loads(labels_file.read_text(encoding="utf-8"))
        return data
    except Exception:
        return None

def _persist_graph(proj, graph_data):
    """Persist graph data to .graph directory."""
    import json
    graph_dir = _get_graph_dir(proj)

    # Save main graph
    graph_file = graph_dir / "graph.json"
    graph_file.write_text(json.dumps(graph_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Save community labels separately if present
    if "community_labels" in graph_data:
        labels_file = graph_dir / "community_labels.json"
        labels_file.write_text(json.dumps(graph_data["community_labels"], ensure_ascii=False, indent=2), encoding="utf-8")


def _build_wiki_graph(proj) -> tuple[list[dict], list[dict]]:
    """Scan wiki/ and build a simple {nodes, edges} graph from wikilinks."""
    import os as _os
    nodes: list[dict] = []
    edges: list[dict] = []
    sys_pages = {"index.md", "log.md", "overview.md"}
    id_to_info: dict[str, dict] = {}

    if proj.wiki_dir.exists():
        for md in proj.wiki_dir.rglob("*.md"):
            rel = str(md.relative_to(proj.wiki_dir))
            text = md.read_text("utf-8")
            meta, body = parse_fm(text)
            pt = meta.get("type", "unknown")
            title = meta.get("title", md.stem.replace("-", " ").title())
            id_to_info[rel] = {
                "id": rel, "label": title, "type": pt,
                "word_count": len(body.split()), "tags": meta.get("tags", []),
            }
            links = extract_links(body)
            for lnk in links:
                edges.append({"from": rel, "to": lnk})

    # Build basename → [all matching ids] lookup for resolving bare wikilinks
    basename_candidates: dict[str, list[str]] = {}
    for fid in id_to_info:
        fn = _os.path.basename(fid)
        stem = fid.replace('.md', '')
        if fn not in basename_candidates:
            basename_candidates[fn] = []
        basename_candidates[fn].append(fid)
        if stem not in basename_candidates:
            basename_candidates[stem] = []
        basename_candidates[stem].append(fid)

    def _resolve(target):
        clean = target.split("#", 1)[0]
        if clean in id_to_info:
            return clean
        cands = basename_candidates.get(clean) or basename_candidates.get(_os.path.basename(clean))
        if not cands:
            return None
        if len(cands) == 1:
            return cands[0]
        # Collision: prefer by label similarity
        hint = clean.lower().replace("-"," ").replace("_"," ")
        best = None; best_score = -1
        for c in cands:
            ct = id_to_info[c]["label"].lower().replace("-"," ").replace("_"," ")
            hw = set(hint.split()); cw = set(ct.split())
            score = len(hw & cw)
            if score > best_score:
                best_score = score; best = c
        return best or cands[0]

    # Resolve edge targets using basename lookup
    for e in edges:
        resolved = _resolve(e["to"])
        if resolved:
            e["to"] = resolved
        elif e["to"] not in id_to_info:
            # Stub node for unresolved targets
            stem = e["to"].replace(".md", "").replace("-", " ").title()
            id_to_info[e["to"]] = {"id": e["to"], "label": stem, "type": "missing",
                                   "word_count": 0, "tags": []}

    nodes = list(id_to_info.values())
    return nodes, edges


@mcp.tool()
def graph_build(project: str = "") -> dict:
    """Build a knowledge graph from wiki pages.

    Scans wiki/ directory, parses wikilinks [[...]], and returns nodes + edges.
    Nodes have: id, label, type, word_count, tags.
    Edges have: from, to, type.
    """
    proj = _resolve(project)
    nodes, edges = _build_wiki_graph(proj)
    return {"project": proj.slug, "nodes": nodes, "edges": edges}


@mcp.tool()
def graph_community(project: str = "") -> dict:
    """Detect communities in the wiki graph using connected components.

    Returns communities (connected components), cohesion scores, and
    splits large communities via greedy local-density clustering.
    """
    from collections import deque

    proj = _resolve(project)
    nodes, edges = _build_wiki_graph(proj)
    node_ids = [n["id"] for n in nodes]
    id_idx = {nid: i for i, nid in enumerate(node_ids)}
    n = len(node_ids)
    adj: list[set[int]] = [set() for _ in range(n)]
    for e in edges:
        if e["from"] in id_idx and e["to"] in id_idx:
            u, v = id_idx[e["from"]], id_idx[e["to"]]
            adj[u].add(v)
            adj[v].add(u)

    # BFS connected components
    visited = [False] * n
    components: list[list[str]] = []
    for start in range(n):
        if visited[start]:
            continue
        comp: list[str] = []
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

    # Cohesion score: actual_edges / max_possible_edges within each community
    def cohesion_score(nodes_in_comp: list[str]) -> float:
        nc = len(nodes_in_comp)
        if nc <= 1:
            return 1.0
        comp_set = set(nodes_in_comp)
        actual = 0
        for e in edges:
            if e["from"] in comp_set and e["to"] in comp_set:
                actual += 1
        possible = nc * (nc - 1) / 2
        return round(actual / possible, 2) if possible > 0 else 0.0

    # Split large communities (>10 nodes) by local density
    final_components: list[list[str]] = []
    for comp in components:
        if len(comp) <= 10:
            final_components.append(comp)
        else:
            # Greedy split: pick high-degree seeds, assign each node to nearest seed
            comp_set = set(comp)
            comp_idx = {nid: i for i, nid in enumerate(comp)}
            comp_adj: list[set[int]] = [set() for _ in range(len(comp))]
            for e in edges:
                if e["from"] in comp_idx and e["to"] in comp_idx:
                    u, v = comp_idx[e["from"]], comp_idx[e["to"]]
                    comp_adj[u].add(v)
                    comp_adj[v].add(u)
            degrees = [(len(comp_adj[i]), i) for i in range(len(comp))]
            degrees.sort(reverse=True)
            seeds = [degrees[0][1], degrees[1][1]] if len(comp) > 5 else [degrees[0][1]]
            clusters: list[list[str]] = [[] for _ in seeds]
            for i in range(len(comp)):
                if i in seeds:
                    continue
                # Assign to seed with most shared neighbors
                best = 0
                best_score = -1
                for si, seed in enumerate(seeds):
                    shared = len(comp_adj[i] & comp_adj[seed])
                    if shared > best_score:
                        best_score = shared
                        best = si
                clusters[best].append(comp[i])
            for si, seed in enumerate(seeds):
                clusters[si].append(comp[seed])
            final_components.extend([c for c in clusters if c])

    # Sort by size descending
    final_components.sort(key=len, reverse=True)
    cohesion = {i: cohesion_score(c) for i, c in enumerate(final_components)}

    return {
        "project": proj.slug,
        "communities": {str(i): c for i, c in enumerate(final_components)},
        "cohesion": cohesion,
        "community_count": len(final_components),
    }


@mcp.tool()
def graph_god_nodes(project: str = "", top_n: int = 10) -> dict:
    """Return the most-connected wiki pages (highest degree).

    Excludes system pages (index.md, log.md, overview.md).
    """
    proj = _resolve(project)
    nodes, edges = _build_wiki_graph(proj)
    sys_pages = {"index.md", "log.md", "overview.md"}
    degree: dict[str, int] = {}
    for n in nodes:
        if n["id"] not in sys_pages:
            degree[n["id"]] = 0
    for e in edges:
        if e["from"] in degree:
            degree[e["from"]] += 1
        if e["to"] in degree:
            degree[e["to"]] += 1

    sorted_nodes = sorted(degree.items(), key=lambda x: -x[1])
    result = []
    for nid, deg in sorted_nodes[:top_n]:
        info = next((n for n in nodes if n["id"] == nid), None)
        result.append({
            "id": nid,
            "label": info["label"] if info else nid,
            "degree": deg,
            "type": info["type"] if info else "unknown",
        })
    return {"project": proj.slug, "god_nodes": result}


@mcp.tool()
def graph_stats(project: str = "") -> dict:
    """Return graph summary statistics.

    Node count, edge count, community count, type distribution,
    isolated pages, average degree, graph density.
    """
    proj = _resolve(project)
    nodes, edges = _build_wiki_graph(proj)
    sys_pages = {"index.md", "log.md", "overview.md"}

    type_counts: dict[str, int] = {}
    for n in nodes:
        type_counts[n["type"]] = type_counts.get(n["type"], 0) + 1

    degree: dict[str, int] = {n["id"]: 0 for n in nodes if n["id"] not in sys_pages}
    for e in edges:
        if e["from"] in degree:
            degree[e["from"]] += 1
        if e["to"] in degree:
            degree[e["to"]] += 1

    n_real = len(degree)
    avg_degree = round(sum(degree.values()) / n_real, 2) if n_real > 0 else 0
    max_possible = n_real * (n_real - 1) / 2 if n_real > 1 else 1
    density = round(len(edges) / max_possible, 4) if max_possible > 0 else 0
    isolated = sum(1 for d in degree.values() if d == 0)

    return {
        "project": proj.slug,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "type_counts": type_counts,
        "isolated_pages": isolated,
        "avg_degree": avg_degree,
        "density": density,
        "real_nodes": n_real,
    }


@mcp.tool()
def graph_shortest_path(source: str, target: str, project: str = "") -> dict:
    """Find the shortest path between two wiki pages (BFS).

    source and target can be filenames or page titles.
    """
    from collections import deque

    proj = _resolve(project)
    nodes, edges = _build_wiki_graph(proj)
    node_map: dict[str, str] = {}  # lowercase title/stem -> id
    for n in nodes:
        node_map[n["id"].lower()] = n["id"]
        stem = n["id"].replace(".md", "").lower()
        node_map[stem] = n["id"]
        node_map[n["label"].lower()] = n["id"]

    src_id = node_map.get(source.lower())
    tgt_id = node_map.get(target.lower())
    if not src_id:
        return {"ok": False, "error": f"source node not found: {source}"}
    if not tgt_id:
        return {"ok": False, "error": f"target node not found: {target}"}

    if src_id == tgt_id:
        return {"ok": True, "path": [src_id], "hops": 0, "edges": []}

    adj: dict[str, list[str]] = {n["id"]: [] for n in nodes}
    for e in edges:
        if e["from"] in adj and e["to"] in adj:
            adj[e["from"]].append(e["to"])
            adj[e["to"]].append(e["from"])

    # BFS
    visited: dict[str, str | None] = {src_id: None}
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
    path: list[str] = []
    cur: str | None = tgt_id
    while cur is not None:
        path.append(cur)
        cur = visited[cur]
    path.reverse()

    path_edges = [{"from": path[i], "to": path[i + 1]} for i in range(len(path) - 1)]
    return {"ok": True, "path": path, "hops": len(path) - 1, "edges": path_edges}


@mcp.tool()
def graph_neighbors(node_id: str, project: str = "") -> dict:
    """Return direct neighbors of a wiki page node.

    node_id can be a filename or page title.
    """
    proj = _resolve(project)
    nodes, edges = _build_wiki_graph(proj)
    node_map: dict[str, str] = {}
    for n in nodes:
        node_map[n["id"].lower()] = n["id"]
        node_map[n["label"].lower()] = n["id"]

    nid = node_map.get(node_id.lower())
    if not nid:
        return {"ok": False, "error": f"node not found: {node_id}"}

    neighbors: list[dict] = []
    seen: set[str] = set()
    for e in edges:
        if e["from"] == nid and e["to"] not in seen:
            seen.add(e["to"])
            info = next((n for n in nodes if n["id"] == e["to"]), None)
            neighbors.append({"id": e["to"], "label": info["label"] if info else e["to"],
                              "type": info["type"] if info else "unknown", "relation": "wikilink"})
        elif e["to"] == nid and e["from"] not in seen:
            seen.add(e["from"])
            info = next((n for n in nodes if n["id"] == e["from"]), None)
            neighbors.append({"id": e["from"], "label": info["label"] if info else e["from"],
                              "type": info["type"] if info else "unknown", "relation": "wikilink"})

    node_info = next((n for n in nodes if n["id"] == nid), None)
    return {
        "ok": True, "project": proj.slug,
        "node": {"id": nid, "label": node_info["label"] if node_info else nid,
                 "type": node_info["type"] if node_info else "unknown"},
        "neighbors": neighbors, "neighbor_count": len(neighbors),
    }


@mcp.tool()
def graph_insights(project: str = "") -> dict:
    """Discover interesting patterns in the wiki graph.

    Cross-type connections, bridge pages, isolated pages, and
    low-cohesion communities.
    """
    proj = _resolve(project)
    nodes, edges = _build_wiki_graph(proj)
    sys_pages = {"index.md", "log.md", "overview.md"}

    node_info: dict[str, dict] = {n["id"]: n for n in nodes}
    degree: dict[str, int] = {n["id"]: 0 for n in nodes}
    for e in edges:
        if e["from"] in degree:
            degree[e["from"]] += 1
        if e["to"] in degree:
            degree[e["to"]] += 1

    # Cross-type connections
    cross_type: list[dict] = []
    for e in edges:
        src = node_info.get(e["from"])
        tgt = node_info.get(e["to"])
        if src and tgt and src["type"] != tgt["type"]:
            cross_type.append({
                "from": e["from"], "from_type": src["type"],
                "to": e["to"], "to_type": tgt["type"],
            })

    # Isolated pages (degree <= 1, not system pages)
    isolated = []
    for nid, deg in degree.items():
        if deg <= 1 and nid not in sys_pages:
            info = node_info.get(nid)
            isolated.append({
                "id": nid, "label": info["label"] if info else nid,
                "type": info["type"] if info else "unknown", "degree": deg,
            })

    # Bridge pages: pages whose removal increases connected component count
    from collections import deque
    node_ids = [n["id"] for n in nodes if n["id"] not in sys_pages]
    adj: dict[str, list[str]] = {nid: [] for nid in node_ids}
    for e in edges:
        if e["from"] in adj and e["to"] in adj:
            adj[e["from"]].append(e["to"])
            adj[e["to"]].append(e["from"])

    def count_components(exclude: str | None = None) -> int:
        remaining = [nid for nid in node_ids if nid != exclude]
        if not remaining:
            return 0
        vis: set[str] = set()
        comps = 0
        for start in remaining:
            if start in vis:
                continue
            comps += 1
            q = deque([start])
            vis.add(start)
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if v != exclude and v not in vis:
                        vis.add(v)
                        q.append(v)
        return comps

    base_comps = count_components()
    bridges = []
    for nid in node_ids:
        if degree.get(nid, 0) < 2:
            continue
        new_comps = count_components(exclude=nid)
        if new_comps > base_comps:
            info = node_info.get(nid)
            bridges.append({
                "id": nid, "label": info["label"] if info else nid,
                "type": info["type"] if info else "unknown",
                "degree": degree[nid],
                "components_if_removed": new_comps,
            })
    bridges.sort(key=lambda x: -x["components_if_removed"])

    suggestions: list[str] = []
    if isolated:
        suggestions.append(f"{len(isolated)} isolated page(s) found — consider adding more wikilinks")
    if bridges:
        suggestions.append(f"{len(bridges)} bridge page(s) detected — these connect separate graph regions")
    if cross_type:
        suggestions.append(f"{len(cross_type)} cross-type connection(s) found")

    return {
        "project": proj.slug,
        "cross_type": cross_type[:20],
        "bridges": bridges[:10],
        "isolated": isolated[:20],
        "suggestions": suggestions,
    }


@mcp.tool()
def graph_export(format: str = "json", project: str = "") -> dict:
    """Export the wiki knowledge graph.

    format='json': returns the full graph as JSON.
    format='html': generates a self-contained interactive HTML visualization.
    """
    import json as _json

    proj = _resolve(project)
    nodes, edges = _build_wiki_graph(proj)

    if format == "json":
        out = proj.root / "graph-export.json"
        out.write_text(_json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        return {"ok": True, "project": proj.slug, "path": str(out.relative_to(REPO_ROOT)), "format": "json"}

    if format == "html":
        # Minimal self-contained HTML with Canvas force-directed graph
        import base64
        nodes_json = _json.dumps(nodes, ensure_ascii=False)
        edges_json = _json.dumps(edges, ensure_ascii=False)
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Memex Graph</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0d1117;color:#c9d1d9;font-family:-apple-system,BlinkMacSystemFont,sans-serif;overflow:hidden}}
canvas{{width:100vw;height:100vh;cursor:grab}}
#legend{{position:fixed;bottom:12px;left:12px;background:#161b22ee;border:1px solid #30363d;border-radius:8px;padding:8px 12px;font-size:11px}}
#legend span{{display:inline-flex;align-items:center;gap:4px;margin-right:12px}}
#legend i{{width:8px;height:8px;border-radius:50%;display:inline-block}}
#info{{position:fixed;top:12px;left:12px;background:#161b22ee;border:1px solid #30363d;border-radius:8px;padding:6px 10px;font-size:11px;color:#8b949e}}
</style></head><body>
<div id="info">{len(nodes)} nodes · {len(edges)} edges · click a node to highlight</div>
<div id="legend"></div>
<canvas id="cv"></canvas>
<script>
var TC={{source:'#3fb950',entity:'#58a6ff',concept:'#bc8cff',analysis:'#39d2c0',overview:'#8b949e',missing:'#f85149',unknown:'#8b949e'}};
var nodes={nodes_json},edges={edges_json};
var cv=document.getElementById('cv'),ctx=cv.getContext('2d');
function resize(){{cv.width=innerWidth*devicePixelRatio;cv.height=innerHeight*devicePixelRatio;ctx.scale(devicePixelRatio,devicePixelRatio);}}
resize();addEventListener('resize',resize);
var W=innerWidth,H=innerHeight;
var ns=nodes.map(function(n){{return {{...n,x:W/2+(Math.random()-.5)*400,y:H/2+(Math.random()-.5)*400,vx:0,vy:0,r:n.type==='overview'?16:10}};}});
var nm={{}};ns.forEach(function(n){{nm[n.id]=n;}});
var es=edges.filter(function(e){{return nm[e.from]&&nm[e.to];}}).map(function(e){{return {{s:nm[e.from],t:nm[e.to]}};}});
var hov=null,drag=null;
// Legend
var types={{}};ns.forEach(function(n){{types[n.type]=true;}});
var lg=document.getElementById('legend');
Object.keys(types).forEach(function(tp){{lg.innerHTML+='<span><i style="background:'+(TC[tp]||'#8b949e')+'"></i>'+tp+'</span>';}});
function tick(){{
  var cx=W/2,cy=H/2;
  for(var n of ns){{n.vx+=(cx-n.x)*.001;n.vy+=(cy-n.y)*.001;}}
  for(var i=0;i<ns.length;i++)for(var j=i+1;j<ns.length;j++){{
    var a=ns[i],b=ns[j],dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)||1,f=1200/(d*d);
    a.vx-=dx/d*f;a.vy-=dy/d*f;b.vx+=dx/d*f;b.vy+=dy/d*f;
  }}
  for(var e of es){{
    var dx2=e.t.x-e.s.x,dy2=e.t.y-e.s.y,d2=Math.sqrt(dx2*dx2+dy2*dy2)||1,f2=(d2-140)*.004;
    e.s.vx+=dx2/d2*f2;e.s.vy+=dy2/d2*f2;e.t.vx-=dx2/d2*f2;e.t.vy-=dy2/d2*f2;
  }}
  for(var n of ns){{
    if(n===drag)continue;n.vx*=.82;n.vy*=.82;
    n.x+=n.vx;n.y+=n.vy;n.x=Math.max(n.r,Math.min(W-n.r,n.x));n.y=Math.max(n.r,Math.min(H-n.r,n.y));
  }}
  ctx.clearRect(0,0,W,H);
  for(var e of es){{
    var hi=hov&&(e.s.id===hov.id||e.t.id===hov.id);
    ctx.strokeStyle=hi?'#58a6ff66':'#30363d';ctx.lineWidth=hi?2:1;
    ctx.beginPath();ctx.moveTo(e.s.x,e.s.y);ctx.lineTo(e.t.x,e.t.y);ctx.stroke();
  }}
  for(var n of ns){{
    var c=TC[n.type]||'#8b949e',hi=hov&&hov.id===n.id;
    ctx.beginPath();ctx.arc(n.x,n.y,n.r,0,Math.PI*2);
    ctx.fillStyle=hi?c:c+'88';ctx.fill();
    if(hi){{ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.stroke();}}
    ctx.fillStyle=hi?'#e6edf3':'#8b949e';ctx.font=(hi?'12':'10')+'px sans-serif';ctx.textAlign='center';
    ctx.fillText(n.label,n.x,n.y+n.r+13);
  }}
  requestAnimationFrame(tick);
}}
function hit(mx,my){{for(var n of ns){{var dx=mx-n.x,dy=my-n.y;if(dx*dx+dy*dy<(n.r+8)**2)return n;}}return null;}}
cv.onmousemove=function(e){{var r=cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;if(drag){{drag.x=mx;drag.y=my;drag.vx=0;drag.vy=0;return;}}hov=hit(mx,my);cv.style.cursor=hov?'pointer':'default';}};
cv.onmousedown=function(e){{var r=cv.getBoundingClientRect();drag=hit(e.clientX-r.left,e.clientY-r.top);}};
cv.onmouseup=function(){{drag=null;}};
tick();
</script></body></html>"""
        out = proj.root / "graph-export.html"
        out.write_text(html, encoding="utf-8")
        return {"ok": True, "project": proj.slug, "path": str(out.relative_to(REPO_ROOT)), "format": "html"}

    return {"ok": False, "error": f"unsupported format: {format}"}


# ─── resources: graph ────────────────────────────────────────────────────────


@mcp.resource("memex://graph/stats")
def resource_graph_stats() -> str:
    """Graph summary statistics as plain text."""
    # Use default project
    proj = _resolve("")
    result = graph_stats(project="")
    lines = [
        f"Nodes: {result['node_count']}",
        f"Edges: {result['edge_count']}",
        f"Real nodes: {result['real_nodes']}",
        f"Isolated pages: {result['isolated_pages']}",
        f"Average degree: {result['avg_degree']}",
        f"Graph density: {result['density']}",
        "Type distribution:",
    ]
    for t, c in sorted(result.get("type_counts", {}).items()):
        lines.append(f"  {t}: {c}")
    return "\n".join(lines)


@mcp.resource("memex://graph/god-nodes")
def resource_graph_god_nodes() -> str:
    """Top 10 most-connected wiki pages as plain text."""
    result = graph_god_nodes(project="", top_n=10)
    lines = ["God nodes (most connected wiki pages):"]
    for i, n in enumerate(result["god_nodes"], 1):
        lines.append(f"  {i}. {n['label']} — {n['degree']} connections ({n['type']})")
    return "\n".join(lines)


@mcp.resource("memex://graph/insights")
def resource_graph_insights() -> str:
    """Interesting patterns and suggestions as plain text."""
    result = graph_insights(project="")
    lines = ["Wiki Graph Insights:"]
    if result.get("suggestions"):
        lines.append("")
        lines.append("Suggestions:")
        for s in result["suggestions"]:
            lines.append(f"  - {s}")
    if result.get("bridges"):
        lines.append("")
        lines.append("Bridge pages (connect separate graph regions):")
        for b in result["bridges"][:5]:
            lines.append(f"  - {b['label']} ({b['degree']} links, would create {b['components_if_removed']} components if removed)")
    if result.get("isolated"):
        lines.append("")
        lines.append(f"Isolated pages ({len(result['isolated'])}):")
        for iso in result["isolated"][:10]:
            lines.append(f"  - {iso['label']} [{iso['type']}] (degree: {iso['degree']})")
    return "\n".join(lines)


# ─── enhanced graph tools (optional, use graphify if available) ───────────────

@mcp.tool()
def graph_composite(project: str = "") -> dict:
    """Get composite graph data (nodes + edges + communities + cohesion + labels)."""
    proj = _resolve(project)

    # First try to load persisted graph
    persisted = _load_persisted_graph(proj)
    if persisted:
        persisted["project"] = proj.slug
        persisted["persisted"] = True
        return persisted

    # Otherwise build from scratch
    nodes, edges = _build_wiki_graph(proj)
    community_result = graph_community(project)

    result = {
        "project": proj.slug,
        "persisted": False,
        "graphify_enhanced": _GRAPHIFY_AVAILABLE,
        "nodes": nodes,
        "edges": edges,
        "communities": community_result["communities"],
        "cohesion": community_result["cohesion"],
        "community_count": community_result["community_count"],
        "community_labels": {},
    }

    return result


@mcp.tool()
def graph_rebuild(project: str = "") -> dict:
    """Rebuild and persist the graph (uses graphify if available)."""
    import json
    proj = _resolve(project)
    nodes, edges = _build_wiki_graph(proj)
    community_result = graph_community(project)

    result = {
        "project": proj.slug,
        "graphify_enhanced": _GRAPHIFY_AVAILABLE,
        "nodes": nodes,
        "edges": edges,
        "communities": community_result["communities"],
        "cohesion": community_result["cohesion"],
        "community_count": community_result["community_count"],
        "community_labels": {},
    }

    # Persist the graph
    _persist_graph(proj, result)

    return {
        "ok": True,
        "project": proj.slug,
        "graphify_enhanced": _GRAPHIFY_AVAILABLE,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "community_count": community_result["community_count"],
    }


@mcp.tool()
def graph_name_community(community_id: str, name: str, project: str = "") -> dict:
    """Set a human-readable name for a community."""
    proj = _resolve(project)

    # Load current persisted graph or build new one
    data = _load_persisted_graph(proj)
    if not data:
        # Build and persist first
        nodes, edges = _build_wiki_graph(proj)
        community_result = graph_community(project)
        data = {
            "nodes": nodes,
            "edges": edges,
            "communities": community_result["communities"],
            "cohesion": community_result["cohesion"],
            "community_count": community_result["community_count"],
            "community_labels": {},
        }

    # Update the label
    if "community_labels" not in data:
        data["community_labels"] = {}
    data["community_labels"][community_id] = name

    # Persist
    _persist_graph(proj, data)

    return {
        "ok": True,
        "project": proj.slug,
        "community_id": community_id,
        "name": name,
    }


@mcp.tool()
def graph_get_community(community_id: str, project: str = "") -> dict:
    """Get detailed information about a specific community."""
    proj = _resolve(project)
    composite = graph_composite(project)

    communities = composite.get("communities", {})
    if community_id not in communities:
        return {"ok": False, "error": f"Community not found: {community_id}"}

    node_ids = communities[community_id]
    cohesion = composite.get("cohesion", {}).get(community_id, 0)
    label = composite.get("community_labels", {}).get(community_id, f"Community {community_id}")

    # Get full node info
    node_map = {n["id"]: n for n in composite.get("nodes", [])}
    nodes = [node_map.get(nid, {"id": nid, "label": nid}) for nid in node_ids]

    return {
        "ok": True,
        "project": proj.slug,
        "community_id": community_id,
        "name": label,
        "cohesion": cohesion,
        "node_count": len(nodes),
        "nodes": nodes,
    }


# ─── tools: semantic wiki operations ─────────────────────────────────────────
# These wrap dashboard/wiki_ops.py so external Claude can trigger wiki actions
# via natural conversation ("lint the wiki", "run the maintenance loop", etc.)


@mcp.tool()
def wiki_ingest(
    title: str, content: str, folder: str = "", project: str = ""
) -> dict:
    """Trigger full ingest of a source into the wiki (creates/updates wiki pages).

    Args:
        title: Source title (used to derive slug).
        content: Raw source content.
        folder: Optional wiki subfolder.
        project: Project slug.
    """
    return wiki_ops.op_ingest(title=title, content=content, folder=folder, project=project)


@mcp.tool()
def wiki_lint(project: str = "") -> dict:
    """Run full wiki lint audit per CLAUDE.md checklist.

    Checks: frontmatter, citations, orphan pages, cross-links, freshness.
    Returns lint report text.
    """
    return wiki_ops.op_lint(project=project)


@mcp.tool()
def wiki_lint_fix(project: str = "") -> dict:
    """Auto-fix all lint issues found by wiki_lint.

    Fixes: missing frontmatter, uncited claims, orphan pages, stale last_updated,
    status/superseded_by inconsistencies.
    """
    return wiki_ops.op_lint_fix(project=project)


@mcp.tool()
def wiki_reflect(
    window: str = "last-10-ingests", project: str = ""
) -> dict:
    """Run reflect analysis: meta-analysis of wiki patterns and improvement suggestions.

    Analyzes recent log, ingest reports, and low-ratio queries to suggest:
    - Missing wiki pages for frequently mentioned entities
    - Schema updates for CLAUDE.md
    - Suggested sources to ingest
    - Contradiction policy improvements

    Args:
        window: Time window ("last-10-ingests", "last-week").
        project: Project slug.
    """
    return wiki_ops.op_reflect(window=window, project=project)


@mcp.tool()
def wiki_compare(
    page_a: str, page_b: str, save_as: str = "", project: str = ""
) -> dict:
    """Compare two wiki pages.

    Structure: Common ground, Differences, Relationship/implications.

    Args:
        page_a: First wiki page filename.
        page_b: Second wiki page filename.
        save_as: Optional title to save comparison as a new page.
        project: Project slug.
    """
    return wiki_ops.op_compare(page_a=page_a, page_b=page_b, save_as=save_as, project=project)


@mcp.tool()
def wiki_write(
    topic: str, length: str = "medium", style: str = "blog", project: str = ""
) -> dict:
    """Writing assistant: generate wiki page content with citations.

    Args:
        topic: Topic to write about.
        length: Article length ("short", "medium", "long").
        style: Writing style ("blog", "paper", "explainer").
        project: Project slug.
    """
    return wiki_ops.op_write(topic=topic, length=length, style=style, project=project)


@mcp.tool()
def wiki_validate_links(project: str = "") -> dict:
    """Validate all wiki wikilinks and citation health.

    Returns:
    - broken_links: [[wikilinks]] with no matching page
    - citation_health: ratio of cited vs uncited claims
    - summary: total pages, broken links, critical flag
    """
    return wiki_ops.op_validate_links(project=project)


@mcp.tool()
def wiki_loop(
    steps: list[str] | None = None,
    include_ingest: bool = False,
    reflect_window: str = "last-10-ingests",
    continue_on_error: bool = False,
    project: str = "",
) -> dict:
    """Execute the wiki maintenance loop: sequential steps with progress tracking.

    Default steps: lint → lint_fix → reflect.
    Optionally includes ingest (detects and ingests uncited raw sources first).

    Args:
        steps: List of step names: "lint", "lint_fix", "reflect", "validate_links".
        include_ingest: Auto-ingest new raw sources before other steps.
        reflect_window: Window for reflect analysis.
        continue_on_error: Continue to next step if current fails.
        project: Project slug.
    """
    return wiki_ops.run_loop(
        project=project,
        steps=steps,
        include_ingest=include_ingest,
        reflect_window=reflect_window,
        continue_on_error=continue_on_error,
    )


# ─── tools: schedule management ──────────────────────────────────────────────


def _load_schedules() -> list[dict]:
    """Load schedules from .dashboard-settings.json."""
    settings_file = wiki_ops.SETTINGS_FILE
    if not settings_file.exists():
        return []
    try:
        data = json.loads(settings_file.read_text("utf-8"))
        return data.get("schedules", [])
    except Exception:
        return []


def _save_schedules(schedules: list[dict]):
    """Save schedules to .dashboard-settings.json."""
    settings_file = wiki_ops.SETTINGS_FILE
    data = {}
    if settings_file.exists():
        try:
            data = json.loads(settings_file.read_text("utf-8"))
        except Exception:
            pass
    data["schedules"] = schedules
    settings_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@mcp.tool()
def schedule_list(project: str = "") -> dict:
    """List all configured wiki maintenance schedules."""
    schedules = _load_schedules()
    return {"ok": True, "schedules": schedules}


@mcp.tool()
def schedule_create(
    name: str,
    cron: str,
    steps: list[str],
    enabled: bool = True,
    project: str = "",
    include_ingest: bool = False,
    reflect_window: str = "last-10-ingests",
) -> dict:
    """Create a new scheduled wiki maintenance task.

    Args:
        name: Schedule name (human-readable).
        cron: 5-field cron expression (minute hour dom month dow).
        steps: List of step names: "lint", "lint_fix", "reflect", "validate_links".
        enabled: Whether schedule is active.
        project: Project slug.
        include_ingest: Include ingest step.
        reflect_window: Window for reflect analysis.
    """
    import hashlib
    schedules = _load_schedules()
    sched_id = hashlib.md5(name.encode()).hexdigest()[:8]
    sched = {
        "id": sched_id,
        "name": name,
        "cron": cron,
        "steps": steps,
        "enabled": enabled,
        "project": project,
        "include_ingest": include_ingest,
        "reflect_window": reflect_window,
        "last_run": None,
        "last_status": None,
    }
    schedules.append(sched)
    _save_schedules(schedules)
    return {"ok": True, "schedule": sched}


@mcp.tool()
def schedule_delete(schedule_id: str) -> dict:
    """Delete a scheduled wiki maintenance task.

    Args:
        schedule_id: The schedule ID to delete.
    """
    schedules = _load_schedules()
    new_schedules = [s for s in schedules if s.get("id") != schedule_id]
    if len(new_schedules) == len(schedules):
        return {"ok": False, "error": f"schedule not found: {schedule_id}"}
    _save_schedules(new_schedules)
    return {"ok": True, "deleted": schedule_id}


@mcp.tool()
def schedule_toggle(schedule_id: str, enabled: bool) -> dict:
    """Enable or disable a scheduled task.

    Args:
        schedule_id: The schedule ID to toggle.
        enabled: New enabled state.
    """
    schedules = _load_schedules()
    for s in schedules:
        if s.get("id") == schedule_id:
            s["enabled"] = enabled
            _save_schedules(schedules)
            return {"ok": True, "schedule_id": schedule_id, "enabled": enabled}
    return {"ok": False, "error": f"schedule not found: {schedule_id}"}


@mcp.tool()
def schedule_run_now(schedule_id: str) -> dict:
    """Manually trigger a scheduled task immediately.

    Args:
        schedule_id: The schedule ID to run.
    """
    schedules = _load_schedules()
    sched = next((s for s in schedules if s.get("id") == schedule_id), None)
    if not sched:
        return {"ok": False, "error": f"schedule not found: {schedule_id}"}

    result = wiki_ops.run_loop(
        project=sched.get("project", ""),
        steps=sched.get("steps", ["lint"]),
        include_ingest=sched.get("include_ingest", False),
        reflect_window=sched.get("reflect_window", "last-10-ingests"),
    )

    # Update last_run and last_status
    for s in schedules:
        if s.get("id") == schedule_id:
            s["last_run"] = datetime.now().isoformat()
            s["last_status"] = "ok" if result.get("ok") else "failed"
            _save_schedules(schedules)
            break

    return {"ok": True, "schedule_id": schedule_id, "result": result}


@mcp.tool()
def schedule_get(schedule_id: str) -> dict:
    """Get details of a specific scheduled task.

    Args:
        schedule_id: The schedule ID to look up.
    """
    schedules = _load_schedules()
    sched = next((s for s in schedules if s.get("id") == schedule_id), None)
    if not sched:
        return {"ok": False, "error": f"schedule not found: {schedule_id}"}
    return {"ok": True, "schedule": sched}


# ─── tools: knowledge universe (cross-project) ───────────────────────────────

_UNIVERSE_CONFIG_FILE = REPO_ROOT / ".memex" / "universe_config.json"


def _load_universe_config() -> dict:
    """Load universe configuration."""
    if _UNIVERSE_CONFIG_FILE.exists():
        try:
            return json.loads(_UNIVERSE_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "version": 1,
        "auto_join_new": False,
        "auto_join_import": True,
        "auto_join_sync": True,
        "default_view": "2d",
        "excluded_projects": [],
        "pending_confirmation": [],
        "galaxy_positions": {},
    }


def _save_universe_config(config: dict):
    """Save universe configuration."""
    _UNIVERSE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _UNIVERSE_CONFIG_FILE.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _universe_project_nodes(proj) -> tuple[list, list, dict]:
    """Build graph data for a single project with project-prefixed IDs."""
    nodes, edges, node_map = _build_wiki_graph(proj)
    prefixed_nodes = []
    prefixed_edges = []

    for n in nodes:
        nid = f"{proj.slug}/{n['filename']}"
        prefixed_nodes.append({
            "id": nid,
            "label": n["label"],
            "type": n.get("type", "unknown"),
            "filename": n["filename"],
            "word_count": n.get("word_count", 0),
            "tags": n.get("tags", []),
            "project": proj.slug,
        })

    for e in edges:
        src_id = f"{proj.slug}/{e['from']}"
        tgt_id = f"{proj.slug}/{e['to']}"
        prefixed_edges.append({
            "source": src_id,
            "target": tgt_id,
            "type": "wikilink",
            "project": proj.slug,
        })

    return prefixed_nodes, prefixed_edges, node_map


def _detect_cross_project_bridges(all_nodes: list) -> list:
    """Detect cross-project connections based on title similarity."""
    bridges = []
    from collections import defaultdict

    # Group by normalized title
    title_map: dict[str, list] = defaultdict(list)
    for n in all_nodes:
        # Normalize: lowercase, strip common suffixes
        key = re.sub(r'[^a-z가-힣0-9]+', '', n["label"].lower())
        if len(key) > 4:
            title_map[key].append(n)

    for key, nodes in title_map.items():
        if len(nodes) < 2:
            continue
        projects = set(n["project"] for n in nodes)
        if len(projects) < 2:
            continue
        # Cross-project match found
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if nodes[i]["project"] != nodes[j]["project"]:
                    bridges.append({
                        "from_node": nodes[i]["id"],
                        "from_title": nodes[i]["label"],
                        "from_project": nodes[i]["project"],
                        "to_node": nodes[j]["id"],
                        "to_title": nodes[j]["label"],
                        "to_project": nodes[j]["project"],
                        "similarity": 0.85,
                        "reason": "标题相同或高度相似",
                    })

    # Also check tag overlap
    tag_map: dict[str, list] = defaultdict(list)
    for n in all_nodes:
        for tag in n.get("tags", []):
            tag_map[tag.lower()].append(n)

    for tag, nodes in tag_map.items():
        if len(nodes) < 2:
            continue
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if nodes[i]["project"] != nodes[j]["project"]:
                    # Check if already added
                    exists = any(
                        b["from_node"] == nodes[i]["id"] and b["to_node"] == nodes[j]["id"]
                        for b in bridges
                    )
                    if not exists:
                        bridges.append({
                            "from_node": nodes[i]["id"],
                            "from_title": nodes[i]["label"],
                            "from_project": nodes[i]["project"],
                            "to_node": nodes[j]["id"],
                            "to_title": nodes[j]["label"],
                            "to_project": nodes[j]["project"],
                            "similarity": 0.5,
                            "reason": f"共享标签: {tag}",
                        })

    return bridges


@mcp.tool()
def graph_universe_config(config: dict = None, project: str = "") -> dict:
    """获取或更新知识宇宙配置。

    配置项：
    - auto_join_new: 新创建项目是否自动加入
    - auto_join_import: 导入项目是否自动加入
    - auto_join_sync: 同步项目是否自动加入
    - default_view: "2d" 或 "3d"
    - excluded_projects: 排除的项目列表
    - pending_confirmation: 等待确认的项目列表
    - galaxy_positions: 星系位置 {slug: {x, y}}
    """
    if config is None:
        return {"ok": True, "config": _load_universe_config()}

    current = _load_universe_config()
    allowed_keys = {
        "auto_join_new", "auto_join_import", "auto_join_sync",
        "default_view", "excluded_projects", "pending_confirmation",
        "galaxy_positions",
    }
    for k, v in config.items():
        if k in allowed_keys:
            current[k] = v
    _save_universe_config(current)

    return {"ok": True, "config": current}


@mcp.tool()
def graph_join_universe(slug: str, project: str = "") -> dict:
    """将项目加入知识宇宙。

    Args:
        slug: 要加入的项目slug
    """
    config = _load_universe_config()
    excluded = config.get("excluded_projects", [])

    if slug in excluded:
        excluded.remove(slug)
        config["excluded_projects"] = excluded

    # Remove from pending
    pending = config.get("pending_confirmation", [])
    if slug in pending:
        pending.remove(slug)
        config["pending_confirmation"] = pending

    # Calculate position if not set
    positions = config.get("galaxy_positions", {})
    if slug not in positions:
        proj_count = len([
            p for p in project_registry.list_projects()
            if p.slug not in excluded
        ])
        angle = (proj_count - 1) * (2 * math.pi / max(proj_count, 7))
        positions[slug] = {
            "x": round(math.cos(angle) * 300, 1),
            "y": round(math.sin(angle) * 300, 1),
        }
        config["galaxy_positions"] = positions

    _save_universe_config(config)

    return {
        "ok": True,
        "project": slug,
        "position": positions.get(slug, {"x": 0, "y": 0}),
        "animation": "simple_join",
    }


@mcp.tool()
def graph_leave_universe(slug: str, project: str = "") -> dict:
    """将项目从知识宇宙中隐藏。

    Args:
        slug: 要隐藏的项目slug
    """
    config = _load_universe_config()
    excluded = config.get("excluded_projects", [])

    if slug not in excluded:
        excluded.append(slug)
        config["excluded_projects"] = excluded
        _save_universe_config(config)

    return {"ok": True, "project": slug, "animation": "simple_fade"}


@mcp.tool()
def graph_new_projects(project: str = "") -> dict:
    """检查是否有新加入的项目需要处理。

    Returns:
        {new: [slugs], pending: [...]}
    """
    config = _load_universe_config()
    pending_slugs = config.get("pending_confirmation", [])
    excluded = config.get("excluded_projects", [])

    pending = []
    for slug in pending_slugs:
        for p in project_registry.list_projects():
            if p.slug == slug:
                pending.append({
                    "slug": p.slug,
                    "title": p.title,
                    "description": p.description,
                })

    # New projects = those not in excluded and not pending
    all_slugs = {p.slug for p in project_registry.list_projects()}
    known_slugs = set(excluded) | set(pending_slugs)
    new_slugs = list(all_slugs - known_slugs)

    return {
        "ok": True,
        "new": new_slugs,
        "pending": pending,
    }


@mcp.tool()
def graph_universe(project_filter: list = None, project: str = "") -> dict:
    """获取知识宇宙完整数据。

    Args:
        project_filter: 可选，只包含指定slug的项目列表，None表示全部
        project: 保留兼容性（可以为空）

    Returns:
        {
            universe: {total_nodes, total_edges, projects},
            nodes: [...],
            edges: [...],
            bridges: [...]
        }
    """
    config = _load_universe_config()
    excluded = set(config.get("excluded_projects", []))

    all_nodes = []
    all_edges = []
    project_info = {}

    for proj in project_registry.list_projects():
        if proj.slug in excluded:
            continue
        if project_filter and proj.slug not in project_filter:
            continue

        nodes, edges, node_map = _universe_project_nodes(proj)
        all_nodes.extend(nodes)
        all_edges.extend(edges)

        project_info[proj.slug] = {
            "title": proj.title,
            "description": proj.description,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    bridges = _detect_cross_project_bridges(all_nodes)

    return {
        "universe": {
            "total_nodes": len(all_nodes),
            "total_edges": len(all_edges),
            "projects": project_info,
        },
        "nodes": all_nodes,
        "edges": all_edges,
        "bridges": bridges,
    }


@mcp.tool()
def graph_project(slug: str, project: str = "") -> dict:
    """获取单个项目的图谱。

    Args:
        slug: 项目slug
    """
    proj = _resolve(slug)
    nodes, edges, node_map = _build_wiki_graph(proj)

    return {
        "ok": True,
        "project": proj.slug,
        "title": proj.title,
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


@mcp.tool()
def graph_bridges(min_similarity: float = 0.3, project: str = "") -> dict:
    """获取跨项目虫洞列表。

    Args:
        min_similarity: 最低相似度阈值
    """
    universe_data = graph_universe()
    bridges = universe_data.get("bridges", [])

    filtered = [b for b in bridges if b.get("similarity", 0) >= min_similarity]
    filtered.sort(key=lambda x: -x["similarity"])

    return {
        "ok": True,
        "bridges": filtered,
        "count": len(filtered),
    }


@mcp.tool()
def graph_search_universe(query: str, limit: int = 20, project: str = "") -> dict:
    """在知识宇宙中搜索。

    Args:
        query: 搜索关键词
        limit: 返回结果数量
    """
    universe_data = graph_universe()
    nodes = universe_data["nodes"]

    results = []
    q_lower = query.lower()
    q_words = re.findall(r'[\w가-힣]+', q_lower)

    for n in nodes:
        score = 0.0
        context_parts = []
        label_lower = n["label"].lower()

        # Title match
        if q_lower in label_lower:
            score = max(score, 1.0)
            context_parts.append("标题匹配")
        elif any(w in label_lower for w in q_words if len(w) > 2):
            score = max(score, 0.7)
            context_parts.append("标题部分匹配")

        # Tag match
        tags_lower = [t.lower() for t in n.get("tags", [])]
        if any(q_lower in t for t in tags_lower):
            score = max(score, 0.7)
            context_parts.append("标签匹配")
        elif any(w in t for t in tags_lower for w in q_words if len(w) > 2):
            score = max(score, 0.4)
            context_parts.append("标签部分匹配")

        # Type match
        if n.get("type", "").lower() == q_lower:
            score = max(score, 0.6)
            context_parts.append("类型匹配")

        if score > 0:
            results.append({
                "node": n,
                "score": round(score, 2),
                "context": ", ".join(context_parts),
            })

    results.sort(key=lambda x: -x["score"])
    return {
        "ok": True,
        "query": query,
        "results": results[:limit],
        "total_matches": len(results),
    }


@mcp.tool()
def graph_god_nodes_universe(limit: int = 20, project: str = "") -> dict:
    """全宇宙最重要的节点（按连接数排序）。

    Args:
        limit: 返回数量
    """
    universe_data = graph_universe()
    nodes = universe_data["nodes"]
    edges = universe_data["edges"]

    # Count degree
    degree_count: dict[str, int] = {}
    for e in edges:
        degree_count[e["source"]] = degree_count.get(e["source"], 0) + 1
        degree_count[e["target"]] = degree_count.get(e["target"], 0) + 1

    node_map = {n["id"]: n for n in nodes}
    god_nodes = []
    for nid, degree in sorted(degree_count.items(), key=lambda x: -x[1])[:limit]:
        n = node_map.get(nid, {"id": nid, "label": nid, "type": "unknown"})
        god_nodes.append({
            "id": nid,
            "label": n.get("label", nid),
            "type": n.get("type", "unknown"),
            "project": n.get("project", ""),
            "degree": degree,
        })

    return {
        "ok": True,
        "god_nodes": god_nodes,
        "total": len(god_nodes),
    }


@mcp.tool()
def graph_community_universe(project: str = "") -> dict:
    """全宇宙社区检测（按项目聚合）。

    Returns combined community data across all projects.
    """
    config = _load_universe_config()
    excluded = set(config.get("excluded_projects", []))

    all_communities = {}
    all_cohesion = {}
    project_count = 0

    for proj in project_registry.list_projects():
        if proj.slug in excluded:
            continue
        result = graph_community(project=proj.slug)
        if result.get("communities"):
            # Prefix community IDs with project slug
            for cid, members in result["communities"].items():
                prefixed_cid = f"{proj.slug}/{cid}"
                all_communities[prefixed_cid] = [
                    f"{proj.slug}/{m}" for m in members
                ]
            for cid, cohesion in result.get("cohesion", {}).items():
                prefixed_cid = f"{proj.slug}/{cid}"
                all_cohesion[prefixed_cid] = cohesion
            project_count += 1

    return {
        "ok": True,
        "communities": all_communities,
        "cohesion": all_cohesion,
        "community_count": len(all_communities),
        "project_count": project_count,
    }


@mcp.tool()
def graph_shortest_path_universe(from_node: str, to_node: str, project: str = "") -> dict:
    """跨项目最短路径（BFS）。

    Args:
        from_node: 起始节点ID (格式: project/filename)
        to_node: 目标节点ID
    """
    from collections import deque

    universe_data = graph_universe()
    nodes = universe_data["nodes"]
    edges = universe_data["edges"]

    node_ids = {n["id"] for n in nodes}
    if from_node not in node_ids:
        return {"ok": False, "error": f"起始节点不存在: {from_node}"}
    if to_node not in node_ids:
        return {"ok": False, "error": f"目标节点不存在: {to_node}"}

    # Build adjacency
    adj: dict[str, list] = {}
    for e in edges:
        adj.setdefault(e["source"], []).append(e["target"])
        adj.setdefault(e["target"], []).append(e["source"])

    # BFS
    queue = deque([(from_node, [from_node])])
    visited = {from_node}

    while queue:
        current, path = queue.popleft()
        if current == to_node:
            return {
                "ok": True,
                "path": path,
                "hops": len(path) - 1,
                "from": from_node,
                "to": to_node,
            }
        for neighbor in adj.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return {
        "ok": False,
        "error": "无路径",
        "from": from_node,
        "to": to_node,
    }


@mcp.tool()
def graph_insights_universe(project: str = "") -> dict:
    """全宇宙洞察报告。

    Returns cross-project bridges, isolated pages across all projects,
    and suggestions.
    """
    universe_data = graph_universe()
    nodes = universe_data["nodes"]
    edges = universe_data["edges"]
    bridges = universe_data["bridges"]

    # Find isolated pages (degree 0)
    connected_ids = set()
    for e in edges:
        connected_ids.add(e["source"])
        connected_ids.add(e["target"])

    isolated = []
    for n in nodes:
        if n["id"] not in connected_ids:
            isolated.append({
                "id": n["id"],
                "label": n["label"],
                "type": n.get("type", "unknown"),
                "project": n.get("project", ""),
            })

    # Find cross-community bridges
    cross_project_edges = [
        e for e in edges
        if e.get("source", "").split("/")[0] != e.get("target", "").split("/")[0]
    ]

    return {
        "ok": True,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "bridges": bridges[:20],
        "isolated": isolated[:50],
        "isolated_count": len(isolated),
        "cross_project_edges": cross_project_edges[:20],
        "cross_project_edge_count": len(cross_project_edges),
        "suggestions": [
            f"发现 {len(bridges)} 个跨项目关联",
            f"发现 {len(isolated)} 个孤立页面需要链接",
            f"发现 {len(cross_project_edges)} 个跨项目连接",
        ],
    }


@mcp.tool()
def graph_suggest_bridges(limit: int = 10, project: str = "") -> dict:
    """智能推荐潜在的跨项目关联（虫洞）。

    基于标题相似度和标签重叠评分。
    """
    universe_data = graph_universe()
    bridges = universe_data.get("bridges", [])

    # Sort by similarity and return top N
    bridges.sort(key=lambda x: -x["similarity"])

    return {
        "ok": True,
        "suggestions": bridges[:limit],
        "total_available": len(bridges),
    }


@mcp.tool()
def graph_add_bridge(from_node: str, to_node: str, reason: str = "", project: str = "") -> dict:
    """手动创建跨项目关联。

    记录人工确认的虫洞连接。
    """
    config = _load_universe_config()
    manual_bridges = config.get("manual_bridges", [])

    bridge_entry = {
        "from_node": from_node,
        "to_node": to_node,
        "reason": reason or "手动添加",
        "created": datetime.now().isoformat(),
    }
    manual_bridges.append(bridge_entry)
    config["manual_bridges"] = manual_bridges
    _save_universe_config(config)

    return {
        "ok": True,
        "bridge": bridge_entry,
        "total_manual_bridges": len(manual_bridges),
    }


@mcp.tool()
def graph_export_universe(format: str = "json", project: str = "") -> dict:
    """导出完整宇宙数据。

    Args:
        format: "json" 或 "html"
    """
    universe_data = graph_universe()

    if format == "json":
        export_dir = REPO_ROOT / ".memex" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = export_dir / f"universe_{timestamp}.json"
        filepath.write_text(
            json.dumps(universe_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {
            "ok": True,
            "format": "json",
            "path": str(filepath.relative_to(REPO_ROOT)),
            "size": filepath.stat().st_size,
        }

    return {"ok": False, "error": f"Unsupported format: {format}. Use 'json'."}


# ─── entry point ─────────────────────────────────────────────────────────────


def main() -> None:
    """Run MCP server.

    Transport mode controlled via MEMEX_MCP_TRANSPORT env var:
    - "stdio" (default): used by `claude mcp add memex -- ...`
    - "http": HTTP mode with Streamable HTTP (SSE), used for remote/container deployment.
    """
    transport = os.environ.get("MEMEX_MCP_TRANSPORT", "stdio")
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "http":
        # FastMCP reads host/port from mcp.settings when using streamable-http transport
        mcp.settings.host = os.environ.get("MEMEX_MCP_HOST", "0.0.0.0")
        mcp.settings.port = int(os.environ.get("MEMEX_MCP_PORT", "8081"))
        mcp.run(transport="streamable-http")
    else:
        sys.stderr.write(f"Unknown transport: {transport}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
