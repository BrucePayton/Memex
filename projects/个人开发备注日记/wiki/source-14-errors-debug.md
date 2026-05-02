---
title: "14 Errors Debug"
type: source-summary
created: "2026-05-02"
last_updated: "2026-05-02"
source_count: 1
confidence: medium
status: active
tags:
  - apple-notes
---

# 14 Errors Debug

> Source: raw/14_errors_debug.md

This raw file contains 1 note from Apple Notes documenting a Vite build error in a ChatBI web designer project. The error reports that multiple @radix-ui React component libraries and lucide-react could not be resolved, with stack traces pointing to vite:import-analysis plugin failures. Root cause analysis identifies that import statements in component files (label.tsx, avatar.tsx, collapsible.tsx, etc.) incorrectly include version numbers (e.g., "@radix-ui/react-collapsible@1.1.3") which Node.js module resolution does not support. The note includes a three-step fix: removing version numbers from all import statements, ensuring all dependencies are installed via npm/yarn (15 @radix-ui packages plus lucide-react@0.487.0), and cleaning cache (.vite, node_modules) before restarting the dev server. Additional troubleshooting steps include verifying package.json and vite.config.ts configurations.

## 笔记数量

1 notes extracted from Apple Notes.

## 对应主题页

- [[错误调试]] — 聚合笔记页
