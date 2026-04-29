---
title: "pkms-query-engine"
type: concept
created: 2026-04-27
last_updated: 2026-04-27
source_count: 1
confidence: medium
status: active
tags:
  - pkms
  - architecture
  - search
sources:
  - pkms-system-design
---

---
title: "PKM Query Engine"
type: concept
tags:
  - pkms
  - architecture
  - search
created: 2026-04-27
last_updated: 2026-04-27
source_count: 1
confidence: medium
status: active
---

# PKM Query Engine

A Personal Knowledge Management query engine searches across multiple index types and merges results for the user.

## Pipeline [^src-pkms-system-design]

```
User Query → Rewrite → Multi-Index Search → Merge/Rank → Results
```

## Index Types [^src-pkms-system-design]

| Index | Purpose |
|-------|---------|
| Inverted (BM25) | Keyword search — exact and near-exact term matching |
| Vector Embeddings | Semantic search — find notes by meaning, not just words |
| Tag index | Metadata filtering — e.g., `tags.contains("technique")` |
| Graph traversal | Relationship queries — "notes connected to this one" |

A robust query engine blends results from all four index types rather than relying on a single strategy.

[^src-pkms-system-design]: [[source-pkms-system-design]]

