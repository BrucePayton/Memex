# Select.Item 空字符串 value 错误修复记录

## 基本信息
- **发现时间**：2026-05-03
- **修复时间**：2026-05-03
- **影响范围**：外部资源管理页面的平台筛选功能
- **严重程度**：P0（页面完全无法访问）

## 问题现象
页面加载失败，控制台报错：
```
A <Select.Item /> must have a value prop that is not an empty string. This is because the Select value can be set to an empty string to clear the selection and show the placeholder.
```

## 根因分析
在平台筛选的Select组件中，"全部平台"选项使用了空字符串作为value：
```typescript
<SelectItem value="">全部平台</SelectItem>
```
违反了Radix UI Select组件的约束：Select.Item的value属性不能是空字符串。

## 修复方案
1. 将空字符串value改为非空值`'all'`：
   ```typescript
   <SelectItem value="all">全部平台</SelectItem>
   ```
2. 调整value映射逻辑：
   ```typescript
   <Select
     value={selectedPlatformFilter === null ? 'all' : selectedPlatformFilter.toString()}
     onValueChange={(value) => {
       if (value === 'all') {
         setSelectedPlatformFilter(null);
       } else if (value === 'manual') {
         setSelectedPlatformFilter('manual');
       } else {
         setSelectedPlatformFilter(parseInt(value, 10));
       }
     }}
   >
   ```

## 经验教训
1. **组件约束遵守**：使用第三方组件时必须严格遵守其API约束，尤其是关于必填属性和格式要求
2. **空值处理**：Select组件的空值逻辑应该通过显式的特殊值（如'all'）来处理，而不是使用空字符串
3. **类型安全**：在处理不同类型的value时，要确保类型转换的正确性，避免出现运行时错误

## 验证要点
- 外部资源管理页面正常加载，无控制台报错
- 平台筛选功能正常工作：
  - "全部平台"选项可以正常选中，显示所有资源
  - "手动录入"选项可以正常筛选，只显示手动添加的资源
  - 各个平台选项可以正常筛选，只显示对应平台的资源
- 筛选逻辑与原有功能完全一致
