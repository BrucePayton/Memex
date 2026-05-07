---
title: "MainSide通知中心功能恢复 - 代码回归后功能重建"
type: analysis
created: 2026-05-07
last_updated: 2026-05-07
source_count: 0
confidence: medium
status: active
tags:
  - notification
  - frontend
  - main-sidebar
  - feature-restoration
  - code-regression
  - askdata-platform
---


# MainSide通知中心功能恢复 - 代码回归后功能重建

## 问题背景

2026-05-07，用户报告MainSide首页右侧的铃铛图标及其通知中心功能在代码回归后缺失。该功能原本用于显示系统通知、任务通知、安全通知等，并支持标记已读、删除等操作。

## 现状分析

### 后端现状 - 完整可用

经检查，后端通知服务完全正常：

| 组件 | 文件位置 | 功能状态 |
|------|----------|----------|
| 通知服务 | `/core/modules/user/services/notification_service.py` | ✅ 完整 |
| API端点 | `/core/modules/user/views.py` (L561-707) | ✅ 完整 |
| 数据模型 | `UserNotification` | ✅ 完整 |

### 后端API端点清单

```
GET    /api/user/notifications
GET    /api/user/notifications/unread-count
PUT    /api/user/notifications/read
PUT    /api/user/notifications/read-all
DELETE /api/user/notifications/{notification_id}
POST   /api/user/notifications (admin only)
```

### 前端现状 - 缺失严重

| 组件 | 状态 |
|------|------|
| Bell图标 | ✅ 已在icon-mapping.ts中定义 |
| API客户端 | ❌ 缺失通知相关类型和方法 |
| Bell组件 | ❌ 完全缺失 |
| MainSidebar集成 | ❌ 缺失 |

## 实现方案

### Step 1: 扩展API客户端 - `user.api.ts`

**文件**: `/web/src/shared/api/user.api.ts`

**添加内容**:

1. **类型定义**:
   - `NotificationType` - 通知类型枚举: 'system' | 'task' | 'security' | 'custom'
   - `UserNotification` - 用户通知接口
   - `GetNotificationsResponse` - 获取通知列表响应
   - `GetUnreadCountResponse` - 获取未读数量响应
   - `MarkAsReadRequest` / `MarkAsReadResponse` - 标记已读请求/响应

2. **API方法**:
   - `notificationApi.getNotifications()` - 获取通知列表
   - `notificationApi.getUnreadCount()` - 获取未读数量
   - `notificationApi.markAsRead()` - 批量标记已读
   - `notificationApi.markAllAsRead()` - 全部标记已读
   - `notificationApi.deleteNotification()` - 删除通知

### Step 2: 创建通知Bell组件 - `NotificationBell.tsx`

**文件**: `/web/src/components/NotificationBell.tsx` (新建)

**功能特性**:

- **UI组件**:
  - Bell图标按钮，带未读计数Badge
  - 下拉面板显示通知列表
  - 通知项带类型图标（AlertCircle/Info/CheckCircle）
  - 操作按钮悬停显示（Check/Trash2）

- **状态管理**:
  ```typescript
  - unreadCount: number
  - notifications: UserNotification[]
  - isLoading: boolean
  - isPanelOpen: boolean
  - page: number
  - hasMore: boolean
  - isLoadingMore: boolean
  ```

- **核心功能**:
  - `fetchUnreadCount()` - 获取未读数，30秒轮询（仅在页面可见时）
  - `fetchNotifications(loadMore?)` - 获取通知列表，支持分页
  - `handleMarkAsRead()` / `handleMarkAllAsRead()` - 标记已读
  - `handleDeleteNotification()` - 删除通知
  - `handleNotificationClick()` - 点击通知（自动标记已读 + 跳转链接）

- **优化特性**:
  - 乐观UI更新（操作后立即更新UI，不等待API响应）
  - 页面可见性检测（隐藏时暂停轮询）
  - Sonner toast消息反馈

- **使用的图标**:
  - `Bell` - 主图标
  - `Check` - 已读标记
  - `Trash2` - 删除
  - `Clock` - 时间显示
  - `AlertCircle` / `Info` / `CheckCircle` - 根据通知类型
  - `ExternalLink` - 跳转链接指示器

### Step 3: 集成到MainSidebar

**文件**: `/web/src/components/MainSidebar.tsx`

**修改内容**:

在Header区域（原Logo区域）调整布局：

```typescript
<div className="p-6 border-b border-border">
  <div className="flex items-center justify-between"> {/* 改为justify-between */}
    <div className="flex items-center gap-3">
      {/* 原有Logo和标题 */}
    </div>
    <NotificationBell /> {/* 新增 */}
  </div>
</div>
```

## 文件变更清单

| 文件 | 操作 |
|------|------|
| `/web/src/shared/api/user.api.ts` | 修改 - 添加通知类型和API方法 |
| `/web/src/components/NotificationBell.tsx` | 新建 - 通知Bell组件 (418行) |
| `/web/src/components/MainSidebar.tsx` | 修改 - 集成Bell组件 |

## 验证计划

1. ✅ 页面加载后显示Bell图标
2. ✅ 点击Bell打开通知面板
3. ✅ 显示未读通知计数Badge
4. ✅ 可以标记单个/全部通知已读
5. ✅ 可以删除通知
6. ✅ 如果有action_url，点击通知可以跳转
7. ✅ 30秒自动刷新未读数（或操作后立即刷新）
8. ✅ 使用Sonner显示操作反馈

## 技术要点

### 1. 轮询优化

使用 `document.visibilityState` 检测页面可见性，仅在页面可见时进行30秒轮询，节省资源：

```typescript
useEffect(() => {
  const handleVisibilityChange = () => {
    if (document.visibilityState === 'visible') {
      fetchUnreadCount();
      pollingTimerRef.current = setInterval(fetchUnreadCount, 30000);
    } else {
      if (pollingTimerRef.current) {
        clearInterval(pollingTimerRef.current);
      }
    }
  };
  // ...
}, [fetchUnreadCount]);
```

### 2. 乐观更新

所有写操作都采用乐观更新模式，先更新UI，再调用API，提升用户体验：

```typescript
// 标记已读
setNotifications(prev => prev.map(n => 
  n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n
));
setUnreadCount(prev => Math.max(0, prev - 1));
// 然后调用API...
```

### 3. 通知类型映射

```typescript
const NotificationIconMap: Record&lt;NotificationType, React.ElementType&gt; = {
  system: AlertCircle,
  task: CheckCircle,
  security: Info,
  custom: Info,
};

const NotificationColorMap: Record&lt;NotificationType, string&gt; = {
  system: 'text-blue-500',
  task: 'text-green-500',
  security: 'text-orange-500',
  custom: 'text-gray-500',
};
```

## Git提交

```
feat: 恢复MainSide通知中心功能

- 添加通知API客户端(user.api.ts)
- 创建NotificationBell组件
- 集成到MainSidebar头部

功能：
- 铃铛图标带未读计数Badge
- 下拉通知面板
- 标记单个/全部已读
- 删除通知
- 分页加载
- 30秒轮询未读数
```

## 经验总结

1. **先验证后端** - 功能恢复前先确认后端是否完整，避免重复工作
2. **复用已有组件** - 项目已有Button/Badge/DropdownMenu等UI组件，直接使用
3. **遵循现有模式** - API客户端扩展遵循现有user.api.ts的代码风格
4. **用户体验优先** - 乐观更新、页面可见性检测等细节提升体验
5. **功能完整性** - 不仅恢复UI，还要确保所有交互（标记已读、删除、分页等）都正常


