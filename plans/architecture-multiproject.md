---
title: "Architecture — Multi-project Repository Layout"
created: 2026-04-23
status: draft
owner: yoo
scope: MP-01
---

# Multi-Project Architecture (MP-01)

## 1. Goal

Isolate the current root-fixed single wiki (`wiki/`, `raw/`, `CLAUDE.md`) under `projects/<slug>/`
so that one dashboard can selectively operate independent wikis for multiple topics.

Principles:

- **Isolation**: One project's ingest/query/lint must not read or write another project's data.
- **Single process**: One server. Project switching is a state change (layer switch), not a process restart.
- **Backward compatibility (Legacy mode)**: Server works before migration. If `projects.json` is absent, the current root `wiki/raw/` is treated as the "default" project.
- **git continuity**: File moves use `git mv`. History preserved.

---

## 2. Directory Tree (Goal State)

```
.
├── projects/
│   ├── karpathy-llm/                    <- Current wiki after migration
│   │   ├── CLAUDE.md                    (Per-project schema)
│   │   ├── .settings.json               (Per-project model etc.)
│   │   ├── raw/                         (immutable)
│   │   │   └── assets/
│   │   ├── wiki/
│   │   │   ├── index.md
│   │   │   ├── log.md
│   │   │   ├── overview.md
│   │   │   ├── sources/                 (MP-09 recommended folders)
│   │   │   ├── entities/
│   │   │   ├── concepts/
│   │   │   ├── techniques/
│   │   │   └── analyses/
│   │   ├── ingest-reports/
│   │   ├── reflect-reports/
│   │   ├── plans/
│   │   │   ├── today-queue.md
│   │   │   ├── backlog.md
│   │   │   └── blocked.md
│   │   └── query-log.jsonl
│   └── <future-project>/
│       └── ... (same structure)
├── projects.json                        <- Project Registry (maintained at root)
├── templates/
│   └── CLAUDE.md                        <- Starter schema (populated in MP-06)
├── dashboard/                           <- UI Server (project-agnostic)
├── logs/                                <- Autonomous mode session logs (maintained at root)
├── plans/                               <- Multi-project migration plans (move to projects/karpathy-llm/plans/ after migration)
├── CLAUDE.md                            <- Root schema (common rules only)
├── README.md                            <- Project-agnostic documentation
└── .obsidian/                           <- Root vault configuration
```

### What stays at root vs moves to project scope

| Item | Location | Rationale |
|------|----------|-----------|
| `dashboard/` | root | Single server. Project switch. |
| `projects.json` | root | Registry file (project list, active) |
| `templates/` | root | Clone source for new project creation |
| `logs/` | root | Autonomous mode session logs are server-level operation records |
| `.obsidian/` | root | One Obsidian vault browses all projects (Q-2 undecided) |
| `.gitignore` | root | repo-level |
| `README.md` | root | Project-agnostic introduction |
| `CLAUDE.md` | root | Common rules (lower priority than project CLAUDE.md) |
| `wiki/`, `raw/`, `ingest-reports/`, `reflect-reports/`, `query-log.jsonl` | project | Content |
| `.dashboard-settings.json` | **Delete** -> distribute to `projects/<slug>/.settings.json` | |
| Per-project `plans/` | project | Per-project work queue |

### Pre-migration (legacy mode) behavior

- If `projects.json` file is absent, the server is considered in "legacy" state.
- `get_project(name=None)` -> returns legacy path (current `wiki/ raw/ CLAUDE.md`) if `name` is absent.
- Dashboard header shows "Project: (legacy)" + migration prompt button.

---

## 3. `projects.json` Schema

```json
{
  "version": 1,
  "active": "karpathy-llm",
  "projects": [
    {
      "slug": "karpathy-llm",
      "title": "Karpathy LLM Wiki",
      "description": "Andrej Karpathy-related LLM material collection",
      "model": "claude-opus-4-7",
      "created": "2026-04-22",
      "last_used": "2026-04-23",
      "template": "llm-research"
    }
  ]
}
```

Field rules:
- `slug` — `make_slug()` result. Alphanumeric + hyphen + unicode (CJK) allowed. No duplicates. Directory name.
- `active` — Currently selected project slug. If absent, legacy.
- `model` — One of `AVAILABLE_MODELS` ids. Synced with project `.settings.json`.
- `template` — Template variant name cloned on creation (MP-06).

