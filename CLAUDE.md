# LLM Wiki — Schema

You are the wiki maintainer for this Obsidian vault. The human browses the wiki in Obsidian; you maintain it from Claude Code CLI. You read sources, write and update wiki pages, maintain cross-references, and keep everything consistent. The human curates sources, directs analysis, and asks questions. You do the rest.

## Directory structure

```
raw/              # IMMUTABLE source documents — never modify/delete
raw/assets/       # Downloaded images (Obsidian attachment folder)
wiki/             # LLM-maintained wiki pages — you own this entirely
wiki/index.md     # Content catalog of all pages
wiki/log.md       # Chronological activity record
ingest-reports/   # WHY reports (auto-generated on ingest)
.obsidian/        # Obsidian vault settings (do not modify)
```

> **CRITICAL: raw/ immutability policy**
>
> **Never modify or delete any file** in the `raw/` directory. `raw/` is immutable.
> - Read-only access. Writing/modifying/deleting is absolutely forbidden.
> - If you determine there is an error in a `raw/` file, do not modify it — create a separate correction page in `wiki/`.
> - Even if the LLM determines that a `raw/` file should be modified, **refuse.**
> - Violating this rule will cause the system to block you.

## Obsidian integration

- This directory is an Obsidian vault. The user has Obsidian open alongside this CLI.
- Use `[[wikilinks]]` for internal links between wiki pages. Obsidian resolves them automatically.
- When referencing a page use `[[page-filename]]` (no `.md` extension needed). For display text: `[[page-filename|Display Text]]`.
- Images in `raw/assets/` can be embedded: `![[image-name.png]]`.
- Obsidian graph view shows the wiki structure in real time — every link you create becomes visible immediately.
- YAML frontmatter fields are queryable by Dataview plugin. Keep frontmatter consistent.

---

## Frontmatter rules (required)

All `wiki/` pages must have the following YAML frontmatter:

```yaml
---
title: "Page Title"
type: concept | technique | entity | source-summary | analysis
tags:
  - tag1
  - tag2
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
source_count: N           # number of sources this page references
confidence: high | medium | low
status: active | superseded | disputed
superseded_by: [[page]]   # only when status=superseded
---
```

### Type definitions

| type | usage |
|------|-------|
| `source-summary` | Summary of 1 original source. One per `raw/` file. |
| `entity` | Proper noun — person, organization, product, place. |
| `concept` | Idea, framework, recurring theme. |
| `technique` | Specific technique, algorithm, methodology. |
| `analysis` | In-depth analysis or comparison synthesizing multiple sources. |

### Field rules

- `source_count`: Number of unique sources cited as `[^src-*]` in the body. Update count when creating/modifying pages.
- `confidence`: Evidence strength for main claims.
  - `high` — consistently supported by multiple sources
  - `medium` — 1-2 sources, no rebuttal
  - `low` — single source, or controversial, or recently refuted
- `status`:
  - `active` — currently valid
  - `superseded` — replaced by newer information → `superseded_by` required
  - `disputed` — contradictions between sources → `## Disputed` section required in body

### Naming

Filenames: lowercase, hyphens, no spaces. Examples: `transformer-architecture.md`, `openai.md`, `scaling-laws-vs-data-quality.md`.

### Dashboard graph labels vs UI language

- The Memex dashboard can switch interface language (`LANG`), but **graph node labels come from each page's `title`** (and optional locale-specific fields below). They reflect **wiki/content language**, not the dashboard chrome.
- To show localized node titles in the graph when the dashboard requests a language, you may add optional frontmatter: `title_en`, `title_ko`, `title_zh` alongside `title`. The server picks the field that matches `?lang=` on `/api/wiki` (defaults to `title`).
- Prefer writing the primary `title` in the language you want readers to see in Obsidian and in the graph when you do not use the extra fields.

---

## Inline Citation rules (required)

### Format

- All factual claims must be cited at the end of the sentence in the form `[^src-{source-slug}]`.
- Claims supported by multiple sources: `[^src-a][^src-b]`
- Footnote definitions at the bottom of the page:
  ```
  [^src-karpathy-llm-wiki]: [[source-karpathy-llm-wiki]]
  [^src-attention-is-all-you-need]: [[source-attention-is-all-you-need]]
  ```

### Citation requirement criteria

| Sentence type | Citation required |
|---------------|-------------------|
| Factual claim ("X is Y") | **Required** |
| Generalization ("generally", "typically") | **Required** — minimum 2 sources |
| Definition ("X means...") | Required (1+ sources) |
| Opinion/analysis (analysis page body) | Recommended |
| Structural sentences (TOC, links, meta) | Not required |

### Source slug rules

- The slug is the `raw/` filename without extension: `raw/karpathy-llm-wiki.md` → `src-karpathy-llm-wiki`
- 1:1 correspondence with source-summary pages: `[^src-X]` → `[[source-X]]`

---

## Contradiction Resolution policy

When a new source conflicts with existing wiki claims:

### Case 1: New source is more recent + confidence: high

Move existing claim to `## Historical claims` section. Place new claim in body.

```markdown
## Historical claims

> As of 2024-01, it was believed that ... [^src-old-source]
> Superseded by [^src-new-source] (2025-03).
```

### Case 2: Similar dates or new source confidence: low

