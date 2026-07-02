# Memex Repository Instructions

## Working scope

- Treat this repository as a knowledge-workspace application, not just a Python service.
- Preserve the separation between immutable source material in `raw/` and derived knowledge in `wiki/`.
- When changing wiki-maintenance behavior, keep the root `CLAUDE.md` as the authoritative schema for page structure, citations, contradiction handling, and ingest flow.

## Repository expectations

- Prefer small, behavior-focused edits over broad refactors.
- Keep project creation, dashboard behavior, and MCP behavior aligned when they share the same data model.
- Do not silently change persistence formats such as `projects.json`, `.dashboard-settings.json`, or per-project `.settings.json` unless the task explicitly requires it.
- Add or update focused regression tests when touching shared API behavior, scheduler behavior, or path-safety logic.

## Codex guidance

- Codex should use this file for repository-level instructions.
- The repository `.codex/config.toml` also registers `CLAUDE.md` as a fallback instruction filename so nested wiki projects can reuse their existing schema files without duplicating them into `AGENTS.md`.
