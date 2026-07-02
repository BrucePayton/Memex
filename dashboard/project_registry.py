"""project_registry.py — Multi-Project Registry/resolver.

- projects.json read/write
- Project dataclass
- legacy mode support (if projects.json is missing or empty, current root wiki/raw is treated as default)
- all paths converted to absolute paths relative to PROJECT_ROOT
"""

from __future__ import annotations

import json
import re
import shutil
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

# Pin PROJECT_ROOT at module load time
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_FILE = PROJECT_ROOT / "projects.json"
PROJECTS_DIR = PROJECT_ROOT / "projects"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# legacy paths (current layout before migration)
LEGACY_WIKI = PROJECT_ROOT / "wiki"
LEGACY_RAW = PROJECT_ROOT / "raw"
LEGACY_CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"
LEGACY_SETTINGS = PROJECT_ROOT / ".dashboard-settings.json"
LEGACY_INGEST_REPORTS = PROJECT_ROOT / "ingest-reports"
LEGACY_REFLECT_REPORTS = PROJECT_ROOT / "reflect-reports"
LEGACY_QUERY_LOG = PROJECT_ROOT / "query-log.jsonl"
LEGACY_PLANS = PROJECT_ROOT / "plans"


@dataclass(frozen=True)
class Project:
    slug: str                  # "" for legacy
    title: str
    is_legacy: bool
    root: Path                 # projects/<slug>/ or PROJECT_ROOT
    wiki_dir: Path
    raw_dir: Path
    claude_md: Path
    settings_file: Path
    ingest_reports: Path
    reflect_reports: Path
    plans_dir: Path
    query_log: Path
    model: str = "default"
    description: str = ""
    created: str = ""
    last_used: str = ""
    template: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        # Path → str for JSON
        for k, v in list(d.items()):
            if isinstance(v, Path):
                d[k] = str(v.relative_to(PROJECT_ROOT)) if v.is_relative_to(PROJECT_ROOT) else str(v)
        return d


# ─── registry I/O ───

def _default_registry() -> dict:
    return {"version": 1, "active": None, "projects": []}


def _load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return _default_registry()
    try:
        data = json.loads(REGISTRY_FILE.read_text("utf-8"))
        if not isinstance(data, dict):
            return _default_registry()
        data.setdefault("version", 1)
        data.setdefault("active", None)
        data.setdefault("projects", [])
        return data
    except Exception:
        return _default_registry()


