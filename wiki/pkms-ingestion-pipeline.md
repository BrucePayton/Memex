---
title: "pkms-ingestion-pipeline"
type: technique
created: 2026-04-27
last_updated: 2026-04-27
source_count: 1
confidence: medium
status: active
tags:
  - pkms
  - architecture
  - pipeline
sources:
  - pkms-system-design
---

---
title: "PKM Ingestion Pipeline"
type: technique
tags:
  - pkms
  - architecture
  - pipeline
created: 2026-04-27
last_updated: 2026-04-27
source_count: 1
confidence: medium
status: active
---

# PKM Ingestion Pipeline

The ingestion pipeline transforms raw input (files, pastes, API responses, web clips) into structured, indexed knowledge.

## Flow [^src-pkms-system-design]

```
Input → Parser → AST → Entity Extractor → Indexer
```

### Steps [^src-pkms-system-design]

1. **Parse** — Convert Markdown to an Abstract Syntax Tree (e.g., using remark or remark/gfm).
2. **Extract** — Pull out wikilinks, tags, YAML frontmatter, and heading structure.
3. **Enrich** — Identify entities (people, concepts, tools), detect cross-references between notes.
4. **Index** — Update the search index (BM25, vector) and graph index (nodes + edges).

The pipeline is idempotent — re-ingesting the same source should produce the same index state.

[^src-pkms-system-design]: [[source-pkms-system-design]]

