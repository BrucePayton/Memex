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


class ProjectStorageError(RuntimeError):
    """Raised when a registered project cannot be safely used on disk."""


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
        d["health"] = project_health(self)
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

# ─── 프로젝트 설정 파일 ───

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
    )


def _entry_to_project(entry: dict) -> Project:
    slug = entry["slug"]
    root = PROJECTS_DIR / slug
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
        description=entry.get("description", ""),
        created=entry.get("created", ""),
        last_used=entry.get("last_used", ""),
        template=entry.get("template", ""),
    )


def _required_storage_paths(proj: Project) -> list[tuple[str, Path, str]]:
    """Required paths for a project to be considered usable storage."""
    if proj.is_legacy:
        return [
            ("root", proj.root, "dir"),
            ("wiki", proj.wiki_dir, "dir"),
            ("raw", proj.raw_dir, "dir"),
            ("CLAUDE.md", proj.claude_md, "file"),
        ]
    return [
        ("root", proj.root, "dir"),
        ("wiki", proj.wiki_dir, "dir"),
        ("wiki/index.md", proj.wiki_dir / "index.md", "file"),
        ("wiki/log.md", proj.wiki_dir / "log.md", "file"),
        ("raw", proj.raw_dir, "dir"),
        ("CLAUDE.md", proj.claude_md, "file"),
        (".settings.json", proj.settings_file, "file"),
    ]


def _path_missing(path: Path, expected: str) -> bool:
    if expected == "dir":
        return not path.is_dir()
    if expected == "file":
        return not path.is_file()
    return not path.exists()


def _rel_project_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def missing_storage_paths(proj: Project) -> list[str]:
    """Relative required paths missing for the project."""
    return [
        name
        for name, path, expected in _required_storage_paths(proj)
        if _path_missing(path, expected)
    ]


def project_health(proj: Project) -> dict:
    """Return non-persisted health metadata for API/UI diagnostics."""
    missing = missing_storage_paths(proj)
    if not missing:
        status = "ok"
    elif "root" in missing:
        status = "missing_on_disk"
    else:
        status = "incomplete_on_disk"
    return {
        "status": status,
        "ok": status == "ok",
        "missing": missing,
    }


