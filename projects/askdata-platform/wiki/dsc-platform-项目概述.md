---
title: "DSC Platform 项目概述"
type: concept
created: 2026-05-02
last_updated: 2026-05-02
source_count: 0
confidence: medium
status: active
tags:
  - dsc
  - data-supply-chain
  - platform
---

# DSC Platform (Data Supply Chain Platform)

## 项目简介
DSC Platform 是一个为生成式AI提供全链路数据支持的平台，专注于数据采集、处理、知识库构建、向量检索和工作流编排，为AI应用提供高质量的数据支撑。

## 核心特性
- **多源数据接入**：支持各类文档（PDF、Word、Excel、PPT、图片等）、数据库、API等多种数据源接入
- **智能文档处理**：集成OCR、文档解析、内容提取等能力，自动化处理非结构化数据
- **知识库管理**：完整的知识库生命周期管理，包括创建、更新、版本控制、权限管理
- **向量检索引擎**：支持多种向量数据库，提供高效的语义检索能力
- **工作流编排**：可视化的工作流设计器，支持复杂数据处理流程的编排和执行
- **统一API服务**：提供标准化的RESTful API，方便与上层应用集成

## 技术栈
### 后端框架
- **FastAPI**: 高性能Python Web框架，提供异步API支持
- **Uvicorn**: ASGI服务器，用于运行FastAPI应用
- **Pydantic**: 数据验证和序列化
- **SQLAlchemy**: ORM框架，用于数据库操作

### AI/ML相关
- **LangChain**: LLM应用开发框架
- **PaddleOCR**: 百度开源OCR工具，支持中英文识别
- **Transformers**: HuggingFace Transformers库，提供预训练模型支持
- **PyTorch**: 深度学习框架
- **OpenCV**: 计算机视觉库，用于图像处理

### 数据处理
- **Pandas/Numpy**: 数据处理和数值计算
- **python-docx/python-pptx/pypdf/openpyxl**: 各类文档格式处理
- **Celery**: 异步任务处理框架
- **Redis**: 缓存和消息队列

### 存储
- **ChromaDB/Weaviate**: 向量数据库，用于向量存储和检索
- **MySQL/PostgreSQL**: 关系型数据库，存储结构化数据
- **MongoDB**: 非结构化数据存储
- **S3兼容存储**: 对象存储，用于文件和资源存储

## 系统架构
DSC Platform采用模块化设计，主要包含以下核心模块：

1. **agent_flow**: 智能体流程编排框架，提供流程定义、节点管理、执行引擎等核心能力
2. **knowledge_mgt**: 知识库管理模块，负责文档上传、解析、存储和检索
3. **db_mgt**: 数据库管理模块，提供数据查询、连接管理、SQL解析等能力
4. **vectors_mgt**: 向量管理模块，负责向量生成、存储和检索
5. **flow_mgt**: 流程管理模块，提供工作流的设计、执行和监控
6. **base_config**: 基础配置模块，管理全局配置和环境变量
7. **utils**: 通用工具函数库

## 快速开始
### 环境要求
- Python 3.11+
- Conda 或虚拟环境管理工具

### 安装步骤
1. 创建并激活虚拟环境：
```bash
conda create -n data_supply_chain python==3.11
conda activate data_supply_chain
```

2. （可选）下载PaddleOCR模型文件并解压到项目根目录
下载地址：https://pan.quark.cn/s/11e83247a065

3. 复制环境配置文件：
```bash
# 本地部署
cp .env.local.template .env

# Docker部署
cp .env.docker.template .env
```

4. 调整环境配置，根据实际情况修改`.env`文件中的配置项

5. 安装依赖包：
```bash
uv pip install -r requirements.txt
```

### 启动服务
```bash
python app_run.py
```

服务默认启动在 `http://0.0.0.0:5630`，可以通过 `http://localhost:5630/docs` 访问API文档。

### Docker部署
```bash
docker run -d --name data_supply_chain_backend -p 5630:5630 data-supply-chain-app:latest
```

## API服务
平台提供统一的API服务，包含以下主要模块：
- `/api/knowledge`: 知识库管理API
- `/api/database`: 数据库操作API
- `/api/vectors`: 向量处理API
- `/api/flow`: 流程提取API
- `/api/flow-apps`: 流程应用市场与调用

详细的API文档可以通过服务的 `/docs` 端点查看。