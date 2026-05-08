# ACR AMD64 镜像迁移与统一版本标记经验总结

## 背景

为 `deployment_remote` 国内部署方案准备阿里云 ACR 镜像，需将所有镜像统一为 amd64 架构并标记 `-amd64` 后缀和版本号 `0.1.0`。

涉及的镜像：
- **第一方镜像**（4 个）：frontend, backend, dashboard, report → 路径 `askdata_platform/askdata:<component>-<version>-amd64`
- **第三方镜像**（10 个）：postgres, redis×2, keycloak, mongo, nginx, clickhouse-server, minio, langfuse×2 → 路径 `askdata_platform/<original-name>:<tag>-amd64`
- **预存镜像**：pgvector:pg17-trixie（已存在 ACR）

## 关键技术细节

### 1. Poetry 源配置：国内 PyPI 镜像选择

项目 `pyproject.toml` 原配置使用阿里云 PyPI 镜像（`mirrors.aliyun.com`）作为 poetry 的主源：

```toml
[[tool.poetry.source]]
name = "aliyun"
url = "https://mirrors.aliyun.com/pypi/simple/"
priority = "primary"
```

阿里云 PyPI 从境外网络无法访问（`Read timed out`）。将源切换为清华 PyPI 镜像后可正常工作：

```toml
[[tool.poetry.source]]
name = "tsinghua"
url = "https://pypi.tuna.tsinghua.edu.cn/simple/"
priority = "primary"
```

**注意**：更换源后必须重新生成 `poetry.lock`，否则 `poetry install` 会因 content-hash 不匹配而失败。

```bash
rm poetry.lock && poetry lock
```

### 2. Docker build context 过大导致 OOM

项目根目录无 `.dockerignore`，`COPY . /app` 会将整个 repo（含 `node_modules`、`.git` 等）作为 build context 发送至 Docker daemon。实测 context 达 1.77GB，导致 Docker 进程被 OOM killer 终止（exit code 137）。

**解决方案**：在项目根创建 `.dockerignore`，排除无关目录。最小配置：

```
.git
**/node_modules
**/__pycache__
**/*.pyc
**.venv
.DS_Store
*.md
data/
docs/
dist/
build/
```

添加后 context 缩减至 ~300MB，构建正常。

### 3. macOS bash 3.2 不支持关联数组

`build-push-acr.sh` 原使用 `declare -A`（关联数组）管理第三方镜像映射。但 macOS 默认 bash 版本为 3.2（2007 年发布），**不支持关联数组**，执行报错。

修复方式：将第三方镜像定义从关联数组改为两个平行索引数组：

```bash
# Before (bash 4+ only)
declare -A THIRD_PARTY_IMAGES=(
  ["postgres:17-alpine"]="postgres:17-alpine"
)

# After (bash 3.2 compatible)
THIRD_PARTY_SOURCE_IMAGES=("postgres:17-alpine")
THIRD_PARTY_TARGET_TAGS=("postgres:17-alpine")
```

迭代方式对应调整为 `for i in "${!THIRD_PARTY_SOURCE_IMAGES[@]}"`。

### 4. Docker Hub 间歇性 EOF 错误

从境外拉取 Docker Hub 镜像时遇到间歇性 `EOF` 错误，重试后通常恢复。这是网络层面的不稳定现象。

**处理方式**：
- 使用 `--force` 标志强制重试
- 单个镜像逐一 pull/tag/push（而非脚本批量执行），以便隔离故障
- 已拉取的镜像层会被 docker 缓存，重试时 `Layer already exists` 可跳过

### 5. 第一方镜像的版本标记

使用 `build-push-acr.sh` 脚本管理版本标记：
- 版本文件 `.release-version` 存储当前版本号（如 `0.1.0`）
- 每次构建可自动递增 patch 版本
- `SKIP_BUMP=1` 跳过递增
- `RELEASE_TAG=1.2.3` 指定固定版本

完整构建命令：
```bash
WITH_DASHBOARD=1 WITH_REPORT=1 SKIP_BUMP=1 ./scripts/build-push-acr.sh --amd64 --push
```

### 6. Dockerfile 中 Python 包的 PyPI 源

多个 Dockerfile 硬编码了 PyPI 源，所有 Python 基础镜像构建均通过 pip 安装 Python 包：

| Dockerfile | 默认源 | 构建时覆盖方式 |
|-----------|--------|--------------|
| 根目录 `Dockerfile` | 清华/阿里云混合 | 手动修改或 pip config |
| `dashboard_server/Dockerfile` | `mirrors.aliyun.com` | `--build-arg PYPI_INDEX_URL=...` |
| `report_app_server/Dockerfile` | `mirrors.aliyun.com` | `--build-arg PYPI_INDEX_URL=...` |

从境外构建时通过 `--build-arg` 覆盖为清华镜像：
```bash
--build-arg PYPI_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple/
```

## 手动推送第三方镜像

当 `build-push-acr.sh --push-third-party` 因网络原因中断时，手动逐一手动操作：

```bash
docker pull --platform linux/amd64 <source-image>
docker tag <source-image> ${ACR_REGISTRY}/${ACR_NS}/<target-tag>-amd64
docker push ${ACR_REGISTRY}/${ACR_NS}/<target-tag>-amd64
```

## 验证

使用 `docker manifest inspect` 逐一检查镜像是否存在于 ACR：
```bash
docker manifest inspect ${ACR_REGISTRY}/${ACR_NS}/${IMAGE_TAG} >/dev/null 2>&1 && echo "EXISTS"
```

## 最终镜像清单

所有 14 个镜像（10 第三方 + 4 第一方）全部推送成功，统一带有 `-amd64` 后缀和版本标记。
