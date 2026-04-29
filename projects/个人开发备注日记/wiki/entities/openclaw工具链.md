---
title: "OpenClaw工具链"
type: entity
created: 2026-04-30
last_updated: 2026-04-30
source_count: 0
confidence: medium
status: active
tags: []
---

# OpenClaw工具链

> 从 Apple Notes 中提取的 OpenClaw 相关工具配置

## 核心工具

### OpenClaw
- **定位**: AI Agent 平台
- **配置**: ~/.openclaw/openclaw.json
- **MCP配置**: ~/.openclaw/workspace/config/mcporter.json

### mcporter
- **定位**: MCP 服务管理
- **配置**: ~/.openclaw/workspace/config/mcporter.json
- **传输方式**: STDIO / SSE

### memo (Apple Notes CLI)
- **版本**: v0.3.3
- **用途**: 读取/管理 Apple Notes

## 已配置的MCP服务

- **xiaohongshu**: http://localhost:18060/mcp
- **xiaohongshu-mcp**: http://localhost:18060/mcp
- **memex**: stdio (本地进程)

## 常用命令

```bash
openclaw status
mcporter list
mcporter call <service>.<method>
memo notes -fl
```

## 相关页面

- [[AI模型提供商概览]] — AI模型配置
- [[Docker部署模式]] — 容器部署

