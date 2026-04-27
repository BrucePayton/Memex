---
title: "pkms-graph-engine"
type: concept
created: 2026-04-27
last_updated: 2026-04-27
source_count: 1
confidence: medium
status: active
tags:
  - pkms
  - architecture
  - graph
sources:
  - pkms-system-design
---

---
title: "PKM Graph Engine"
type: concept
tags:
  - pkms
  - architecture
  - graph
created: 2026-04-27
last_updated: 2026-04-27
source_count: 1
confidence: medium
status: active
---

# PKM Graph Engine

The graph engine is the core data structure of a Personal Knowledge Management system. Each note is a node; each link (wikilink, reference) is an edge.

## Structure [^src-pkms-system-design]

A graph maps note IDs to sets of connected IDs:

```typescript
interface Graph {
  nodes: Map<string, NoteNode>
  edges: Map<string, Set<string>>  // forward links
}
```

Backlinks are derived by inverting the forward edge map — they are never stored, only computed.

## Key Operations [^src-pkms-system-design]

- **`getBacklinks(noteId)`** — all nodes that link to the given note.
- **`getNeighbors(noteId, depth)`** — k-hop neighborhood around a note.
- **`findOrphans()`** — nodes with zero in-degree and zero out-degree (isolated notes).
- **`findHubs()`** — nodes with high in-degree (central, frequently referenced concepts).

## Computed Properties [^src-pkms-system-design]

Each note node carries computed metrics:

| Property | Description |
|----------|-------------|
| `inDegree` | How many notes link here |
| `outDegree` | How many links the note makes |
| `clusters` | Community detection result (grouping related notes) |

[^src-pkms-system-design]: [[source-pkms-system-design]]

