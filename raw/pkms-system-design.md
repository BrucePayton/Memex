# Personal Knowledge Management System Design

## Core Principles

1. **Capture** — Collect notes, highlights, ideas wherever they come from
2. **Organize** — Structure with links, tags, and folders (not rigid hierarchies)
3. **Connect** — Cross-reference ideas so knowledge compounds over time
4. **Express** — Surface insights by combining and refining your notes

## Recommended Approach

**Tool choice:**
- **Obsidian** — best for linking, local-first, plugin ecosystem
- Alternatives: Logseq, Notion, Roam Research

**Structure:**
- **MOCs (Maps of Content)** — Hub pages that organize notes on a topic
- **Daily notes** — Inbox for unprocessed thoughts, dated automatically
- **Evergreen notes** — One idea per note, written for your future self
- **Wikilinks** over folders — Let connections matter more than location

**Workflow (CODE or PARA):**
- **Capture** → Store in daily notes or inbox
- **Distill** — Summarize, tag, link to related notes
- **Organize** — Create MOCs to cluster related ideas
- **Express** — Use notes as building blocks for output (writing, decisions)

---

## PKM Engine Architecture

### 1. Storage Layer

```
┌─────────────────────────────────────────┐
│                 Storage                  │
├─────────────────────────────────────────┤
│  File System (Markdown files)           │
│  Graph Index (edges/relationships)      │
│  Full-Text Index (search)               │
│  Metadata DB (frontmatter/tags/dates)   │
└─────────────────────────────────────────┘
```

- **Primary storage**: Plain text files (usually Markdown) — portable, git-friendly
- **Secondary indexes**: Built from files, never the source of truth
- **Key decision**: Store everything in plain files; rebuild indexes from scratch if needed

### 2. Ingestion Pipeline

```
Input (file, paste, API, clip) → Parser → AST → Entity Extractor → Indexer
```

Steps:
1. **Parse** — Markdown → AST (e.g., remark, remark/gfm)
2. **Extract** — Links, tags, frontmatter, headings
3. **Enrich** — Identify entities (people, concepts), detect cross-references
4. **Index** — Update search index + graph index

### 3. Graph Engine

The heart of a PKM. Each note is a node, each link is an edge:

```typescript
interface Graph {
  nodes: Map<string, NoteNode>
  edges: Map<string, Set<string>>  // backlinks are inverse edges
}

interface NoteNode {
  id: string
  title: string
  tags: string[]
  metadata: Record<string, unknown>
  // computed
  inDegree: number          // how many notes link here
  outDegree: number         // how many links it makes
  clusters: ClusterId[]     // community detection result
}
```

**Key operations:**
- `getBacklinks(noteId)` — all nodes pointing here (reverse of forward links)
- `getNeighbors(noteId, depth)` — k-hop neighborhood
- `findOrphans()` — nodes with 0 in-degree and 0 out-degree
- `findHubs()` — nodes with high in-degree (central concepts)

### 4. Query Engine

```
User Query → Rewrite → Multi-Index Search → Merge/Rank → Results
```

Index types to maintain:

| Index | Purpose | Example |
|-------|---------|---------|
| Inverted (BM25) | Keyword search | "show me notes about transformers" |
| Vector Embeddings | Semantic search | "notes about how models learn" (even without exact words) |
| Tag index | Filtering | `tags.contains("technique")` |
| Graph traversal | Relationship queries | "notes connected to this one" |

### 5. Link Resolution

Two critical link types:

- **Forward links** — `[[wikilink]]` in note content
- **Backlinks** — computed: "who links to me?"

```typescript
function resolveLinks(notes: Note[]): LinkGraph {
  const graph = new Map<string, Set<string>>()
  for (const note of notes) {
    for (const link of extractWikilinks(note)) {
      const target = resolveTitleToId(link)
      if (target) {
        graph.get(note.id).add(target)
      }
    }
  }
  return graph // then derive backlinks by inversion
}
```

### 6. Rendering / Presentation Layer

- **Graph View** — Force-directed layout of the graph
- **Preview Pane** — Render markdown to HTML on hover (like link previews)
- **Backlinks Panel** — List of `getBacklinks(currentNote)`
- **Daily Notes View** — Templated scaffold with auto-date
- **Search Results** — Blended results from all index types

### 7. Sync / Conflict Strategy

If multi-device:

- **CRDT-based** (e.g., Yjs) for conflict-free editing
- **File-based** — Rely on Git or cloud sync, detect on file change
- **Last-write-wins** — Simple but fragile

## Minimal Viable Engine

If you want to build one, start with this:

```
pkmd/
├── vault/          # Markdown files
├── src/
│   ├── parser.ts       # Markdown → AST + extract links/tags
│   ├── graph.ts        # Build in-memory graph
│   ├── search.ts       # BM25 inverted index
│   ├── server.ts       # HTTP/WebSocket API
│   └── renderer.ts     # Markdown → HTML
└── package.json
```

Key API:

| Endpoint | Description |
|----------|-------------|
| `GET /notes/:id` | Full note content |
| `GET /notes/:id/backlinks` | All notes linking here |
| `GET /graph` | Full graph (nodes + edges) for visualization |
| `GET /search?q=` | BM25 keyword search |
| `POST /notes` | Create/update a note |
