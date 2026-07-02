---
title: "Backlog — Multi-project + Additional Improvements Candidates"
created: 2026-04-23
---

# Backlog — Additional Implementation/Development Items

Improvement candidates identified while reviewing the current implementation, separate from the multi-project migration.
Priority determined by user.

---

## Operations / Stability

- **[OPS-01] Job queue + progress streaming** — `/api/ingest` risks HTTP timeout on long runs. SSE/WS progress log push + background job identifier.
- **[OPS-02] Long-running Claude call log persistence** — Currently stdout only. Hard to trace failures. Save `runs/<date>-<id>.log`.
- **[OPS-03] Rate limit / budget guard** — Cumulative token/cost tracking per model + block on threshold exceeded. Currently only records cost in `query-log.jsonl`.
- **[OPS-04] backup/restore** — Per-project zip export/import. Consider git bundle as well.
- **[OPS-05] Health check improvement** — Obsidian vault open status, git status, Claude CLI response time in one endpoint.

## Quality / Features

- **[FEAT-01] Cross-project search** — Search multiple project wikis at once. Currently TF-IDF is single-wiki only.
- **[FEAT-02] Cross-project links/embeds** — Reference pages from other projects — syntax like `[[projectA::page]]`.
- **[FEAT-03] Tag-based browser** — Filter/group by frontmatter `tags`. Current UI is type-focused.
- **[FEAT-04] Source upload UX** — Currently text input only. Support file upload (.pdf, .html, .md).
- **[FEAT-05] Page history view** — Per-page git blame/diff viewer (read-only in Dashboard).
- **[FEAT-06] Auto reflect schedule** — Execute reflect at regular intervals -> queue suggestions.
- **[FEAT-07] Diff preview** — Verify diff before applying ingest/lint-fix, then confirm.
- **[FEAT-08] Multilingual wiki pipeline** — Link KO/EN pages for the same concept (translation relationship, not superseded).

## Schema / Governance

- **[GOV-01] Auto contradiction detection** — LLM checks if new claims conflict with existing ones, warns user.
- **[GOV-02] Citation validator (local)** — Auto lint via regex + frontmatter without Claude call. CI hook candidate.
- **[GOV-03] Source trust score** — Per-source trust field (peer-reviewed / blog / tweet etc.) + auto page confidence calculation.
- **[GOV-04] CHANGELOG** — Per-project CHANGELOG.md (Keep a Changelog format). Auto-append by ingest/reflect/lint.

## Security / Access Control

- **[SEC-01] localhost-only access verification** — Currently `::` binding — document and make optional to ensure local-only exposure.
- **[SEC-02] Project delete guard** — `confirm` parameter required + trash/ intermediary.
- **[SEC-03] Secret scan** — Warn at ingest time if API keys/token patterns are included in raw/wiki.

## Test / DX

- **[DX-01] Unit tests** — Pure functions in `server.py`: `make_slug`, `parse_fm`, `_diff_snapshots`, `_tokenize` etc. with pytest.
- **[DX-02] Endpoint contract tests** — Smoke tests for each `/api/*`.
- **[DX-03] Dev mode hot reload** — Currently manual restart.
- **[DX-04] Logging format standardization** — JSON line logging + levels.

## User Experience

- **[UX-01] Onboarding wizard** — First run tutorial: "Create project" -> "Add first source" -> "Ask a question" (3-step).
- **[UX-02] Command palette** — Cmd/Ctrl+K -> fuzzy search all features + project switching.
- **[UX-03] Mobile layout** — Currently desktop-only. Minimum adaptation per section 8.
- **[UX-04] Dark/light theme toggle** — Currently dark fixed.