def _save_registry(reg: dict) -> None:
    REGISTRY_FILE.write_text(
        json.dumps(reg, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


from dashboard.models import make_slug

# --- Project settings file (model etc.) ---

def _load_project_settings(settings_path: Path) -> dict:
    if not settings_path.exists():
        return {}
    try:
        return json.loads(settings_path.read_text("utf-8")) or {}
    except Exception:
        return {}


def _save_project_settings(settings_path: Path, settings: dict) -> None:
    settings_path.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# --- Project instantiation ---

def _legacy_project() -> Project:
    settings = _load_project_settings(LEGACY_SETTINGS)
    return Project(
        slug="",
        title="(legacy)",
        is_legacy=True,
        root=PROJECT_ROOT,
        wiki_dir=LEGACY_WIKI,
        raw_dir=LEGACY_RAW,
        claude_md=LEGACY_CLAUDE_MD,
        settings_file=LEGACY_SETTINGS,
        ingest_reports=LEGACY_INGEST_REPORTS,
        reflect_reports=LEGACY_REFLECT_REPORTS,
        plans_dir=LEGACY_PLANS,
        query_log=LEGACY_QUERY_LOG,
        model=settings.get("model", "default"),
    )


def _entry_to_project(entry: dict) -> Project:
    slug = entry["slug"]
    root = PROJECTS_DIR / slug
    settings = _load_project_settings(root / ".settings.json")
    # model priority: .settings.json > registry entry > default
    model = settings.get("model") or entry.get("model") or "default"
    return Project(
        slug=slug,
        title=entry.get("title", slug),
        is_legacy=False,
        root=root,
        wiki_dir=root / "wiki",
        raw_dir=root / "raw",
        claude_md=root / "CLAUDE.md",
        settings_file=root / ".settings.json",
        ingest_reports=root / "ingest-reports",
        reflect_reports=root / "reflect-reports",
        plans_dir=root / "plans",
        query_log=root / "query-log.jsonl",
        model=model,
        description=entry.get("description", ""),
        created=entry.get("created", ""),
        last_used=entry.get("last_used", ""),
        template=entry.get("template", ""),
    )


def all_raw_dirs() -> list[Path]:
    """All raw/ paths (legacy + each project). Used for write-protection checks."""
    out = [LEGACY_RAW]
    if PROJECTS_DIR.exists():
        for p in PROJECTS_DIR.iterdir():
            if p.is_dir() and not p.name.startswith("."):
                out.append(p / "raw")
    return out


def is_protected_raw(path: Path | str) -> bool:
    """True if given path is inside any raw/ (immutable protection target)."""
    s = str(Path(path).absolute())
    for r in all_raw_dirs():
        rs = str(r.absolute())
        if s == rs or s.startswith(rs + "/"):
            return True
    return False


def list_projects() -> list[Project]:
    reg = _load_registry()
    return [_entry_to_project(e) for e in reg.get("projects", [])]


def get_active_slug() -> str | None:
    reg = _load_registry()
    return reg.get("active")


def has_projects() -> bool:
    reg = _load_registry()
    return bool(reg.get("projects"))


def get_project(slug: str | None = None) -> Project:
    """Get project by slug. Returns legacy project if missing or projects.json is empty.

    Args:
        slug: specific project slug. If None, uses active. Falls back to legacy.
    """
    reg = _load_registry()
    projects = reg.get("projects", [])
    if not projects:
        # projects.json empty -> legacy
        return _legacy_project()

    target = slug or reg.get("active")
    if not target:
        # active unspecified but projects exist -> fallback to first
        return _entry_to_project(projects[0])

    for e in projects:
        if e.get("slug") == target:
            return _entry_to_project(e)

    # slug mismatch -> exception instead of silent legacy fallback
    raise KeyError(f"Project not found: {target}")


# ─── CRUD ───

# Recommended wiki/ sub-folders per template. Auto-scaffolded on Create project.
# Keys are templates/ directory names and "" (generic).
TEMPLATE_FOLDERS: dict[str, list[str]] = {
    "": ["sources", "entities", "concepts", "techniques", "analyses"],
    "llm-research": ["sources", "models", "techniques", "concepts", "entities", "benchmarks", "analyses"],
    "reading-log": ["sources", "authors", "ideas", "quotes", "reviews"],
    "personal-notes": ["daily", "topics", "people", "projects"],
}


def recommended_folders(template_name: str) -> list[str]:
    """Recommended folder list for the given template."""
    return TEMPLATE_FOLDERS.get(template_name or "", TEMPLATE_FOLDERS[""])


def list_template_names() -> list[str]:
    """Only directories directly under `templates/` that contain CLAUDE.md are allowed."""
    if not TEMPLATES_DIR.is_dir():
        return []
    out = []
    for child in TEMPLATES_DIR.iterdir():
        if not child.is_dir() or child.name.startswith("."):
            continue
        if (child / "CLAUDE.md").is_file():
            out.append(child.name)
    return sorted(out)


def _copy_template(template_name: str, dest: Path) -> None:
    """templates/<name>/copy templates/<name>/CLAUDE.md to dest/CLAUDE.md. Falls back to generic if missing.

    Security: template_name must be in `list_template_names()` whitelist + no slashes/dots.
    traversal attempts (`../foo`, `a/b` etc.) are downgraded to generic fallback.

    placeholder {{TOPIC}} {{PURPOSE}} replaced in create_project.
    """
    generic = TEMPLATES_DIR / "CLAUDE.md"

    safe_name = (template_name or "").strip()
    allowed = set(list_template_names())
    bad = ("/" in safe_name) or ("\\" in safe_name) or (".." in safe_name) or safe_name.startswith(".")
    if not safe_name or bad or safe_name not in allowed:
        # generic fallback (templates/CLAUDE.md)
        src_file = generic
    else:
        candidate = TEMPLATES_DIR / safe_name / "CLAUDE.md"
        # re-verify under TEMPLATES_DIR after resolve (defense against symlinks etc.)
        try:
            resolved = candidate.resolve(strict=True)
            if not str(resolved).startswith(str(TEMPLATES_DIR.resolve()) + "/"):
                src_file = generic
            else:
                src_file = resolved
        except FileNotFoundError:
            src_file = generic

    if not src_file.is_file():
        # if even generic is missing, minimal stub
        dest.write_text("# Wiki\n\n(no template available)\n", encoding="utf-8")
        return
    dest.write_text(src_file.read_text("utf-8"), encoding="utf-8")


# model validation hook injected from server.py. Default passes (legacy compat).
# Return True to allow, False to deny.
_model_validator = lambda m: True  # noqa: E731


def set_model_validator(fn) -> None:
    """Inject model allowlist validator (to avoid circular import with server)."""
    global _model_validator
    _model_validator = fn


def create_project(
    slug_hint: str,
    title: str,
    description: str = "",
    model: str = "default",
    template: str = "",
) -> Project:
    """Create new project.

    - slug_hint -> make_slug -> duplicate check
    - model must pass validator injected via `set_model_validator`
    - create projects/<slug>/ directory + default files
    - register in projects.json, set as active
    """
    if not title or not title.strip():
        raise ValueError("title is required")
    slug = make_slug(slug_hint or title)
    if not slug:
        raise ValueError("invalid slug")
    if not _model_validator(model):
        raise ValueError(f"invalid model: {model!r}")

    reg = _load_registry()
    for e in reg.get("projects", []):
        if e.get("slug") == slug:
            raise ValueError(f"slug already exists: {slug}")

    root = PROJECTS_DIR / slug
    if root.exists():
        raise ValueError(f"projects/{slug} already exists on disk")
    root.mkdir(parents=True)
    (root / "wiki").mkdir()
    (root / "raw").mkdir()
    (root / "raw" / "assets").mkdir()
    (root / "ingest-reports").mkdir()
    (root / "reflect-reports").mkdir()
    (root / "plans").mkdir()

    # template recommended folder scaffold. Falls back to generic if template not in whitelist.
    tmpl_key = template if template in list_template_names() else ""
    for folder in recommended_folders(tmpl_key):
        (root / "wiki" / folder).mkdir(exist_ok=True)

    # starter wiki files (minimal)
    today = datetime.now().strftime("%Y-%m-%d")
    (root / "wiki" / "index.md").write_text(
        f"# {title} — Index\n\n## Sources\n\n## Entities\n\n## Concepts\n\n## Techniques\n\n## Analyses\n",
        encoding="utf-8",
    )
    (root / "wiki" / "log.md").write_text(
        f"# {title} — Activity Log\n\n## [{today}] init | {title}\nProject created.\n",
        encoding="utf-8",
    )
    (root / "wiki" / "overview.md").write_text(
        f"---\ntitle: \"{title}\"\ntype: overview\ncreated: {today}\nlast_updated: {today}\n---\n\n# {title}\n\n{description}\n",
        encoding="utf-8",
    )

    # copy CLAUDE.md template
    _copy_template(template or "", root / "CLAUDE.md")
    content = (root / "CLAUDE.md").read_text("utf-8")
    content = content.replace("{{TOPIC}}", title).replace("{{PURPOSE}}", description or "")
    (root / "CLAUDE.md").write_text(content, encoding="utf-8")

    # .settings.json
    _save_project_settings(root / ".settings.json", {"model": model})

    # empty query-log
    (root / "query-log.jsonl").write_text("", encoding="utf-8")

    # update registry
    entry = {
        "slug": slug,
        "title": title,
        "description": description,
        "model": model,
        "created": today,
        "last_used": today,
        "template": template or "",
    }
    reg.setdefault("projects", []).append(entry)
    reg["active"] = slug
    _save_registry(reg)

    return _entry_to_project(entry)


def switch_project(slug: str) -> Project:
    reg = _load_registry()
    projects = reg.get("projects", [])
    for e in projects:
        if e.get("slug") == slug:
            reg["active"] = slug
            e["last_used"] = datetime.now().strftime("%Y-%m-%d")
            _save_registry(reg)
            return _entry_to_project(e)
    raise KeyError(f"Project not found: {slug}")


def update_project_settings(slug: str, *, model: str | None = None, title: str | None = None, description: str | None = None) -> Project:
    reg = _load_registry()
    projects = reg.get("projects", [])
    for e in projects:
        if e.get("slug") == slug:
            if model is not None:
                if not _model_validator(model):
                    raise ValueError(f"invalid model: {model!r}")
                e["model"] = model
                # sync with .settings.json
                sf = PROJECTS_DIR / slug / ".settings.json"
                s = _load_project_settings(sf)
                s["model"] = model
                _save_project_settings(sf, s)
            if title is not None:
                e["title"] = title
            if description is not None:
                e["description"] = description
            _save_registry(reg)
            return _entry_to_project(e)
    raise KeyError(f"Project not found: {slug}")


def delete_project(slug: str, confirm: bool = False) -> dict:
    """Delete project. Default: move to projects/.trash/<slug>-<ts>/ (soft delete).
    Runs only with confirm=True. 'hard' option not yet implemented.
    """
    if not confirm:
        return {"ok": False, "error": "confirm=True required"}
    reg = _load_registry()
    projects = reg.get("projects", [])
    entry = next((e for e in projects if e.get("slug") == slug), None)
    if not entry:
        return {"ok": False, "error": f"Project not found: {slug}"}

    src = PROJECTS_DIR / slug
    trash = PROJECTS_DIR / ".trash"
    trash.mkdir(exist_ok=True)
    # ms + counter on collision. shutil.move, if dest is an existing directory,
    # places src inside it, so a unique name must be ensured.
    ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    dest = trash / f"{slug}-{ts}"
    n = 0
    while dest.exists():
        n += 1
        dest = trash / f"{slug}-{ts}-{n}"
    shutil.move(str(src), str(dest))

    reg["projects"] = [e for e in projects if e.get("slug") != slug]
    if reg.get("active") == slug:
        reg["active"] = reg["projects"][0]["slug"] if reg["projects"] else None
    _save_registry(reg)
    return {"ok": True, "moved_to": str(dest.relative_to(PROJECT_ROOT))}
