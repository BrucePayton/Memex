---
title: "前端构建失败-NotificationBell-HTML实体编码问题排查"
type: analysis
created: 2026-05-07
last_updated: 2026-05-07
source_count: 0
confidence: medium
status: active
tags:
  - frontend
  - typescript
  - build
  - esbuild
  - html-entities
---


---
title: 前端构建失败-NotificationBell-HTML实体编码问题排查
type: analysis
date: 2026-05-07
tags: [frontend, typescript, build, esbuild, html-entities]
---

## 问题现象

前端 Docker 构建失败，esbuild 报错：
```
> [askdata_frontend build-stage 6/7] RUN npm run build:production
error during build:
[vite:esbuild] Transform failed with 1 error:
/app/src/components/NotificationBell.tsx:72:19: ERROR: Expected ")" but found ":"

Expected ")" but found ":"
70 |  }: {
71 |    notification: UserNotification;
72 |    onMarkAsRead: (id: number) =&gt; void;
   |                     ^
73 |    onDelete: (id: number) =&gt; void;
74 |  }) {
```

注意错误位置显示的是 `=&gt;` 而不是正常的 `=>`。

## 根因分析

### 问题定位

通过检查 `web/src/components/NotificationBell.tsx` 文件，发现整个文件的 TypeScript 代码被错误地进行了 HTML 实体编码：

| 原始字符 | 被编码成 |
|---------|--------|
| `=>` | `=&gt;` |
| `<` | `&lt;` |
| `>` | `&gt;` |
| `&` | `&amp;` |

例如，第 72 行实际内容是：
```typescript
onMarkAsRead: (id: number) =&gt; void;
```

而应该是：
```typescript
onMarkAsRead: (id: number) => void;
```

### 可能原因

1. **复制粘贴错误**：从网页或富文本编辑器中复制代码时，内容被 HTML 转义
2. **Markdown 渲染问题**：可能是经过了错误的 Markdown 处理流程
3. **工具链问题**：某个处理步骤错误地对代码进行了 HTML 实体编码

## 解决方案

### 批量修复 HTML 实体编码

使用 sed 批量替换文件中的实体编码：

```bash
cd web/src/components
sed -i '' 's/=&gt;/=>/g; s/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g' NotificationBell.tsx
```

或者使用其他方式替换：
- `=&gt;` → `=>`（箭头函数）
- `&lt;` → `<`（泛型、JSX标签）
- `&gt;` → `>`（泛型、JSX标签）
- `&amp;` → `&`（逻辑与）

### 验证修复

修复后检查关键语法正常：
```typescript
function NotificationItem({
  notification,
  onMarkAsRead,
  onDelete,
}: {
  notification: UserNotification;
  onMarkAsRead: (id: number) => void;
  onDelete: (id: number) => void;
}) {
  // ...
}
```

## 修改的文件

- `web/src/components/NotificationBell.tsx` - 修复 HTML 实体编码问题

## 经验总结

1. **检查整个项目范围**：如果一个文件出现这种问题，要检查其他文件是否也有类似问题
   ```bash
   grep -r "=&gt;" web/src --include="*.tsx" --include="*.ts"
   ```

2. **git 检查帮助定位问题**：通过 `git status` 和 `git diff` 可以发现异常变更

3. **复制代码注意来源**：从网页复制代码时，最好先粘贴到纯文本编辑器中转一道
4. **编辑器设置**：确保编辑器以纯文本模式编辑代码，不要用富文本模式

4. **预防措施**：
   - 使用 git 追踪变更，及时发现异常
   - 复制代码后先检查特殊字符是否正常
   - 优先使用 IDE 的代码片段而非网页内容

## 验证方法

```bash
# 1. 检查是否还有 HTML 实体编码
grep -n "=&gt;" web/src/components/NotificationBell.tsx

# 2. 本地尝试构建（如果有本地环境）
cd web/
npm run build:production

# 3. 或者重新运行 Docker 构建
cd deployments/deployment_local/
docker-compose build askdata-frontend
```

## 相关文件

- `web/src/components/NotificationBell.tsx` - 问题和修复位置

