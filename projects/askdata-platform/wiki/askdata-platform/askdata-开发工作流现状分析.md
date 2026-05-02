---
title: "AskData 开发工作流现状分析"
type: analysis
created: 2026-05-02
last_updated: 2026-05-02
source_count: 0
confidence: medium
status: active
tags:
  - askdata-platform
  - dev-workflow
  - ci-cd
  - 现状分析
---

# AskData 开发工作流现状分析

## 一、当前 CI/CD 状态

### CI 覆盖

项目中只有 1 个 GitHub Actions 工作流：`.github/workflows/user-module-tests.yml`

- 仅覆盖 `core/modules/user/` 模块
- 触发条件：user 模块文件变更
- 包含：flake8 + black lint、pytest（覆盖率 ≥80%）、safety/bandit 安全扫描、codecov 上传

**严重缺口**：
- AskData 核心流程（Orchestrator、节点、分析）— 零 CI 覆盖
- Dashboard — 零 CI
- Report — 零 CI
- 数据库迁移 — 零 CI
- 前端 — 零 CI（Playwright E2E 已安装但未接入 CI）
- Docker 镜像构建 — 仅本地手动

### Makefile 现状

Makefile 主要围绕 **数据库管理** 设计：

```
db-setup              # 迁移 + 种子数据
db-migrate            # 生成新迁移
db-migrate-down       # 回滚迁移
db-migrate-autogenerate # 自动生成迁移
db-check-schema       # Schema 检查
db-migration-ci-smoke # CI 冒烟测试
deploy-local          # 本地部署
deploy-local-recreate # 重建
deploy-local-rebuild  # 重建镜像
test-askdata          # 唯一测试目标
```

**缺口**：
- 无 `make install`（依赖安装）
- 无 `make lint` / `make format`（代码质量）
- 无 `make test` / `make test-all`（通用测试）
- 无 `make test-coverage`（覆盖率）
- 无 `make build`（构建）
- 无 `make dev`（开发模式）
- 无 `make stop`（停止服务）

### 部署

`deployments/deployment_local/deploy-local.sh` — 600 行 bash 脚本，功能强大但：
- 单一脚本覆盖所有场景（up/recreate/rebuild/migration/health-check）
- 无错误恢复（`set -euo pipefail` 直接退出）
- 需要人工阅读才能理解

## 二、当前开发流程痛点

### 添加新功能的标准流程

```
1. 手动创建 git 分支
2. 编写代码
3. 手动运行测试（如果记得的话）
4. 手动 git commit
5. 手动 push + 创建 PR
6. 手动 review（如果团队有人的话）
7. 手动 merge
```

**问题**：
- 每一步都需要人工干预
- 测试经常跳过（Makefile 中只有一个 `test-askdata` 目标）
- 无 lint/type-check 卡点
- 无 CI 自动反馈
- 数据库迁移经常跳过（只有一份 "reset all" 迁移，无增量历史）

### 修复 Bug 的标准流程

```
1. 定位问题
2. 手动修复代码
3. 前端有大量 "fix" 脚本（fix-blank-screen.sh, fix-all-errors.sh...）
   说明 bug 修复经常是探索性的
4. 手动测试
5. 手动提交
```

**问题**：
- 前端积累了 10+ 个一次性 "fix" 脚本，说明构建不稳定
- 无回归测试保障
- 修复可能引入新问题

### 数据库变更

```
1. 手动修改 models
2. make db-migrate-autogenerate (很少使用)
3. 只有一个迁移文件：80b9742e0f30_reset_all_migrate.py
   说明增量迁移机制基本未使用
4. 手动在本地/服务器应用迁移
```

**问题**：
- 增量迁移很少走正规流程
- 无迁移回滚测试
- 多环境迁移一致性无保障

## 三、Claw-Code 可自动化的环节

| 环节 | 当前状态 | Claw-Code 可替代 | 自动化程度 |
|------|---------|-----------------|-----------|
| 代码编写 | 人工 | ✅ 根据需求描述自动生成 | 80% |
| 单元测试 | 经常跳过 | ✅ 自动生成测试用例 | 70% |
| 代码审查 | 人工或无 | ⚠️ 辅助建议，不能替代人工 | 40% |
| Git 分支 | 手动 | ✅ 自动创建/切换分支 | 90% |
| Git 提交 | 手动 | ✅ 自动 commit + 消息 | 80% |
| PR 创建 | 手动 | ✅ 自动创建 PR | 80% |
| 运行测试 | 手动/CI | ✅ 自动执行 | 100% |
| Lint/Format | 仅 user 模块 CI | ✅ 每次变更自动执行 | 100% |
| 数据库迁移 | 手动 | ✅ 自动生成迁移文件 | 70% |
| Docker 构建 | 手动 | ✅ 自动构建 + 验证 | 90% |
| 部署 | 手动脚本 | ⚠️ 可触发，但需审批 | 50% |

## 四、关键缺失基础设施

在引入 claw-code 之前，以下基础设施缺失会导致自动化效果大打折扣：

1. **代码质量工具**：无 ruff/black 本地配置，无 pre-commit hooks
2. **测试框架**：无默认测试路径，无覆盖率配置
3. **CI 流水线**：仅 user 模块有 CI
4. **增量迁移**：只有单份 reset 迁移
5. **依赖管理**：CI 用 pip + requirements.txt（不存在），项目用 Poetry

**建议**：先补齐这些基础设施，再接入 claw-code，否则 Agent 生成的代码可能缺乏质量保障。