---

## 4. Resolver API (Implemented in MP-03)

### 4.1 Core Functions

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Project:
    slug: str                 # "karpathy-llm" | "" (legacy)
    is_legacy: bool           # True when projects.json absent
    root: Path                # projects/<slug>/ or PROJECT_ROOT
    wiki_dir: Path            # <root>/wiki
    raw_dir: Path             # <root>/raw
    claude_md: Path           # <root>/CLAUDE.md
    settings_file: Path       # <root>/.settings.json (legacy: PROJECT_ROOT/.dashboard-settings.json)
    ingest_reports: Path
    reflect_reports: Path
    plans_dir: Path
    query_log: Path
    title: str
    model: str                # Current model
```

```python
def list_projects() -> list[dict]: ...          # Parse projects.json
def get_active_slug() -> str | None: ...
def get_project(slug: str | None = None) -> Project: ...
def create_project(slug: str, title: str, description: str, model: str, template: str) -> Project: ...
def switch_project(slug: str) -> Project: ...
def delete_project(slug: str, confirm: bool) -> dict: ...
def update_project_settings(slug: str, **fields) -> Project: ...
```

### 4.2 Endpoint Scoping Rules

- All existing endpoints accept `project` field in body/query.
- If omitted, use `get_active_slug()`. If no active and legacy, use legacy path.
- Echo `project: <slug>` in response.

### 4.3 `run_claude(...)` Signature Change

- `cwd=str(PROJECT_ROOT)` -> changed to `cwd=str(project.root)`.
- Model args resolved from `project.model` (no longer global SETTINGS).
- Use `project.claude_md` path when reading `CLAUDE.md`.

### 4.4 git Policy

- **Single repo maintained (Option A, Q-1 default)**. Per-project subdirectory commits.
- `GitManager._stage_all()` -> `add projects/<slug>/wiki/ projects/<slug>/raw/ projects/<slug>/ingest-reports/`
- Commit message prefix includes project slug: `ingest(karpathy-llm): <title>`
- Branch strategy unchanged — all work on feature branches.

### 4.5 Safeguards

- `assert_writable(path)` — raw/ immutability applies to **all project raw/ directories** (not just current project).
- `assert_raw_create_only(path)` — Same extension.
- Cross-project-boundary path access (`../`) rejected at resolver level.

---

## 5. Migration Steps (Executed in MP-04, autonomous mode prohibited)

1. `git mv wiki projects/karpathy-llm/wiki`
2. `git mv raw projects/karpathy-llm/raw`
3. `git mv ingest-reports projects/karpathy-llm/ingest-reports`
4. `git mv reflect-reports projects/karpathy-llm/reflect-reports`
5. `git mv query-log.jsonl projects/karpathy-llm/query-log.jsonl`
6. `git mv CLAUDE.md projects/karpathy-llm/CLAUDE.md` — create new thin `CLAUDE.md` at root (common rules + reference to projects/<slug>/CLAUDE.md)
7. Convert `.dashboard-settings.json` -> `projects/karpathy-llm/.settings.json`, delete original
8. Create new `projects.json` (active: "karpathy-llm")
9. Update `README.md` path examples
10. Single smoke test (restart server -> `/api/projects` -> `/api/wiki?project=karpathy-llm`)

---

## 6. Open Items (see `plans/blocked.md`)

- Q-1 Single repo vs Per-project repo -> This document assumes **Option A (single repo)**.
- Q-2 Obsidian vault scope -> Currently maintain root vault, per-project separation is separate work.
- Q-3 Slug rules -> Reuse `make_slug()` + duplicate check.
- Q-4 Delete policy -> Move to `projects/.trash/<slug>-<ts>/` (hard delete option requires `confirm=hard`).

---

## 7. Implementation Phase Checklist (derived from this design)

- [ ] MP-02: Create `projects/` directory + `projects.json` initial file + `templates/CLAUDE.md` stubs
- [ ] MP-03: resolver + legacy fallback + add at least 1 endpoint (`/api/projects`) + in-process smoke test
- [ ] MP-04 (blocked): Move legacy content — user approval needed
- [ ] MP-05~MP-10: See parent plan
