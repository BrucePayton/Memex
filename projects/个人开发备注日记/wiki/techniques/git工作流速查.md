---
title: "Git工作流速查"
type: technique
created: 2026-04-30
last_updated: 2026-04-30
source_count: 0
confidence: medium
status: active
tags: []
---

# Git工作流速查

> 从 Apple Notes 中提取的 Git 操作要点

## 远程仓库操作

### 修改远程URL (含Token)
```bash
git remote set-url origin https://<user>:<token>@github.com/<user>/<repo>.git
```

### 拉取远程分支
```bash
git fetch origin
git checkout -b <branch> origin/<branch>
```

## 常用工作流

```bash
git status      # 查看状态
git add .       # 添加文件
git commit -m "message"  # 提交
git push origin <branch>  # 推送
git pull origin <branch>  # 拉取
```

## Token 认证

- GitHub PAT: github_pat_xxx
- 格式: https://user:token@github.com/...
- 注意: Token 不要提交到仓库

## 相关页面

- [[Docker部署模式]] — 容器部署
- [[数据库操作速查]] — 数据库查询

