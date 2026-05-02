---
title: "AskData 技术栈"
type: concept
created: 2026-05-02
last_updated: 2026-05-02
source_count: 0
confidence: medium
status: active
tags:
  - askdata-platform
  - tech-stack
  - 技术栈
---

# AskData 技术栈

## 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.11-3.12 | 主要语言 |
| **FastAPI** | 0.115.9 | Web 框架 |
| **Uvicorn** | 0.34.3 | ASGI 服务器 |
| **LangGraph** | ^1.0.6 | Agent 工作流编排 |
| **LangChain** | 1.2.3 | LLM 应用框架 |
| **LiteLLM** | 1.72.0 | 多模型统一接口 |
| **CrewAI** | 0.130.0 | 多 Agent 协作 |
| **LlamaIndex** | ^0.14.3 | 数据索引与检索 |
| **ChromaDB** | 1.0.12 | 向量数据库 |
| **PostgreSQL** | — | 主数据库 |
| **Redis** | ^6.4.0 | 缓存/会话 |
| **Alembic** | ^1.16.4 | 数据库迁移 |
| **Psycopg** | ^3.2.0 | PostgreSQL 异步驱动 |
| **PgVector** | ^0.4.2 | 向量检索 |
| **Keycloak** | — | 身份认证 |
| **Langfuse** | ^3.0.8 | LLM 可观测性 |
| **OpenTelemetry** | 1.34.1 | 分布式追踪 |

## LLM 集成

| 提供商 | 集成方式 |
|--------|----------|
| OpenAI | langchain-openai |
| DeepSeek | langchain-deepseek |
| Google Gemini | langchain-google-genai |
| 通用兼容 | LiteLLM (OpenAI 格式) |

## 前端技术栈

| 技术 | 用途 |
|------|------|
| **React** | UI 框架 |
| **TypeScript** | 类型安全 |
| **Vite** | 构建工具 |
| **TailwindCSS** | CSS 框架 |
| **Plotly/Dash** | 数据可视化 |
| **Dash Bootstrap Components** | UI 组件 |

## 数据处理

| 库 | 用途 |
|----|------|
| **Pandas** | 2.0-2.3 数据分析 |
| **NumPy** | 2.2.6 数值计算 |
| **SciPy** | 1.15.3 科学计算 |
| **Matplotlib** | 图表生成 |
| **akshare** | 1.17.8 金融数据 |
| **tushare** | 1.4.21 股票数据 |
| **yfinance** | 0.2.63 Yahoo Finance |

## 文档处理

| 库 | 用途 |
|----|------|
| **fpdf2** | ^2.8.2 PDF 生成 |
| **python-docx** | ^1.1.2 Word 生成 |
| **python-pptx** | ^1.0.2 PPT 生成 |
| **pdfplumber** | 0.11.7 PDF 解析 |
| **markitdown** | ^0.1.2 文档转 Markdown |
| **markdown** | ^3.10.1 Markdown 处理 |
| **openpyxl** | 3.1.5 Excel 读写 |
| **xlrd** | 2.0.2 Excel 读取 |

## 爬虫与数据采集

| 库 | 用途 |
|----|------|
| **beautifulsoup4** | 4.13.4 HTML 解析 |
| **lxml** | 5.4.0 XML/HTML 解析 |
| **curl-cffi** | 0.11.4 HTTP 请求 |
| **requests** | 2.32.5 HTTP 客户端 |
| **httpx** | 0.28.1 异步 HTTP |
| **aiohttp** | 3.12.13 异步 HTTP |
| **trafilatura** | ^2.0.0 网页内容提取 |
| **markdownify** | ^1.1.0 HTML → Markdown |

## 部署与运维

| 组件 | 用途 |
|------|------|
| **Docker** | 容器化部署 |
| **Docker Compose** | 多服务编排 |
| **Nginx** | 反向代理 |
| **Kubernetes** | 33.1.0 K8s 客户端 |
| **Celery** | ^5.6.3 异步任务队列 |

## MCP (Model Context Protocol)

| 库 | 用途 |
|----|------|
| **mcp** | ^1.10.1 MCP SDK |
| **langchain-mcp-adapters** | 0.2.1 MCP → LangChain 桥接 |

## 测试

| 库 | 用途 |
|----|------|
| **pytest** | ^9.0.2 测试框架 |
| **pytest-asyncio** | ^1.3.0 异步测试 |

[^src-14-pyproject]: `pyproject.toml`
