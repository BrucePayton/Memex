# Select is not defined 错误修复记录

## 基本信息
- **发现时间**：2026-05-03
- **修复时间**：2026-05-03
- **影响范围**：外部资源管理页面
- **严重程度**：P0（页面完全无法访问）

## 问题现象
点击外部资源管理卡片时页面加载失败，控制台报错：`Select is not defined`

## 根因分析
1. **组件未导入**：`/web/src/features/external-resources/pages/ExternalResourcesPage.tsx`文件中多处使用了Select相关组件，但导入部分缺失
2. **错误注释**：代码中存在误导性注释"// Select已经导入，不需要重复导入"，导致问题被掩盖
3. **图标缺失**：同时发现`Bot`和`GitBranch`两个图标组件也未导入
4. **影响位置**：
   - 新建资源/平台对话框中的类型选择下拉框
   - 资源列表页面的平台筛选下拉框

## 修复方案
1. 添加Select组件完整导入：
   ```typescript
   import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
   ```
2. 补充图标导入：在lucide-react导入列表中添加`Bot`和`GitBranch`
3. 清理错误的注释说明

## 经验教训
1. **代码合并检查**：功能合并前需要完整测试页面加载和基本功能
2. **注释准确性**：代码注释需要保持准确，误导性注释比没有注释更危险
3. **导入完整性**：新增组件使用时必须同步添加导入声明，避免遗漏
4. **自动化校验**：建议在CI流程中添加TypeScript类型检查，提前发现此类错误

## 验证要点
- 外部资源管理页面正常加载，无控制台报错
- 新建/编辑对话框中的下拉选择功能正常
- 资源列表的平台筛选功能正常
- 页面图标显示正常
