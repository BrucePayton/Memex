---
title: "ACR amd64 镜像迁移与统一版本标记经验总结"
type: analysis
created: 2026-05-09
last_updated: 2026-05-09
source_count: 1
confidence: medium
status: active
tags:
  - deployment
  - acr
  - docker
  - amd64
  - migration
sources:
  - deployment-remote-acr-amd64-migration
---


## 背景

为 `deployment_remote` 国内部署方案准备阿里云 ACR 镜像，需将所有镜像统一为 amd64 架构并标记 `-amd64` 后缀和版本号 `0.1.0`。

涉及镜像：10 个第三方（postgres, redis×2, keycloak, mongo, nginx, clickhouse-server, minio, langfuse×2）+ 4 个第一方（frontend, backend, dashboard, report）+ pgvector。

## 关键技术问题与解决

### 1. Poetry 镜像源：阿里云不可达 → 清华镜像

**问题**：项目 `pyproject.toml` 配置阿里云 PyPI（`mirrors.aliyun.com`）为主源。从境外网络全部读取超时。

**解决**：切换为清华 PyPI 镜像，重新生成 `poetry.lock` [^src-deployment-remote-acr-amd64-migration]。

```toml
[[tool.poetry.source]]
name = "tsinghua"
url = "https://pypi.tuna.tsinghua.edu.cn/simple/"
priority = "primary"
```

更换源后必须重新生成 lock 文件：
```bash
rm poetry.lock && poetry lock
```

### 2. Docker build context 过大导致 OOM

**问题**：项目根目录无 `.dockerignore`，`COPY . /app` 将整个 repo（含 `node_modules`、`.git` 等 1.77GB）发送至 Docker daemon，进程被 OOM 终止（exit 137）。

**解决**：添加 `.dockerignore` 排除 `node_modules`、`.git`、`**/__pycache__`、`data/`、`docs/` 等，context 缩减至 ~300MB。

### 3. macOS bash 3.2 不支持关联数组

**问题**：构建脚本 `build-push-acr.sh` 使用 `declare -A`（关联数组），macOS 默认 bash 3.2 不支持。

**解决**：改为两个平行索引数组，保持向后兼容 [^src-deployment-remote-acr-amd64-migration]。

### 4. Docker Hub 间歇性 EOF

从境外拉取 Docker Hub 镜像时偶发 EOF 错误。重试即可恢复，已拉取的层会被缓存。

### 5. Dockerfile 硬编码 PyPI 源

dashboard/report 的 Dockerfile 默认使用阿里云镜像。从境外构建时需覆盖：
```bash
--build-arg PYPI_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/
```

## 版本标记规范

使用 `build-push-acr.sh` 管理版本：
- `.release-version` 文件存储当前版本号（`0.1.0`）
- 自动递增 patch 版本或 `RELEASE_TAG=1.2.3` 固定版本
- 镜像 tag 格式：`<component>-<version>-amd64`

## 手动推镜像流程

当脚本因网络中断时，可逐一手动操作：
```bash
docker pull --platform linux/amd64 <source>
docker tag <source> ${ACR}/${NS}/<target>-amd64
docker push ${ACR}/${NS}/<target>-amd64
```

## 验证

使用 `docker manifest inspect` 检查镜像存在性。

## 经验要点

1. **境外构建国内项目**：PyPI 源选择清华镜像比阿里云更可靠
2. **Docker context**：始终维护 `.dockerignore`，特别是大项目
3. **脚本兼容性**：macOS 开发环境注意 bash 版本差异
4. **重试机制**：境外网络操作需容忍间歇性失败，支持重试
5. **版本管理**：统一版本标记可大幅简化部署配置维护

