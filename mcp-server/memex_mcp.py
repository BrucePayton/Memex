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

import asyncio
import json
import math
import os
import re
import subprocess
import sys
import urllib.error
from collections import defaultdict, deque
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

# ─── locate repo + bring dashboard/ onto sys.path ────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = REPO_ROOT / "dashboard"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
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
        "wiki maintenance tasks. "
        "Graph path tools: `graph_path_with_content` (single project) and "
        "`graph_path_universe_with_content` (cross-project) return the shortest "
        "path between two wiki pages with the full content of each page along "
        "the path. Use these to gather context before answering user questions."
    ),
)

# ─── small helpers (now imported from shared dashboard.models) ──────

from dashboard.models import (
    FRONTMATTER_RE, WIKILINK_RE, parse_fm, extract_links, extract_citations,
    make_slug, is_system_page, SYSTEM_PAGES,
)

WORD_RE = re.compile(r"[\w]+")


# parse_fm, extract_links now imported from dashboard.models above


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


# ─── HTTP async call layer (all graph tools call dashboard API) ──────────────

def _dashboard_base_url() -> str:
    """Get dashboard base URL from env or default."""
    return os.environ.get("MEMEX_DASHBOARD_URL", "http://localhost:8000")


async def _api_call(path: str, params: dict | None = None, method: str = "GET", body: dict | None = None) -> dict:
    """Call dashboard API over HTTP asynchronously."""
    url = _dashboard_base_url() + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    loop = asyncio.get_event_loop()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return await loop.run_in_executor(None, json.loads, raw)
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode()
        except Exception:
            pass
        return {"ok": False, "error": f"HTTP {e.code}: {err_body}"}
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"Connection failed: {e.reason}"}


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

    try:
        data = json.loads(graph_file.read_text(encoding="utf-8"))
        if labels_file.exists():
            data["community_labels"] = json.loads(labels_file.read_text(encoding="utf-8"))
        return data
    except Exception:
        return None