def require_project_storage(proj: Project) -> Project:
    """Validate that a project has the required on-disk structure."""
    health = project_health(proj)
    if health["ok"]:
        return proj
    missing = ", ".join(health["missing"])
    raise ProjectStorageError(
        f"Project storage {health['status']}: {proj.slug or '(legacy)'}"
        + (f" (missing: {missing})" if missing else "")
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


def get_project(slug: str | None = None, *, require_storage: bool = False) -> Project:
    """Get project by slug. Returns legacy project if missing or projects.json is empty.

    Args:
        slug: specific project slug. If None, uses active. Falls back to legacy.
        require_storage: if True, validate required on-disk paths before returning.
    """
    reg = _load_registry()
    projects = reg.get("projects", [])
    if not projects:
        # projects.json empty -> legacy
        proj = _legacy_project()
        return require_project_storage(proj) if require_storage else proj

    target = slug or reg.get("active")
    if not target:
        # active unspecified but projects exist -> fallback to first
        proj = _entry_to_project(projects[0])
        return require_project_storage(proj) if require_storage else proj

    for e in projects:
        if e.get("slug") == target:
            proj = _entry_to_project(e)
            return require_project_storage(proj) if require_storage else proj

    # slug mismatch -> exception instead of silent legacy fallback
    raise KeyError(f"Project not found: {target}")


def _direct_project_dirs() -> list[Path]:
    if not PROJECTS_DIR.is_dir():
        return []
    return [
        p for p in sorted(PROJECTS_DIR.iterdir())
        if p.is_dir() and not p.name.startswith(".")
    ]


def _dir_has_files(path: Path) -> bool:
    if not path.exists():
        return False
    return any(p.is_file() for p in path.rglob("*"))


def _unique_trash_dest(slug: str) -> Path:
    trash = PROJECTS_DIR / ".trash"
    trash.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    dest = trash / f"{slug}-{ts}"
    n = 0
    while dest.exists():
        n += 1
        dest = trash / f"{slug}-{ts}-{n}"
    return dest


def reconcile_projects(apply: bool = False) -> dict:
    """Inspect registry/disk drift and optionally move empty orphan dirs to trash.

    This never deletes data. Only orphan directories with no files are moved when
    apply=True; missing registered projects and non-empty orphans are reported.
    """
    reg = _load_registry()
    entries = reg.get("projects", [])
    registered = {e.get("slug") for e in entries if e.get("slug")}

    missing_on_disk: list[dict] = []
    incomplete_on_disk: list[dict] = []
    for e in entries:
        proj = _entry_to_project(e)
        health = project_health(proj)
        item = {
            "slug": proj.slug,
            "title": proj.title,
            "root": _rel_project_path(proj.root),
            "missing": health["missing"],
        }
        if health["status"] == "missing_on_disk":
            missing_on_disk.append(item)
        elif health["status"] == "incomplete_on_disk":
            incomplete_on_disk.append(item)

    orphan_on_disk: list[dict] = []
    moved: list[dict] = []
    for child in _direct_project_dirs():
        if child.name in registered:
            continue
        has_files = _dir_has_files(child)
        item = {
            "slug": child.name,
            "root": _rel_project_path(child),
            "empty": not has_files,
            "action": "move_to_trash" if not has_files else "report_only",
        }
        if apply and not has_files:
            dest = _unique_trash_dest(f"orphan-{child.name}")
            shutil.move(str(child), str(dest))
            item["moved_to"] = _rel_project_path(dest)
            moved.append(item)
        else:
            orphan_on_disk.append(item)

    return {
        "ok": True,
        "dry_run": not apply,
        "missing_on_disk": missing_on_disk,
        "incomplete_on_disk": incomplete_on_disk,
        "orphan_on_disk": orphan_on_disk,
        "moved": moved,
    }


# ─── CRUD ───

# Recommended wiki/ sub-folders per template. Auto-scaffolded on Create project.
# Keys are templates/ directory names and "" (generic).
TEMPLATE_FOLDERS: dict[str, list[str]] = {
    "": ["sources", "entities", "concepts", "techniques", "analyses"],
    "llm-research": ["sources", "models", "techniques", "concepts", "entities", "benchmarks", "analyses"],
    "reading-log": ["sources", "authors", "ideas", "quotes", "reviews"],
    "personal-notes": ["daily", "topics", "people", "projects"],
    "process-knowledge": ["org", "rules", "metrics", "concepts", "steps"],
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

def create_project(
    slug_hint: str,
    title: str,
    description: str = "",
    template: str = "",
) -> Project:
    """Create new project.

    - slug_hint → make_slug → 중복 체크
    - projects/<slug>/ 디렉터리 + 기본 파일 생성
    - projects.json에 등록, active로 설정
    """
    if not title or not title.strip():
        raise ValueError("title is required")
    slug = make_slug(slug_hint or title)
    if not slug:
        raise ValueError("invalid slug")
    reg = _load_registry()
    for e in reg.get("projects", []):
        if e.get("slug") == slug:
            raise ValueError(f"slug already exists: {slug}")

    # process-knowledge uniqueness: same process name cannot create duplicate project
    if template == "process-knowledge":
        for e in reg.get("projects", []):
            existing_title = (e.get("title") or "").lower().strip()
            if existing_title == title.lower().strip():
                raise ValueError(
                    f"Process [{title}] already exists in project [{e['slug']}] "
                    f"(created {e.get('created', 'unknown')}). "
                    f"Please use the existing project or change the process name."
                )

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
    _save_project_settings(root / ".settings.json", {})

    # empty query-log
    (root / "query-log.jsonl").write_text("", encoding="utf-8")

    # update registry
    entry = {
        "slug": slug,
        "title": title,
        "description": description,
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


def update_project_settings(slug: str, *, title: str | None = None, description: str | None = None) -> Project:
    reg = _load_registry()
    projects = reg.get("projects", [])
    for e in projects:
        if e.get("slug") == slug:
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
    dest = None
    if src.exists():
        # shutil.move places src inside an existing directory, so dest must be unique.
        dest = _unique_trash_dest(slug)
        shutil.move(str(src), str(dest))

    reg["projects"] = [e for e in projects if e.get("slug") != slug]
    if reg.get("active") == slug:
        reg["active"] = reg["projects"][0]["slug"] if reg["projects"] else None
    _save_registry(reg)
    out = {"ok": True, "moved_to": _rel_project_path(dest) if dest else None}
    if dest is None:
        out["warning"] = f"projects/{slug} was already missing on disk; registry entry removed"
    return out