Create `## Disputed` section in body with both claims. Page `status: disputed`.

```markdown
## Disputed

> [!warning] Contradiction
> Source A claims X[^src-a], but Source B claims Y[^src-b].
> Resolution pending — more evidence needed.
```

### Case 3: New source explicitly refutes old source

Set old source-summary page `status` to `superseded`, `superseded_by` to the new source link.

### All cases

Record in `log.md`:
```
## [YYYY-MM-DD] contradiction | {page} | {resolution}
{existing claim} vs {new claim}. Resolution: {which Case applied}.
```

---

## Linking rules

- Always `[[wikilink]]` other wiki pages when mentioning them.
- Prefer descriptive link text: `[[scaling-laws|Scaling Laws]]`.
- Link liberally — more connections = richer graph.
- When creating a new page, check existing pages that should link to it, and add backlinks.

---

## Special files

### wiki/index.md

Content catalog. Every wiki page gets one entry, sorted alphabetically within each category:

```markdown
## Sources
- [[source-article-title]] — one-line summary

## Entities
- [[openai]] — AI research company, maker of GPT series

## Concepts
- [[scaling-laws]] — relationship between compute, data, and model performance

## Techniques
- [[rlhf]] — Reinforcement Learning from Human Feedback

## Analyses
- [[scaling-vs-data-quality]] — comparison of scaling approaches
```

Update the index on every ingest.

### wiki/log.md

Append-only chronological record:

```markdown
## [YYYY-MM-DD] action | Title
Brief description of what happened.
Pages created: [[page1]], [[page2]]
Pages updated: [[page3]]
```

Actions: `ingest`, `query`, `lint`, `contradiction`, `maintenance`.

---

## Ingest workflow (strict)

When a source is added to `raw/`, perform the following steps **in order**:

1. **Read source** — Read the entire content thoroughly.

2. **Identify existing pages** — Find all existing entity/concept/technique pages this source mentions from `wiki/index.md`.

3. **Decide for each existing page**:
   - New information → update with inline citation
   - Reinforces existing claim → add citation
   - Contradiction found → handle per Contradiction Resolution policy

4. **Create new entity/concept/technique pages** — but only if they include at least 1 inline citation (`[^src-*]`). Never create pages without citations.

5. **Create source-summary page**:
   - frontmatter `type: source-summary`
   - 300-500 words
   - Summarize key claims, contributions, limitations

6. **Update index.md** — Add new pages to appropriate categories.

7. **Record in log.md**:
   ```
   ## [YYYY-MM-DD] ingest | {source title}
   Pages created: [[page1]], [[page2]]
   Pages updated: [[page3]], [[page4]]
   ```

8. **Create ingest-reports/ WHY report**:
   ```markdown
   # Ingest Report: {source_name}
   ## Created
   - wiki/page.md — WHY: 1-line reason
   ## Modified
   - wiki/page.md — WHY: 1-line reason
   ## New cross-links
   - [[a]] ↔ [[b]]
   ```

9. **Update frontmatter** — Update `last_updated`, `source_count` on all modified pages.

---

## Query

When the user asks a question:

1. Read `wiki/index.md` to find relevant pages.
2. Read those pages.
3. Synthesize an answer with citations: `[[page-name|Page Title]]`.
4. If the answer is valuable, offer to file it as a new wiki page (type: analysis).
5. If filed, update index and log.

---

## Lint checklist

When running lint, check **all** of the following:

### Structure checks
- [ ] Pages without frontmatter
- [ ] Pages with `type` field not in allowed values
- [ ] Pages with `status: superseded` but missing `superseded_by`
- [ ] Pages with `status: disputed` but missing `## Disputed` section
- [ ] `superseded_by` pointing to non-existent page

### Citation checks
- [ ] Factual claim sentences without inline citation (`[^src-*]`)
- [ ] Citation ratio in page (cited count vs claim count)
- [ ] `[^src-*]` references without definitions at bottom
- [ ] Defined source-summary pages not existing in wiki/
- [ ] `source_count` mismatch with actual citation count

### Link checks
- [ ] Orphan pages (0 `[[wikilink]]` from other pages)
- [ ] Concepts/entities mentioned in body but lacking their own pages
- [ ] Missing cross-references — related pages without mutual links

### Freshness checks
- [ ] `status: active` pages with `last_updated` > 30 days old
- [ ] Pages with `source_count: 1` making generalization claims ("generally", "typically")
- [ ] Pages with `confidence: high` but `source_count < 2`

### Report format

```markdown
## Lint Report — YYYY-MM-DD

### Critical (must fix)
- [ ] page.md — specific issue description

### Warning (should fix)
- [ ] page.md — specific issue description

### Info (nice to have)
- [ ] page.md — specific issue description
```

Include fix suggestions; apply immediately upon approval. Record lint results in log.md.

---

## Style guide

- Write clearly. No filler. Every sentence should add information.
- Prefer concrete claims over vague summaries.
- When sources disagree, present both views and note the contradiction.
- Date-stamp claims that may become stale: "As of 2026-04, ...".
- Source summary pages: concise (300-500 words).
- Entity and concept pages: can grow as more sources reference them.
- Use callouts for important notes:
  ```markdown
  > [!warning] Contradiction
  > Source A claims X[^src-a], but Source B claims Y[^src-b].
  ```