def _persist_graph(proj, graph_data):
    """Persist graph data to .graph directory."""
    graph_dir = _get_graph_dir(proj)

    # Save main graph
    graph_file = graph_dir / "graph.json"
    graph_file.write_text(json.dumps(graph_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Save community labels separately if present
    if "community_labels" in graph_data:
        labels_file = graph_dir / "community_labels.json"
        labels_file.write_text(json.dumps(graph_data["community_labels"], ensure_ascii=False, indent=2), encoding="utf-8")


def _build_wiki_graph(proj) -> tuple[list[dict], list[dict]]:
    """Scan wiki/ and build a simple {nodes, edges} graph from wikilinks.

    Delegates to shared dashboard.graph.builder to avoid code duplication.
    """
    from dashboard.graph.builder import build_graph_data

    nodes, edges, _node_map = build_graph_data(proj.wiki_dir, proj.raw_dir)

    # Convert to the format expected by MCP graph tools:
    # nodes: [{id, label, type, word_count, tags}]
    # edges: [{from, to}]
    graph_nodes = [
        {"id": n["filename"], "label": n["title"], "type": n["type"],
         "word_count": n.get("word_count", 0), "tags": n.get("tags", [])}
        for n in nodes
    ]
    graph_edges = [{"from": e["from"], "to": e["to"]} for e in edges]

    return graph_nodes, graph_edges


# ─── graph tools (HTTP async calls to dashboard API) ─────────────────────────


@mcp.tool()
async def graph_build(project: str = "") -> dict:
    """Build a knowledge graph from wiki pages.

    Scans wiki/ directory, parses wikilinks [[...]], and returns nodes + edges.
    Uses shared graph/builder.py directly — no HTTP dependency on Dashboard.
    """
    from dashboard.graph.builder import build_graph_data
    proj = _resolve(project)
    nodes, edges, _node_map = build_graph_data(proj.wiki_dir, proj.raw_dir)
    return {
        "project": proj.slug,
        "nodes": [{"id": n["filename"], "label": n["title"], "type": n["type"],
                   "word_count": n.get("word_count", 0), "tags": n.get("tags", [])} for n in nodes],
        "edges": edges,
    }


@mcp.tool()
async def graph_community(project: str = "") -> dict:
    """Detect communities in the wiki graph using connected components."""
    from dashboard.graph.community import detect_communities
    proj = _resolve(project)
    result = detect_communities(proj.wiki_dir)
    result["project"] = proj.slug
    return result


@mcp.tool()
async def graph_god_nodes(project: str = "", top_n: int = 10) -> dict:
    """Return the most-connected wiki pages (highest degree)."""
    from dashboard.graph.paths import god_nodes
    proj = _resolve(project)
    result = god_nodes(proj.wiki_dir, top_n)
    result["project"] = proj.slug
    return result


@mcp.tool()
async def graph_stats(project: str = "") -> dict:
    """Return graph summary statistics (node/edge counts, density, etc.)."""
    from dashboard.graph.builder import build_graph_data
    proj = _resolve(project)
    nodes, edges, _ = build_graph_data(proj.wiki_dir, proj.raw_dir)
    sys_pages = SYSTEM_PAGES
    type_counts = {}
    for n in nodes:
        type_counts[n.get("type", "unknown")] = type_counts.get(n.get("type", "unknown"), 0) + 1
    degree = {n["filename"]: 0 for n in nodes if n["filename"] not in sys_pages}
    for e in edges:
        if e["from"] in degree: degree[e["from"]] += 1
        if e["to"] in degree: degree[e["to"]] += 1
    n_real = len(degree)
    avg_degree = round(sum(degree.values()) / n_real, 2) if n_real > 0 else 0
    max_possible = n_real * (n_real - 1) / 2 if n_real > 1 else 1
    density = round(len(edges) / max_possible, 4) if max_possible > 0 else 0
    isolated = sum(1 for d in degree.values() if d == 0)
    return {
        "project": proj.slug, "node_count": len(nodes), "edge_count": len(edges),
        "real_nodes": n_real, "type_counts": type_counts, "isolated_pages": isolated,
        "avg_degree": avg_degree, "density": density,
    }


@mcp.tool()
async def graph_shortest_path(source: str, target: str, project: str = "") -> dict:
    """Find the shortest path between two wiki pages (BFS)."""
    from dashboard.graph.paths import shortest_path
    proj = _resolve(project)
    return shortest_path(proj.wiki_dir, source, target)


@mcp.tool()
async def graph_neighbors(node_id: str, project: str = "") -> dict:
    """Return direct neighbors of a wiki page node."""
    from dashboard.graph.paths import neighbors as graph_neighbors_fn
    proj = _resolve(project)
    return graph_neighbors_fn(proj.wiki_dir, node_id)


@mcp.tool()
async def graph_insights(project: str = "") -> dict:
    """Discover interesting patterns in the wiki graph.

    Cross-type connections, bridge pages, isolated pages.
    """
    from dashboard.graph.builder import build_graph_data
    proj = _resolve(project)
    nodes, edges, node_map = build_graph_data(proj.wiki_dir, proj.raw_dir)
    sys_pages = SYSTEM_PAGES

    # Cross-type connections
    cross_type = []
    for e in edges:
        fnode = node_map.get(e["from"], {})
        tnode = node_map.get(e["to"], {})
        ft = fnode.get("type", "unknown") if isinstance(fnode, dict) else "unknown"
        tt = tnode.get("type", "unknown") if isinstance(tnode, dict) else "unknown"
        if ft != tt and ft != "unknown" and tt != "unknown":
            cross_type.append({"from": e["from"], "to": e["to"], "from_type": ft, "to_type": tt})

    # Isolated pages
    degree = {n["filename"]: 0 for n in nodes if n["filename"] not in sys_pages}
    for e in edges:
        if e["from"] in degree: degree[e["from"]] += 1
        if e["to"] in degree: degree[e["to"]] += 1
    isolated = [nid for nid, d in degree.items() if d == 0]

    return {
        "project": proj.slug,
        "cross_type_connections": len(cross_type),
        "isolated_pages": isolated,
        "isolated_count": len(isolated),
        "cross_type_examples": cross_type[:10],
    }


@mcp.tool()
async def graph_export(format: str = "json", project: str = "") -> dict:
    """Export the wiki knowledge graph as JSON or self-contained HTML."""
    params = {"format": format}
    if project:
        params["project"] = project
    return await _api_call("/api/graph/export", params=params)


# ─── resources: graph ────────────────────────────────────────────────────────


@mcp.resource("memex://graph/stats")
def resource_graph_stats() -> str:
    """Graph summary statistics as plain text."""
    result = asyncio.get_event_loop().run_until_complete(graph_stats(project=""))
    if not result.get("ok", True):
        return f"Error: {result.get('error', 'unknown')}"
    lines = [
        f"Nodes: {result.get('node_count', 'N/A')}",
        f"Edges: {result.get('edge_count', 'N/A')}",
        f"Real nodes: {result.get('real_nodes', 'N/A')}",
        f"Isolated pages: {result.get('isolated_pages', 'N/A')}",
        f"Average degree: {result.get('avg_degree', 'N/A')}",
        f"Graph density: {result.get('density', 'N/A')}",
        "Type distribution:",
    ]
    for t, c in sorted(result.get("type_counts", {}).items()):
        lines.append(f"  {t}: {c}")
    return "\n".join(lines)


@mcp.resource("memex://graph/god-nodes")
def resource_graph_god_nodes() -> str:
    """Top 10 most-connected wiki pages as plain text."""
    result = asyncio.get_event_loop().run_until_complete(graph_god_nodes(project="", top_n=10))
    if not result.get("ok", True):
        return f"Error: {result.get('error', 'unknown')}"
    lines = ["God nodes (most connected wiki pages):"]
    for i, n in enumerate(result.get("god_nodes", []), 1):
        lines.append(f"  {i}. {n['label']} — {n['degree']} connections ({n['type']})")
    return "\n".join(lines)


@mcp.resource("memex://graph/insights")
def resource_graph_insights() -> str:
    """Interesting patterns and suggestions as plain text."""
    result = asyncio.get_event_loop().run_until_complete(graph_insights(project=""))
    if not result.get("ok", True):
        return f"Error: {result.get('error', 'unknown')}"
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


# ─── enhanced graph tools (HTTP async calls) ─────────────────────────────────

@mcp.tool()
async def graph_composite(project: str = "") -> dict:
    """Get composite graph data (nodes + edges + communities + cohesion + labels)."""
    params = {}
    if project:
        params["project"] = project
    return await _api_call("/api/graph/composite", params=params)


@mcp.tool()
async def graph_rebuild(project: str = "") -> dict:
    """Rebuild and persist the graph (uses graphify if available)."""
    body = {}
    if project:
        body["project"] = project
    return await _api_call("/api/graph/rebuild", method="POST", body=body)


@mcp.tool()
async def graph_name_community(community_id: str, name: str, project: str = "") -> dict:
    """Set a human-readable name for a community."""
    body = {"community_id": community_id, "name": name}
    if project:
        body["project"] = project
    return await _api_call("/api/graph/name-community", method="POST", body=body)


@mcp.tool()
async def graph_get_community(community_id: str, project: str = "") -> dict:
    """Get detailed information about a specific community."""
    params = {"community_id": community_id}
    if project:
        params["project"] = project
    return await _api_call("/api/graph/get-community", params=params)


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

    # Group by normalized title
    title_map: dict[str, list] = defaultdict(list)
    for n in all_nodes:
        # Normalize: lowercase, strip common suffixes
        key = re.sub(r'[^a-z0-9]+', '', n["label"].lower())
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
async def graph_universe_config(config: dict = None, project: str = "") -> dict:
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
        return await _api_call("/api/graph/universe-config")
    body = config
    if project:
        body["project"] = project
    return await _api_call("/api/graph/universe-config", method="POST", body=body)


@mcp.tool()
async def graph_join_universe(slug: str, project: str = "") -> dict:
    """将项目加入知识宇宙。

    Args:
        slug: 要加入的项目slug
    """
    body = {"slug": slug}
    if project:
        body["project"] = project
    return await _api_call("/api/graph/join-universe", method="POST", body=body)


@mcp.tool()
async def graph_leave_universe(slug: str, project: str = "") -> dict:
    """将项目从知识宇宙中隐藏。

    Args:
        slug: 要隐藏的项目slug
    """
    body = {"slug": slug}
    if project:
        body["project"] = project
    return await _api_call("/api/graph/leave-universe", method="POST", body=body)


@mcp.tool()
async def graph_new_projects(project: str = "") -> dict:
    """检查是否有新加入的项目需要处理。

    Returns:
        {new: [slugs], pending: [...]}
    """
    params = {}
    if project:
        params["project"] = project
    return await _api_call("/api/graph/universe-changes", params=params)


@mcp.tool()
async def graph_universe(project_filter: list = None, project: str = "") -> dict:
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
    params = {}
    if project_filter:
        params["project"] = ",".join(project_filter)
    elif project:
        params["project"] = project
    return await _api_call("/api/graph/universe", params=params)


@mcp.tool()
async def graph_project(slug: str, project: str = "") -> dict:
    """获取单个项目的图谱。

    Args:
        slug: 项目slug
    """
    params = {"project": slug}
    return await _api_call("/api/graph/build", params=params)


@mcp.tool()
async def graph_bridges(min_similarity: float = 0.3, project: str = "") -> dict:
    """获取跨项目虫洞列表。

    Args:
        min_similarity: 最低相似度阈值
    """
    params = {"min_similarity": str(min_similarity)}
    if project:
        params["project"] = project
    return await _api_call("/api/graph/bridges", params=params)


@mcp.tool()
async def graph_search_universe(query: str, limit: int = 20, project: str = "") -> dict:
    """在知识宇宙中搜索节点。

    Args:
        query: 搜索关键词
        limit: 返回结果数量
    """
    universe_data = await graph_universe()
    nodes = universe_data["nodes"]

    results = []
    q_lower = query.lower()
    q_words = re.findall(r'[\w]+', q_lower)

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
async def graph_god_nodes_universe(limit: int = 20, project: str = "") -> dict:
    """全宇宙最重要的节点（按连接数排序）。

    Args:
        limit: 返回数量
    """
    universe_data = await graph_universe()
    nodes = universe_data["nodes"]
    edges = universe_data["edges"]

    # Count degree
    degree_count: dict[str, int] = {}
    for e in edges:
        degree_count[e["source"]] = degree_count.get(e["source"], 0) + 1
        degree_count[e["target"]] = degree_count.get(e["target"], 0) + 1

    node_map = {n["id"]: n for n in nodes}
    god_nodes_list = []
    for nid, degree in sorted(degree_count.items(), key=lambda x: -x[1])[:limit]:
        n = node_map.get(nid, {"id": nid, "label": nid, "type": "unknown"})
        god_nodes_list.append({
            "id": nid,
            "label": n.get("label", nid),
            "type": n.get("type", "unknown"),
            "project": n.get("project", ""),
            "degree": degree,
        })

    return {
        "ok": True,
        "god_nodes": god_nodes_list,
        "total": len(god_nodes_list),
    }


@mcp.tool()
async def graph_community_universe(project: str = "") -> dict:
    """全宇宙社区检测（按项目聚合）。

    Returns combined community data across all projects.
    """
    # Fetch universe data via API to get cross-project context
    universe_data = await graph_universe()

    # Call per-project community detection via API
    all_communities = {}
    all_cohesion = {}
    project_count = 0

    # Get projects from universe data
    projects = universe_data.get("universe", {}).get("projects", [])
    for proj_info in projects:
        slug = proj_info.get("slug", "")
        if not slug:
            continue
        result = await graph_community(project=slug)
        if result.get("communities"):
            for cid, members in result["communities"].items():
                prefixed_cid = f"{slug}/{cid}"
                all_communities[prefixed_cid] = [
                    f"{slug}/{m}" for m in members
                ]
            for cid, cohesion in result.get("cohesion", {}).items():
                prefixed_cid = f"{slug}/{cid}"
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
async def graph_shortest_path_universe(from_node: str, to_node: str, project: str = "") -> dict:
    """跨项目最短路径（BFS）。

    Args:
        from_node: 起始节点ID (格式: project/filename)
        to_node: 目标节点ID
    """
    universe_data = await graph_universe()
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
async def graph_insights_universe(project: str = "") -> dict:
    """全宇宙洞察报告。

    Returns cross-project bridges, isolated pages across all projects,
    and suggestions.
    """
    universe_data = await graph_universe()
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
async def graph_suggest_bridges(limit: int = 10, project: str = "") -> dict:
    """智能推荐潜在的跨项目关联（虫洞）。

    基于标题相似度和标签重叠评分。
    """
    universe_data = await graph_universe()
    bridges = universe_data.get("bridges", [])

    # Sort by similarity and return top N
    bridges.sort(key=lambda x: -x["similarity"])

    return {
        "ok": True,
        "suggestions": bridges[:limit],
        "total_available": len(bridges),
    }


@mcp.tool()
async def graph_path_with_content(source: str, target: str, project: str = "") -> dict:
    """获取项目内最短路径及其页面内容。

    在单个项目的知识图谱中找到两个节点之间的最短路径，
    并返回路径上每个wiki页面的内容摘要作为参考背景。

    Args:
        source: 起始节点（filename 或 title）
        target: 目标节点（filename 或 title）
        project: 项目slug（空=当前活动项目）

    Returns:
        {ok, path, hops, edges, content: [{filename, title, type, snippet, word_count, ...}]}
    """
    params = {"source": source, "target": target}
    if project:
        params["project"] = project
    return await _api_call("/api/graph/shortest-path-with-content", params=params)


@mcp.tool()
async def graph_path_universe_with_content(
    from_node: str = "",
    to_node: str = "",
    source_id: str = "",
    target_id: str = "",
) -> dict:
    """获取跨项目最短路径及其页面内容。

    在知识宇宙中找到两个节点之间的最短路径，
    并返回路径上每个wiki页面的内容摘要作为参考背景。
    支持跨项目的节点ID格式：project/filename.md

    Args:
        from_node: 起始节点ID（同 source_id，兼容旧参数名）
        to_node: 目标节点ID（同 target_id，兼容旧参数名）
        source_id: 起始节点ID（格式：project/filename.md）
        target_id: 目标节点ID（格式：project/filename.md）

    Returns:
        {ok, path, hops, edges, content: [{id, project, filename, title, type, snippet, word_count, ...}]}
    """
    sid = source_id or from_node
    tid = target_id or to_node
    params = {"source_id": sid, "target_id": tid}
    return await _api_call("/api/graph/universe-shortest-path-with-content", params=params)


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
async def graph_export_universe(format: str = "json", project: str = "") -> dict:
    """导出完整宇宙数据。

    Args:
        format: "json" 或 "html"
    """
    universe_data = await graph_universe()

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


@mcp.tool()
async def search_hybrid(query: str, project: str = "", top_k: int = 10, backend: str = "auto") -> dict:
    """混合语义搜索 — 自动选择最优搜索后端（TF-IDF / qmd / Hybrid RRF融合）。

    Args:
        query: 搜索查询（支持中英文）
        project: 项目 slug
        top_k: 返回结果数量
        backend: 搜索后端 (auto/tfidf/qmd/hybrid)
    """
    import sys as _sys
    _sys.path.insert(0, str(REPO_ROOT))

    from dashboard.search.engine import create_search_engine, TFIDFBackend

    proj = _resolve(project)

    if backend == "tfidf":
        engine = TFIDFBackend()
    else:
        try:
            engine = create_search_engine()
        except Exception:
            engine = TFIDFBackend()

    results = engine.search(query, proj.wiki_dir, top_k)

    return {
        "ok": True,
        "query": query,
        "backend": engine.name,
        "project": proj.slug,
        "total_results": len(results),
        "results": results,
    }


@mcp.tool()
async def okf_import(bundle_path: str, project: str = "", folder: str = "") -> dict:
    """导入 OKF (Open Knowledge Format) 知识包到 Memex wiki。

    Args:
        bundle_path: OKF bundle 目录的绝对路径
        project: 目标项目 slug
        folder: wiki 子目录（如 "concepts"）
    """
    import sys as _sys
    _sys.path.insert(0, str(REPO_ROOT))

    from pathlib import Path
    from dashboard.wiki_extensions import import_okf_bundle

    proj = _resolve(project)
    wiki_target = proj.wiki_dir / folder if folder else proj.wiki_dir
    wiki_target.mkdir(parents=True, exist_ok=True)

    imported = import_okf_bundle(Path(bundle_path), wiki_target)
    return {
        "ok": True,
        "imported_count": len(imported),
        "pages": imported,
    }


@mcp.tool()
async def okf_export(project: str = "", output_dir: str = "") -> dict:
    """导出 Memex wiki 为 OKF (Open Knowledge Format) 格式。

    Args:
        project: 源项目 slug
        output_dir: 输出目录路径
    """
    import sys as _sys
    _sys.path.insert(0, str(REPO_ROOT))

    from pathlib import Path
    from dashboard.wiki_extensions import export_to_okf

    proj = _resolve(project)
    out = Path(output_dir) if output_dir else REPO_ROOT / "okf-export"
    result = export_to_okf(proj.wiki_dir, out)
    return result


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
        # Disable DNS rebinding protection for nginx proxy deployment
        mcp.settings.transport_security.enable_dns_rebinding_protection = False
        mcp.settings.transport_security.allowed_hosts = ["*"]
        mcp.run(transport="streamable-http")
    else:
        sys.stderr.write(f"Unknown transport: {transport}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
