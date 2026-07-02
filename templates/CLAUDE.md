# Wiki Template (generic)

> This file is the starter schema copied to `projects/<slug>/CLAUDE.md` when creating a new project.

## Purpose

{{PURPOSE}}

## Agent scope

- This schema is for a filesystem-capable maintenance agent, not a vendor-specific CLI.
- `raw/` remains immutable; only `wiki/` and maintenance outputs are writable surfaces.

## Directory structure

```
raw/              # IMMUTABLE source documents
raw/assets/       # Downloaded images
wiki/             # Agent-maintained wiki pages
  sources/        # source-summary pages
  entities/       # proper nouns
  concepts/       # ideas and frameworks
  techniques/     # methods and algorithms
  analyses/       # multi-source analysis
  index.md
  log.md
  overview.md
ingest-reports/
reflect-reports/
plans/
.obsidian/        # Obsidian vault settings (do not modify)
```

## Behavior

- Always add `[^src-{slug}]` inline citations to factual claims.
- When sources contradict, apply the Contradiction Resolution policy.
- Update `last_updated`, `source_count` in frontmatter on every page modification.
- Record all actions in `wiki/log.md`.
- Generate WHY reports in `ingest-reports/` after each ingest.

## Key policies

1. **raw/ is immutable** — never modify files under any raw/ directory.
2. **Citations required** — all factual claims must have inline `[^src-*]` citations.
3. **Contradiction resolution** — when sources conflict, follow the resolution policy.
4. **Git commits** — every change is committed with descriptive messages.
5. **Cross-references** — link related pages liberally with `[[wikilinks]]`.
