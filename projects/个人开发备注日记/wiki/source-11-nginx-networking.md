---
title: "11 Nginx Networking"
type: source-summary
created: "2026-05-02"
last_updated: "2026-05-02"
source_count: 1
confidence: medium
status: active
tags:
  - apple-notes
---

# 11 Nginx Networking

> Source: raw/11_nginx_networking.md

This raw file contains 1 note from Apple Notes documenting a comprehensive path-based Nginx reverse proxy design. The note includes a complete Nginx configuration with upstream backends for multiple services (ports 3001-3003), location blocks with path-based routing and rewrite rules, standard proxy headers (Host, X-Real-IP, X-Forwarded-For), health check endpoints, and static file caching with 1-year expiration. A Docker Compose configuration is provided with nginx, three app services, an app-network bridge, and health checks. Frontend application configuration adjustments are documented for both React (vite.config.js base path) and Vue (vue.config.js publicPath). Path design best practices include clear naming conventions (/admin/, /api/, /auth/, /storage/), API versioning (/api/v1/, /api/v2/), advanced options for load balancing (weighted, least_conn, ip_hash), rate limiting (limit_req_zone), and proxy cache configuration. Environment variable management with .env files is also covered.

## 笔记数量

1 notes extracted from Apple Notes.

## 对应主题页

- [[nginx网络]] — 聚合笔记页
