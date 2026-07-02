---
title: "Today Queue — Multi-project Architecture"
created: 2026-04-23
owner: yoo
---

# Today Queue — Multi-project Migration

Priority: consume from top to bottom. Each item is an independent commit.

---

## ~~[MP-01] Repository Layout Redesign~~ ✅ Done (2026-04-23)
- Result: `plans/architecture-multiproject.md`
- Commit: 8c0750d

---

## ~~[MP-02] `projects/` root + `projects.json` registry~~ ✅ Done (2026-04-23)
- Result: `projects/`, `projects.json`, `templates/{CLAUDE.md,llm-research,reading-log,personal-notes}`
- Commit: 18b0cd9

---

## ~~[MP-03] `server.py` project resolver (partial)~~ ⚠️ Foundation only (2026-04-23)
- Done: `dashboard/project_registry.py` module + `/api/projects*` endpoints + legacy fallback
- Commit: bcf7f32
- Remaining (transferred to MP-07): replace `WIKI_DIR`/`RAW_DIR` in do_ingest/do_query/do_lint etc. with resolver-based approach

---

## [MP-04] Legacy Content -> `projects/karpathy-llm/` Migration 🚨 BLOCKED
- Risk: high -> autonomous mode prohibited (section 21.8). User approval needed.
- See `plans/blocked.md` [BLOCK-MP-04]
- Impact scope: large-scale root directory move
- Done criteria:
  - Preserve history with `git mv`
  - Register `karpathy-llm` in `projects.json` + set active
  - Copy model value from `.dashboard-settings.json` to project `.settings.json`
  - Update path examples in root `README.md`
  - Verify dashboard works correctly after server restart

---

## ~~[MP-05] `/api/projects` CRUD Endpoints~~ ✅ Done (co-implemented with MP-03, 2026-04-23)

All items below completed in MP-03 commit (bcf7f32): `/api/projects`, `/api/projects/create`,
`/switch`, `/update`, `/delete`.

---

## [MP-05-archived] `/api/projects` CRUD Endpoints
- Goal: Project list/create/switch/delete API
- Impact scope: `server.py`
- Done criteria:
  - `GET /api/projects` -> list + active
  - `POST /api/projects` (name, description, model, template) -> new `projects/<slug>/` + starter CLAUDE.md + empty wiki/raw
  - `POST /api/projects/switch` (slug) -> update active
  - `POST /api/projects/delete` (slug, confirm) -> delete (move to trash recommended)
  - `POST /api/projects/<slug>/settings` (model) -> save per-project model
- Risk: medium

---

## [MP-06] Project Template CLAUDE.md
- Goal: Provide starter schema cloned on new project creation
- Impact scope: `templates/CLAUDE.md` new
- Done criteria:
  - General purpose (keep basic frontmatter/citation rules, remove domain examples)
  - 3-5 topic variants (llm-research / product-ops / personal-notes / reading-log) — selectable on creation
- Risk: low

---

## ~~[MP-07] Existing API Endpoint Project Scoping~~ ✅ Done (2026-04-23 ~ 2026-04-24)
- Partial (read): cb04d81 — `/api/wiki`, `/api/folders`, `/api/hash`, `/api/schema`, `/api/provenance`, `/api/index/status` accept `?project=<slug>`, unknown slug returns 404
- Full (write/Claude calls): 1f50ddb — all `do_*` + CRUD + `run_claude` cwd + GitManager + `assert_writable` fully scoped

---

## [MP-07-archived] Existing API Endpoint Project Scoping
- Goal: All endpoints accept project scope — `/api/ingest, /api/query, /api/lint, /api/lint/fix, /api/reflect, /api/write, /api/compare, /api/review/*, /api/search, /api/page*, /api/folder, /api/slides, /api/revert, /api/history, /api/provenance, /api/suggest/sources, /api/raw/integrity, /api/index/*, /api/schema, /api/wiki, /api/folders, /api/hash, /api/query-stats, /api/assistant`
- Impact scope: all handlers
- Done criteria:
  - Accept `project` field in body or querystring
  - Use active when omitted
  - Echo `project` in response
- Risk: medium

---

## ~~[MP-08] Header Project Selector (UI)~~ ✅ Done (2026-04-24)
- Commit: fb39871
- Header `<select#projectSelect>` + Create/Delete buttons + 2 modals (New Project / Delete Project)
- `window.fetch` monkey-patch auto-injects `CURRENT_PROJECT` into all `/api/*` calls (no changes to existing fetch code)
- Cmd/Ctrl+P shortcut -> focus project selector
- Model selector auto-reflects current project's model

---

## [MP-08-archived] Header Project Selector (UI)
- Goal: Add project dropdown to dashboard header (next to model selector)
- Impact scope: `dashboard/index.html`
- Done criteria:
  - Project list + active indicator
  - Full view reload on switch (`/api/wiki?project=<slug>` etc.)
  - "New Project" button -> modal (name, description, model, template variant)
  - Model selector reads/writes current project's model
  - Keyboard shortcut: Cmd/Ctrl+P (project switch palette)
- Risk: medium

---

## ~~[MP-09] Purpose-based Folder Template Support~~ ✅ Done (2026-04-24)
- Commit: df51718
- `project_registry.TEMPLATE_FOLDERS` + `recommended_folders()`
- `create_project`: auto mkdir per-template folders
- `/api/templates` endpoint + recommended folder preview in New Project modal
- Existing folder select dropdown auto-updates via `loadFolders()` for immediate use

---

## [MP-09-archived] Purpose-based Folder Template Support
- Goal: Meet user request to "organize pages in purpose-based folders"
- Impact scope: Page creation flow
- Done criteria:
  - Recommended folder structure in template CLAUDE.md (e.g. `sources/ entities/ concepts/ techniques/ analyses/`, varying by variant)
  - Option to auto-place ingested content in appropriate subfolder by type
  - "Quick folder select" dropdown in page create modal (project root + existing folders)
  - Sidebar "Purpose" tab: grouping view based on frontmatter.tags or folder
- Risk: low

---

## ~~[MP-10] Documentation Update~~ ✅ Partial (2026-04-24)
- Commit: dfcf66a
- Added 'Multi-project' section to README.md / README-ko.md
- Updated repository layout: projects/ templates/ plans/ logs/ project_registry.py
- API curl examples + per-template recommended folder table + legacy compatibility notes
- Remaining: Update Guide modal in dashboard, re-capture screenshots — proceed optionally after user verification

---

## [MP-10-archived] Obsidian / git / Dashboard Documentation Update
- Goal: After multi-project migration, update README/guide for actual usable state (CLAUDE.md section 4.5)
- Impact scope: `README.md`, `README-ko.md`, `docs/`, Dashboard Guide modal
- Done criteria:
  - Reflect new paths/commands
  - Re-capture screenshots/GIFs (if needed)
  - Verify `.obsidian/` vault path still works — decide if per-project vault registration is needed
- Risk: low
