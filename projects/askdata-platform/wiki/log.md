---
title: Changelog
type: log
---

# Changelog

| Date | Source | Summary |
|------|--------|---------|
| 2026-05-07 | 部署修复 | nginx配置重复指令问题彻底解决：移除include模式，每个location显式配置所有proxy指令，避免proxy_buffering/proxy_read_timeout等重复错误 |
| 2026-05-07 | 开发修复 | Wiki Memex 对标优化 Phase 1-4 完成：RAW 文件展示、路由守卫、返回导航、页面列表一致性、文档数量、Wiki 统计、工具栏折叠、健康指示器、LLM 连通性检测 |
| 2026-05-04 | 代码库扫描 | 内容层报告生成功能问题分析：发现核心实现完整但API路由未注册的关键问题 |
| 2026-05-04 | 代码库扫描 | Claw Code 实现审计：实际实现 vs wiki 分析的偏差分析。发现实现方向从 Rust CLI 集成偏移为 Python 原生内嵌，PolicyEngine/BranchLock 已实现但孤立 |
| 2026-05-05 | 开发规划 | 成果物文本自适应与导出能力建设规划：Pretext 文本自适应工具链 Phase 1-2 完成，规划 Phase 2.5（气泡布局优化）/ Phase 3.1（Canvas 报告渲染器）/ Phase 3.2（后端 PDF CJK）/ Phase 3.3（看板截图导出） |
