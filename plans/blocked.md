---
title: "Blocked — items needing decisions/information"
created: 2026-04-23
---

# Blocked

---

## [2026-04-23 20:45] BLOCK-MP-04 Legacy Content Migration

**Original queue item**: MP-04 Move wiki/raw/ingest-reports/reflect-reports/query-log.jsonl/CLAUDE.md to `projects/karpathy-llm/`
**Attempt count**: 0 (autonomous mode does not execute)
**Block reason**:
- Risk level `high` — stated in `today-queue.md`. Autonomous mode prohibited per section 21.8.
- Bulk `git mv`, root layout change, running Dashboard Server (pid 94329) requires restart with new paths.
- Q-1~Q-4 (below) decisions are prerequisites.

**Decisions/information needed** (from user):
- Q-1 Single repo vs Per-project repo
- Q-2 Obsidian vault scope
- Q-3 Slug rules (default: `make_slug` + duplicate check)
- Q-4 Delete policy (default: `projects/.trash/` soft delete)

**Execution checklist** (after user approval):
1. `git mv` 5 items (wiki, raw, ingest-reports, reflect-reports, query-log.jsonl)
2. `git mv CLAUDE.md projects/karpathy-llm/CLAUDE.md` + recreate thin CLAUDE.md at root
3. `.dashboard-settings.json` -> `projects/karpathy-llm/.settings.json` (migrate model value, delete original)
4. Register `karpathy-llm` in `projects.json` + set `active`
5. Restart server, smoke test `/api/projects`, `/api/wiki?project=karpathy-llm` — note: if MP-07 is incomplete, `/api/wiki` may still reference legacy paths and break. MP-07 must be done first.

**Related commits**: 8c0750d (MP-01), 18b0cd9 (MP-02), bcf7f32 (MP-03)

---

## Design decisions pending

## Design decisions pending (required before MP-04 execution)

- **[Q-1] Per-project git repo separation**
  - Option A: Single repo + commit under `projects/<slug>/` (recommended, simple)
  - Option B: Separate repo per project
  - Decision maker: user
  - Impact: MP-04, MP-05, OPS-04

- **[Q-2] Obsidian vault scope**
  - Option A: Entire root as one vault (current) — free movement between projects
  - Option B: Independent vault registration per project — N entries in obsidian.json
  - Decision maker: user (depends on workflow)
  - Impact: MP-10

- **[Q-3] Project slug rules**
  - Alphanumeric+hyphen only? Allow Korean? No spaces?
  - Alternative: user-provided title + auto slug (reuse make_slug)

- **[Q-4] Project delete policy**
  - Immediate permanent delete vs move to trash/<slug>-<timestamp>/
  - Default: trash recommended (reversible)
