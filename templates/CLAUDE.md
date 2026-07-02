# Wiki Template (generic)

> This file is the starter schema copied to `projects/<slug>/CLAUDE.md` when creating a new project.

## Purpose

{{PURPOSE}}

## Directory structure

```
raw/              # IMMUTABLE source documents
raw/assets/       # Downloaded images
wiki/             # LLM-maintained wiki pages
wiki/index.md     # Content catalog of all pages
wiki/log.md       # Chronological activity record
ingest-reports/   # WHY reports (auto-generated on ingest)
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
