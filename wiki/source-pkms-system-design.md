---
title: "source-pkms-system-design"
type: source-summary
created: 2026-04-27
last_updated: 2026-04-27
source_count: 1
confidence: medium
status: active
tags:
  - pkms
  - architecture
  - engine
sources:
  - pkms-system-design
---

# Personal Knowledge Management System Design

Overview of how to build a PKM engine from scratch, covering storage, ingestion, graph topology, query, link resolution, rendering, and sync strategies.

## Core Principles [^src-pkms-system-design]

A PKM rests on four activities forming a cycle: **Capture → Organize → Connect → Express**. Notes flow from raw collection through structured linking until they become usable output.

## Architecture Layers

1. **Storage** — Plain text files (Markdown) as the source of truth, with secondary indexes rebuilt on demand.
2. **Ingestion Pipeline** — Parse Markdown → extract links/tags/frontmatter → enrich with entity recognition → index into search + graph.
3. **Graph Engine** — Notes as nodes, links as edges. Key queries: backlinks, k-hop neighbors, orphans, hubs.
4. **Query Engine** — Multi-index search combining BM25 inverted index, vector embeddings, tag filtering, and graph traversal.
5. **Link Resolution** — Forward wikilinks parsed from content; backlinks computed by inverting the edge map.
6. **Rendering** — Graph view (force-directed), preview panes, backlinks panel, daily notes, blended search.
7. **Sync/Conflict** — CRDT-based, file-based (Git/cloud), or last-write-wins depending on consistency needs.

## Minimal Viable Engine

A starter skeleton: Markdown files in a `vault/` directory with five source files — `parser.ts`, `graph.ts`, `search.ts`, `server.ts`, `renderer.ts` — exposed via a small HTTP API (GET notes, backlinks, graph, search; POST notes).

[^src-pkms-system-design]: [[source-pkms-system-design]]
