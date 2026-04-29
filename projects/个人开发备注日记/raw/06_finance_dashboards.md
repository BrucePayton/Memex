# 06 Finance Dashboards

*12 notes grouped from Apple Notes*

---

## FlowAdaptationOut global context  文档类型 寿险机构集中项目年结决算工作通知书 术语  年结 指 

# FlowAdaptationOut(global_context='文档类型：寿险机构集中项目年结决算工作通知书。术语：‘年结’指…

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p129 -->

<div>FlowAdaptationOut(global_context='文档类型：寿险机构集中项目年结决算工作通知书。术语：‘年结’指年度会计决算；‘预提’指提前确认费用；‘关账’指系统关闭并数据锁定。关键引用：‘12月19日18:00截止’、‘费用-NEWFAS报销模块关闭’、‘1月3日为总账期间关闭时间’。歧义：部分模块关闭时间未明确具体时点（如‘系统关闭时点’）。', framework_branch_brief='起点：年结工作启动。主路径：各模块按截止时间完成任务→系统关闭→账务核对→税金处理→最终关账。并行：预算、费用、总账、税务等模块可并行执行（fork→[预算, 费用, 总账, 税务]→join）。条件分支：如预提费用需总部审批，涉及特殊场景的流程调整。边界约束：从12月19日开始至1月3日结束，各步骤需在指定时间节点前完成。', systems_branch_brief='系统：E采购（预算模块）、后援AP（费用模块）、NEWFAS报销模块（费用模块）、LAS、CDS、TMS、综合财务平台（总账模块）、财智云费用分摊模块（往来账务模块）、OF系统（过账与制证）。数据库：科目余额表、待摊费用台账、往来科目表、税金科目表。工具：Excel模板（如印花税测算底稿）、邮件/会签平台（用于签报审核）、即时通讯群组（用于远程费用联动）。接口：E采购与预算系统集成、后援AP与费用系统集成、NEWFAS与OF系统集成。挂靠步骤：s-budget-e-purchase、s-expense-ap-scan、s-expense-newfas-close、s-accounting-verification、s-tax-adjustment。', risks_branch_brief='步骤‘费用-NEWFAS报销模块关闭’存在逾期风险（12月31日18:00截止）；步骤‘分摊流程创建’若未在1月1日前完成，可能导致往来账务延迟；步骤‘TMS系统关闭’若未按注1要求操作，可能引发数据异常；步骤‘增值税附加税手工计提’若未在1月3日前完成，影响税金准确性；并行支线若未全部到达 join，可能导致数据不一致。', future_dimensions={})</div>

---

##   模板位置 assets dashboard chart card template py

# # 模板位置：assets/dashboard/chart_card_template.py

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p119 -->

<div>        # 模板位置：assets/dashboard/chart_card_template.py</div>
<div>        # 主题位置：assets/dashboard/themes/</div>
<div><br></div>
<div>        from dash import dcc</div>
<div>        import plotly.graph_objects as go</div>
<div>        from assets.dashboard.chart_card_template import create_chart_card</div>
<div>        from assets.dashboard.themes.dark_business import DARK_BUSINESS_THEME, CHART_STYLES, PLOTLY_TEMPLATE</div>
<div>        from assets.dashboard.themes.light_professional import LIGHT_PROFESSIONAL_THEME</div>
<div><br></div>
<div>        # 根据 dashboard_color_style 选择主题</div>
<div>        if &quot深色&quot in dashboard_color_style or &quot暗黑&quot in dashboard_color_style:</div>
<div>            theme = DARK_BUSINESS_THEME</div>
<div>        else:</div>
<div>            theme = LIGHT_PROFESSIONAL_THEME</div>
<div><br></div>
<div>        # 方法 1: 使用模板函数创建图表卡片（推荐方式）</div>
<div>        chart_card = create_chart_card(</div>
<div>            title=&quot利润表瀑布 · 收入至净利润&quot,</div>
<div>            chart_component=create_waterfall_figure(data),  # dcc.Graph 组件</div>
<div>            icon=&quotfa-water&quot,                                # Font Awesome 图标</div>
<div>            notes=[&quotEBITDA ¥2,410&quot, &quot折旧/摊销 ¥295&quot],     # 底部注释（可选）</div>
<div>            style_theme=theme['chart_styles']</div>
<div>        )</div>

---

##  1    设计名称生成    根据 dashboard title layout design 和 autofit color design 

# '1. **设计名称生成**: 根据 dashboard_title、layout_design 和 autofit_color_design…

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p115 -->

<div>'1. **设计名称生成**: 根据 dashboard_title、layout_design 和 autofit_color_design 组合为驼峰命名 `FinancialSharedCenterRevenueOverviewClassicThreeLayerBlueBusiness`。\n2. **布局结构**: 严格遵循“经典三层”规范。顶部 Header 包含标题与元数据；中间层分为 KPI 行和图表网格区；底部 Footer 包含数据来源。\n3. **响应式设计**: 使用 Flexbox (`display: flex`, `flexWrap: wrap`) 实现自适应。KPI 卡片自动换行，图表区域采用 `flex: 2` (主图) 和 `flex: 1` (侧图) 的比例分配，确保在不同屏幕尺寸下均能良好展示。\n4. **视觉风格**: 统一应用“蓝色商务风”。背景色使用浅蓝灰 (`#f0f4f8`)，卡片使用白色半透明配合 `backdrop-filter: blur` 实现毛玻璃效果。圆角统一为 `28px` (KPI) 和 `32px` (图表)，增强现代感。\n5. **组件集成**: 将输入的 KPI 数据和图表逻辑封装为独立函数或变量，保持代码模块化。虽然输入中提到了热力图任务，但鉴于未提供具体组件代码，为保证可运行性，优先组装了提供的 4 个核心图表，并保留了热力图任务的逻辑位置（在注释中说明）。\n6. **图标与交互**: 引入 Font Awesome CDN，为每个章节添加对应图标，提升可读性。图表配置了 hover 提示和响应式设置。'</div>

---

##    title    财务状况分析    status    confirmed    section id    sec 01 

# [{"title": "财务状况分析", "status": "confirmed", "section_id": "sec_01…

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p67 -->

<div>[{&quottitle&quot: &quot财务状况分析&quot, &quotstatus&quot: &quotconfirmed&quot, &quotsection_id&quot: &quotsec_01&quot, &quotdescription&quot: &quot本章节将分析2024年第一季度北京和上海地区的销售收入趋势。&quot, &quotsub_sections&quot: [{&quottitle&quot: &quot北京地区销售趋势&quot, &quotstatus&quot: &quotconfirmed&quot, &quotsection_id&quot: &quotsec_01_01&quot, &quotdescription&quot: &quot分析北京地区产品A在2024年第一季度的销售收入波动情况。&quot, &quotsupporting_facts&quot: [&quotF-Q001&quot, &quotF-Q002&quot, &quotF-Q003&quot]}, {&quottitle&quot: &quot上海地区销售趋势&quot, &quotstatus&quot: &quotconfirmed&quot, &quotsection_id&quot: &quotsec_01_02&quot, &quotdescription&quot: &quot分析上海地区产品B在2024年第一季度的销售收入增长情况。&quot, &quotsupporting_facts&quot: [&quotF-Q004&quot, &quotF-Q005&quot, &quotF-Q006&quot]}], &quotdata_coverage&quot: &quot充分&quot, &quotexpected_depth&quot: &quotdetailed&quot, &quotsupporting_facts&quot: [&quotF-Q001&quot, &quotF-Q002&quot, &quotF-Q003&quot, &quotF-Q004&quot, &quotF-Q005&quot, &quotF-Q006&quot]}, {&quottitle&quot: &quot市场地位与行业趋势&quot, &quotstatus&quot: &quotconfirmed&quot, &quotsection_id&quot: &quotsec_02&quot, &quotdescription&quot: &quot本章节将分析行业整体趋势、市场规模及增长率。&quot, &quotsub_sections&quot: [{&quottitle&quot: &quot行业整体趋势&quot, &quotstatus&quot: &quotconfirmed&quot, &quotsection_id&quot: &quotsec_02_01&quot, &quotdescription&quot: &quot分析行业整体呈现的上升趋势。&quot, &quotsupporting_facts&quot: [&quotF-D001&quot]}, {&quottitle&quot: &quot市场规模与增长率&quot, &quotstatus&quot: &quotconfirmed&quot, &quotsection_id&quot: &quotsec_02_02&quot, &quotdescription&quot: &quot分析市场规模约1000亿元及年增长率约15%的情况。&quot, &quotsupporting_facts&quot: [&quotF-Q007&quot, &quotF-Q008&quot]}], &quotdata_coverage&quot: &quot充分&quot, &quotexpected_depth&quot: &quotdetailed&quot, &quotsupporting_facts&quot: [&quotF-D001&quot, &quotF-Q007&quot, &quotF-Q008&quot]}, {&quottitle&quot: &quot预留：可能的新发现&quot, &quotstatus&quot: &quotplaceholder&quot, &quotsection_id&quot: &quotsec_placeholder&quot, &quotdescription&quot: &quotAdvanced 阶段如发现重要新线索，可在此位置新增章节&quot, &quotsub_sections&quot: [], &quotdata_coverage&quot: &quot无&quot}]</div>

---

##   charts      reasoning    数据非空 基于 sample rows 提取 label field 与 value field 

# {"charts": [{"reasoning": "数据非空，基于 sample_rows 提取 label_field 与 value_field…

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p120 -->

<div>{&quotcharts&quot: [{&quotreasoning&quot: &quot数据非空，基于 sample_rows 提取 label_field 与 value_field 映射；income_ratio_pct 为百分比值，适合作为饼图数值；字段名需显式绑定至 canonical runtime keys。&quot, &quotelapsed_ms&quot: 4144, &quoterror_type&quot: &quot&quot, &quotfigure_dict&quot: {&quotdata&quot: [{&quotlabel_field&quot: &quot综合&quot, &quotvalue_field&quot: 23.94}, {&quotlabel_field&quot: &quot费用&quot, &quotvalue_field&quot: 22.24}, {&quotlabel_field&quot: &quot估值&quot, &quotvalue_field&quot: 19.15}, {&quotlabel_field&quot: &quot财税&quot, &quotvalue_field&quot: 18.18}, {&quotlabel_field&quot: &quot资金&quot, &quotvalue_field&quot: 16.49}], &quotnotes&quot: [&quot综合与费用产品线合计占比超46%，为核心收入来源；资金产品线占比最低，属长尾。&quot], &quottitle&quot: &quot产品线收入占比&quot, &quotsubtitle&quot: &quot2025年各产品线收入贡献分布&quot, &quotcard_size&quot: &quot1x1&quot, &quotchart_type&quot: &quotresponse_pie_chart&quot, &quotfield_bindings&quot: {&quotlabel_field&quot: &quotproduct_line&quot, &quotvalue_field&quot: &quotincome_ratio_pct&quot}, &quotwrapped_in_card&quot: true}, &quotcomponent_id&quot: &quotchart-0006-9e494a&quot, &quoterror_message&quot: &quot&quot, &quotused_fallback&quot: false, &quotcomponent_code&quot: &quotchart_0006_9e494a_graph = create_chart_from_strategy(\n    chart_type='response_pie_chart',\n    data=[{'label_field': '综合', 'value_field': 23.94},\n {'label_field': '费用', 'value_field': 22.24},\n {'label_field': '估值', 'value_field': 19.15},\n {'label_field': '财税', 'value_field': 18.18},\n {'label_field': '资金', 'value_field': 16.49}],\n    style_theme=theme,\n    label_field='product_line',\n    value_field='income_ratio_pct',\n)\nchart_0006_9e494a = create_chart_card(\n    title='产品线收入占比',\n    subtitle='2025年各产品线收入贡献分布',\n    chart_component=chart_0006_9e494a_graph,\n    icon='fa-chart-pie',\n    notes=['综合与费用产品线合计占比超46%，为核心收入来源；资金产品线占比最低，属长尾。'],\n    style_theme=theme,\n    card_size='1x1',\n    card_id='chart-0006-9e494a',\n)&quot, &quotgeneration_status&quot: &quotsuccess&quot}, {&quotreasoning&quot: &quot数据来自真实SQL执行结果，含8条样本行；因截断仅展示前2个月数据，仍满足趋势图最小可视化需求&quot, &quotelapsed_ms&quot: 6581, &quoterror_type&quot: &quot&quot, &quotfigure_dict&quot: {&quotdata&quot: [{&quotmonth&quot: &quot2025-01&quot, &quotproduct_line&quot: &quot综合&quot, &quotmonthly_income_in_wan&quot: 4.6125}, {&quotmonth&quot: &quot2025-01&quot, &quotproduct_line&quot: &quot费用&quot, &quotmonthly_income_in_wan&quot: 3.97}, {&quotmonth&quot: &quot2025-01&quot, &quotproduct_line&quot: &quot估值&quot, &quotmonthly_income_in_wan&quot: 3.7175}, {&quotmonth&quot: &quot2025-01&quot, &quotproduct_line&quot: &quot资金&quot, &quotmonthly_income_in_wan&quot: 3.28}, {&quotmonth&quot: &quot2025-01&quot, &quotproduct_line&quot: &quot财税&quot, &quotmonthly_income_in_wan&quot: 3.25}, {&quotmonth&quot: &quot2025-02&quot, &quotproduct_line&quot: &quot费用&quot, &quotmonthly_income_in_wan&quot: 2.625}, {&quotmonth&quot: &quot2025-02&quot, &quotproduct_line&quot: &quot综合&quot, &quotmonthly_income_in_wan&quot: 1.97}, {&quotmonth&quot: &quot2025-02&quot, &quotproduct_line&quot: &quot估值&quot, &quotmonthly_income_in_wan&quot: 1.95}], &quotnotes&quot: [&quot按月分产品线展示收入趋势，用于识别季节性波动与拐点&quot], &quottitle&quot: &quot产品线收入月度趋势（万元）&quot, &quotsubtitle&quot: &quot2025年1-2月（样本数据）&quot, &quotcard_size&quot: &quot1x1&quot, &quotchart_type&quot: &quotresponse_line_chart&quot, &quotfield_bindings&quot: {&quotx_field&quot: &quotmonth&quot, &quoty_field&quot: &quotmonthly_income_in_wan&quot, &quotseries_field&quot: &quotproduct_line&quot}, &quotwrapped_in_card&quot: true}, &quotcomponent_id&quot: &quotchart-0007-517996&quot, &quoterror_message&quot: &quot&quot, &quotused_fallback&quot: false, &quotcomponent_code&quot: &quotchart_0007_517996_graph = create_chart_from_strategy(\n    chart_type='response_line_chart',\n    data=[{'month': '2025-01', 'product_line': '综合', 'monthly_income_in_wan': 4.6125},\n {'month': '2025-01', 'product_line': '费用', 'monthly_income_in_wan': 3.97},\n {'month': '2025-01', 'product_line': '估值', 'monthly_income_in_wan': 3.7175},\n {'month': '2025-01', 'product_line': '资金', 'monthly_income_in_wan': 3.28},\n {'month': '2025-01', 'product_line': '财税', 'monthly_income_in_wan': 3.25},\n {'month': '2025-02', 'product_line': '费用', 'monthly_income_in_wan': 2.625},\n {'month': '2025-02', 'product_line': '综合', 'monthly_income_in_wan': 1.97},\n {'month': '2025-02', 'product_line': '估值', 'monthly_income_in_wan': 1.95}],\n    style_theme=theme,\n    x_field='month',\n    y_field='monthly_income_in_wan',\n    series_field='product_line',\n)\nchart_0007_517996 = create_chart_card(\n    title='产品线收入月度趋势（万元）',\n    subtitle='2025年1-2月（样本数据）',\n    chart_component=chart_0007_517996_graph,\n    icon='fa-chart-line',\n    notes=['按月分产品线展示收入趋势，用于识别季节性波动与拐点'],\n    style_theme=theme,\n    card_size='1x1',\n    card_id='chart-0007-517996',\n)&quot, &quotgeneration_status&quot: &quotsuccess&quot}, {&quotreasoning&quot: &quot数据来自真实SQL执行结果，共5行有效记录；使用response_bar_chart适配横向柱状图展示产品线收入对比；字段已按canonical映射绑定x_field/y_field。&quot, &quotelapsed_ms&quot: 6141, &quoterror_type&quot: &quot&quot, &quotfigure_dict&quot: {&quotdata&quot: [{&quotproduct_line&quot: &quot综合&quot, &quottotal_income_in_wan&quot: 11.7165}, {&quotproduct_line&quot: &quot费用&quot, &quottotal_income_in_wan&quot: 10.885}, {&quotproduct_line&quot: &quot估值&quot, &quottotal_income_in_wan&quot: 9.3735}, {&quotproduct_line&quot: &quot财税&quot, &quottotal_income_in_wan&quot: 8.896}, {&quotproduct_line&quot: &quot资金&quot, &quottotal_income_in_wan&quot: 8.07}], &quotnotes&quot: [&quotTop 5产品线合计占比超50%，资源倾斜空间显著&quot], &quottitle&quot: &quot产品线收入Top-N排名（万元）&quot, &quotsubtitle&quot: &quot2025年累计收入，聚焦头部产品线&quot, &quotcard_size&quot: &quot1x1&quot, &quotchart_type&quot: &quotresponse_bar_chart&quot, &quotfield_bindings&quot: {&quotx_field&quot: &quotproduct_line&quot, &quoty_field&quot: &quottotal_income_in_wan&quot}, &quotwrapped_in_card&quot: true}, &quotcomponent_id&quot: &quotchart-0008-4f010c&quot, &quoterror_message&quot: &quot&quot, &quotused_fallback&quot: false, &quotcomponent_code&quot: &quotchart_0008_4f010c_graph = create_chart_from_strategy(\n    chart_type='response_bar_chart',\n    data=[{'product_line': '综合', 'total_income_in_wan': 11.7165},\n {'product_line': '费用', 'total_income_in_wan': 10.885},\n {'product_line': '估值', 'total_income_in_wan': 9.3735},\n {'product_line': '财税', 'total_income_in_wan': 8.896},\n {'product_line': '资金', 'total_income_in_wan': 8.07}],\n    style_theme=theme,\n    x_field='product_line',\n    y_field='total_income_in_wan',\n)\nchart_0008_4f010c = create_chart_card(\n    title='产品线收入Top-N排名（万元）',\n    subtitle='2025年累计收入，聚焦头部产品线',\n    chart_component=chart_0008_4f010c_graph,\n    icon='fa-chart-bar',\n    notes=['Top 5产品线合计占比超50%，资源倾斜空间显著'],\n    style_theme=theme,\n    card_size='1x1',\n    card_id='chart-0008-4f010c',\n)&quot, &quotgeneration_status&quot: &quotsuccess&quot}, {&quotreasoning&quot: &quot数据非空，含5个产品线的收入与作业量指标，可构成有效散点图；x轴为作业量，y轴为收入，系列字段为产品线名称。&quot, &quotelapsed_ms&quot: 20568, &quoterror_type&quot: &quot&quot, &quotfigure_dict&quot: {&quotdata&quot: [{&quottotal_qty&quot: 930.0, &quotproduct_line&quot: &quot综合&quot, &quottotal_income_in_wan&quot: 11.7165}, {&quottotal_qty&quot: 740.0, &quotproduct_line&quot: &quot费用&quot, &quottotal_income_in_wan&quot: 10.885}, {&quottotal_qty&quot: 450.0, &quotproduct_line&quot: &quot估值&quot, &quottotal_income_in_wan&quot: 9.3735}, {&quottotal_qty&quot: 308.0, &quotproduct_line&quot: &quot财税&quot, &quottotal_income_in_wan&quot: 8.896}, {&quottotal_qty&quot: 381.0, &quotproduct_line&quot: &quot资金&quot, &quottotal_income_in_wan&quot: 8.07}], &quotnotes&quot: [&quot散点位置反映单位作业量产出效率；高收入高作业量需关注资源匹配。&quot], &quottitle&quot: &quot产品线收入与作业量相关性&quot, &quotsubtitle&quot: &quot2025年各产品线收入（万元） vs 作业量&quot, &quotcard_size&quot: &quot1x1&quot, &quotchart_type&quot: &quotresponse_scatter_plot&quot, &quotfield_bindings&quot: {&quotx_field&quot: &quottotal_qty&quot, &quoty_field&quot: &quottotal_income_in_wan&quot, &quotseries_field&quot: &quotproduct_line&quot}, &quotwrapped_in_card&quot: true}, &quotcomponent_id&quot: &quotchart-0009-156a8c&quot, &quoterror_message&quot: &quot&quot, &quotused_fallback&quot: false, &quotcomponent_code&quot: &quotchart_0009_156a8c_graph = create_chart_from_strategy(\n    chart_type='response_scatter_plot',\n    data=[{'product_line': '综合', 'total_income_in_wan': 11.7165, 'total_qty': 930.0},\n {'product_line': '费用', 'total_income_in_wan': 10.885, 'total_qty': 740.0},\n {'product_line': '估值', 'total_income_in_wan': 9.3735, 'total_qty': 450.0},\n {'product_line': '财税', 'total_income_in_wan': 8.896, 'total_qty': 308.0},\n {'product_line': '资金', 'total_income_in_wan': 8.07, 'total_qty': 381.0}],\n    style_theme=theme,\n    x_field='total_qty',\n    y_field='total_income_in_wan',\n    series_field='product_line',\n)\nchart_0009_156a8c = create_chart_card(\n    title='产品线收入与作业量相关性',\n    subtitle='2025年各产品线收入（万元） vs 作业量',\n    chart_component=chart_0009_156a8c_graph,\n    icon='fa-chart-scatter',\n    notes=['散点位置反映单位作业量产出效率；高收入高作业量需关注资源匹配。'],\n    style_theme=theme,\n    card_size='1x1',\n    card_id='chart-0009-156a8c',\n)&quot, &quotgeneration_status&quot: &quotsuccess&quot}, {&quotreasoning&quot: &quot数据来自真实SQL执行结果，共8条样本行，按type1（白名单/非白）分组展示各产品线收入；使用response_column_chart符合分组柱状图语义，series_field用于区分白名单状态。&quot, &quotelapsed_ms&quot: 8958, &quoterror_type&quot: &quot&quot, &quotfigure_dict&quot: {&quotdata&quot: [{&quottype1&quot: &quot白名单&quot, &quotproduct_line&quot: &quot估值&quot, &quottotal_income_in_wan&quot: 3.26}, {&quottype1&quot: &quot白名单&quot, &quotproduct_line&quot: &quot综合&quot, &quottotal_income_in_wan&quot: 2.84}, {&quottype1&quot: &quot白名单&quot, &quotproduct_line&quot: &quot财税&quot, &quottotal_income_in_wan&quot: 2.45}, {&quottype1&quot: &quot白名单&quot, &quotproduct_line&quot: &quot费用&quot, &quottotal_income_in_wan&quot: 2.01}, {&quottype1&quot: &quot白名单&quot, &quotproduct_line&quot: &quot资金&quot, &quottotal_income_in_wan&quot: 1.64}, {&quottype1&quot: &quot非白&quot, &quotproduct_line&quot: &quot综合&quot, &quottotal_income_in_wan&quot: 8.8765}, {&quottype1&quot: &quot非白&quot, &quotproduct_line&quot: &quot费用&quot, &quottotal_income_in_wan&quot: 8.875}, {&quottype1&quot: &quot非白&quot, &quotproduct_line&quot: &quot财税&quot, &quottotal_income_in_wan&quot: 6.446}], &quotnotes&quot: [&quot白名单服务聚焦战略高价值产品线；非白名单服务以综合与费用类为主，收入规模更高。&quot], &quottitle&quot: &quot产品线收入按白名单状态分布（万元）&quot, &quotsubtitle&quot: &quot2025年数据&quot, &quotcard_size&quot: &quot1x1&quot, &quotchart_type&quot: &quotresponse_column_chart&quot, &quotfield_bindings&quot: {&quotx_field&quot: &quotproduct_line&quot, &quoty_field&quot: &quottotal_income_in_wan&quot, &quotseries_field&quot: &quottype1&quot}, &quotwrapped_in_card&quot: true}, &quotcomponent_id&quot: &quotchart-0010-2d866a&quot, &quoterror_message&quot: &quot&quot, &quotused_fallback&quot: false, &quotcomponent_code&quot: &quotchart_0010_2d866a_graph = create_chart_from_strategy(\n    chart_type='response_column_chart',\n    data=[{'type1': '白名单', 'product_line': '估值', 'total_income_in_wan': 3.26},\n {'type1': '白名单', 'product_line': '综合', 'total_income_in_wan': 2.84},\n {'type1': '白名单', 'product_line': '财税', 'total_income_in_wan': 2.45},\n {'type1': '白名单', 'product_line': '费用', 'total_income_in_wan': 2.01},\n {'type1': '白名单', 'product_line': '资金', 'total_income_in_wan': 1.64},\n {'type1': '非白', 'product_line': '综合', 'total_income_in_wan': 8.8765},\n {'type1': '非白', 'product_line': '费用', 'total_income_in_wan': 8.875},\n {'type1': '非白', 'product_line': '财税', 'total_income_in_wan': 6.446}],\n    style_theme=theme,\n    x_field='product_line',\n    y_field='total_income_in_wan',\n    series_field='type1',\n)\nchart_0010_2d866a = create_chart_card(\n    title='产品线收入按白名单状态分布（万元）',\n    subtitle='2025年数据',\n    chart_component=chart_0010_2d866a_graph,\n    icon='fa-chart-column',\n    notes=['白名单服务聚焦战略高价值产品线；非白名单服务以综合与费用类为主，收入规模更高。'],\n    style_theme=theme,\n    card_size='1x1',\n    card_id='chart-0010-2d866a',\n)&quot, &quotgeneration_status&quot: &quotsuccess&quot}, {&quotreasoning&quot: &quot数据来自真实 SQL 查询结果，含 5 行区域-产品线交叉收入记录；按 heatmap 规范映射为 x_field（area）、y_field（product_line）、value_field（total_income_in_wan）。&quot, &quotelapsed_ms&quot: 11784, &quoterror_type&quot: &quot&quot, &quotfigure_dict&quot: {&quotdata&quot: [{&quotarea&quot: &quot上海&quot, &quotproduct_line&quot: &quot估值&quot, &quottotal_income_in_wan&quot: 9.3735}, {&quotarea&quot: &quot内江&quot, &quotproduct_line&quot: &quot资金&quot, &quottotal_income_in_wan&quot: 8.07}, {&quotarea&quot: &quot合肥&quot, &quotproduct_line&quot: &quot费用&quot, &quottotal_income_in_wan&quot: 10.885}, {&quotarea&quot: &quot成都&quot, &quotproduct_line&quot: &quot财税&quot, &quottotal_income_in_wan&quot: 8.896}, {&quotarea&quot: &quot深圳&quot, &quotproduct_line&quot: &quot综合&quot, &quottotal_income_in_wan&quot: 11.7165}], &quotnotes&quot: [&quot数据单位：万元；用于识别区域与产品线收入匹配热点。&quot], &quottitle&quot: &quot产品线收入区域分布（万元）&quot, &quotsubtitle&quot: &quot2025年区域×产品线收入热力图&quot, &quotcard_size&quot: &quot1x1&quot, &quotchart_type&quot: &quotresponse_heatmap&quot, &quotfield_bindings&quot: {&quotx_field&quot: &quotarea&quot, &quoty_field&quot: &quotproduct_line&quot, &quotvalue_field&quot: &quottotal_income_in_wan&quot}, &quotwrapped_in_card&quot: true}, &quotcomponent_id&quot: &quotchart-0011-c660fb&quot, &quoterror_message&quot: &quot&quot, &quotused_fallback&quot: false, &quotcomponent_code&quot: &quotchart_0011_c660fb_graph = create_chart_from_strategy(\n    chart_type='response_heatmap',\n    data=[{'area': '上海', 'product_line': '估值', 'total_income_in_wan': 9.3735},\n {'area': '内江', 'product_line': '资金', 'total_income_in_wan': 8.07},\n {'area': '合肥', 'product_line': '费用', 'total_income_in_wan': 10.885},\n {'area': '成都', 'product_line': '财税', 'total_income_in_wan': 8.896},\n {'area': '深圳', 'product_line': '综合', 'total_income_in_wan': 11.7165}],\n    style_theme=theme,\n    x_field='area',\n    y_field='product_line',\n    value_field='total_income_in_wan',\n)\nchart_0011_c660fb = create_chart_card(\n    title='产品线收入区域分布（万元）',\n    subtitle='2025年区域×产品线收入热力图',\n    chart_component=chart_0011_c660fb_graph,\n    icon='fa-table-cells-large',\n    notes=['数据单位：万元；用于识别区域与产品线收入匹配热点。'],\n    style_theme=theme,\n    card_size='1x1',\n    card_id='chart-0011-c660fb',\n)&quot, &quotgeneration_status&quot: &quotsuccess&quot}], &quottables&quot: [{&quotreasoning&quot: &quot表格字段严格基于task_sql_executed_data摘要中的sample_rows和columns构建，确保与SQL结果一致并支持明细查询需求。&quot, &quotelapsed_ms&quot: 8679, &quoterror_type&quot: &quot&quot, &quottable_dict&quot: {&quotdata&quot: [{&quotproduct_line&quot: &quot综合&quot, &quottotal_income_in_wan&quot: &quot11.7165&quot}, {&quotproduct_line&quot: &quot费用&quot, &quottotal_income_in_wan&quot: &quot10.885&quot}, {&quotproduct_line&quot: &quot估值&quot, &quottotal_income_in_wan&quot: &quot9.3735&quot}, {&quotproduct_line&quot: &quot财税&quot, &quottotal_income_in_wan&quot: &quot8.896&quot}, {&quotproduct_line&quot: &quot资金&quot, &quottotal_income_in_wan&quot: &quot8.07&quot}], &quotnotes&quot: [&quot数据来源：ods_jfcxexcel_shouru_dlt_m；单位：万元&quot], &quottitle&quot: &quot产品线收入Top-N排名明细表&quot, &quotcolumns&quot: [{&quotkey&quot: &quotproduct_line&quot, &quottitle&quot: &quot产品线名称&quot}, {&quotkey&quot: &quottotal_income_in_wan&quot, &quottitle&quot: &quot收入（万元）&quot}], &quotsubtitle&quot: &quot2025年收入排名前10的产品线明细数据&quot, &quotcard_size&quot: &quot1x1&quot, &quotpage_size&quot: 10, &quottable_type&quot: &quotresponse_table&quot, &quotwrapped_in_card&quot: true}, &quotcomponent_id&quot: &quottable-0012-c24d2a&quot, &quoterror_message&quot: &quot&quot, &quotused_fallback&quot: false, &quotcomponent_code&quot: &quottable_0012_c24d2a_table = create_table_from_strategy(\n    data=[{'product_line': '综合', 'total_income_in_wan': '11.7165'},\n {'product_line': '费用', 'total_income_in_wan': '10.885'},\n {'product_line': '估值', 'total_income_in_wan': '9.3735'},\n {'product_line': '财税', 'total_income_in_wan': '8.896'},\n {'product_line': '资金', 'total_income_in_wan': '8.07'}],\n    columns=[{'key': 'product_line', 'title': '产品线名称'}, {'key': 'total_income_in_wan', 'title': '收入（万元）'}],\n    style_theme=theme,\n    table_id='table-0012-c24d2a',\n    page_size=10,\n)\ntable_0012_c24d2a = create_chart_card(\n    title='产品线收入Top-N排名明细表',\n    subtitle='2025年收入排名前10的产品线明细数据',\n    chart_component=table_0012_c24d2a_table,\n    icon='fa-table-cells-large',\n    notes=['数据来源：ods_jfcxexcel_shouru_dlt_m；单位：万元'],\n    style_theme=theme,\n    card_size='1x1',\n    card_id='table-0012-c24d2a',\n)&quot, &quotgeneration_status&quot: &quotsuccess&quot}], &quotkpi_cards&quot: [{&quotreasoning&quot: &quot使用 task_sql_executed_data 中 sample_rows 提供的精确值 48.941，无趋势数据故 trend_text 与 trend_direction 留空&quot, &quotelapsed_ms&quot: 1120, &quoterror_type&quot: &quot&quot, &quotcomponent_id&quot: &quotkpi-0000-d4f33c&quot, &quoterror_message&quot: &quot&quot, &quotused_fallback&quot: false, &quotcomponent_code&quot: &quotkpi_0000_d4f33c = create_kpi_card(\n    icon='fa-dollar-sign',\n    title='2025年总收入（万元）',\n    value='48.941',\n    style_theme=theme.get('kpi_styles'),\n)&quot, &quotgeneration_status&quot: &quotsuccess&quot}, {&quotreasoning&quot: &quot从 sample_rows 提取 COUNT(DISTINCT product_line) 的值 '5' 作为 value_literal，无趋势数据故 trend_text 和 trend_direction 置空，使用 fa-layer-group 表示分类广度&quot, &quotelapsed_ms&quot: 1105, &quoterror_type&quot: &quot&quot, &quotcomponent_id&quot: &quotkpi-0001-658277&quot, &quoterror_message&quot: &quot&quot, &quotused_fallback&quot: false, &quotcomponent_code&quot: &quotkpi_0001_658277 = create_kpi_card(\n    icon='fa-layer-group',\n    title='产品线数量',\n    value='5',\n    style_theme=theme.get('kpi_styles'),\n)&quot, &quotgeneration_status&quot: &quotsuccess&quot}, {&quotreasoning&quot: &quot从 sample_rows 提取唯一数值字段作为 value_literal，无趋势数据故 trend_text 和 trend_direction 置空，选用 create_kpi_card 适配静态数值展示&quot, &quotelapsed_ms&quot: 2508, &quoterror_type&quot: &quot&quot, &quotcomponent_id&quot: &quotkpi-0002-34189c&quot, &quoterror_message&quot: &quot&quot, &quotused_fallback&quot: false, &quotcomponent_code&quot: &quotkpi_0002_34189c = create_kpi_card(\n    icon='fa-dollar-sign',\n    title='平均单产品线收入（万元）',\n    value='9.7882',\n    style_theme=theme.get('kpi_styles'),\n)&quot, &quotgeneration_status&quot: &quotsuccess&quot}, {&quotreasoning&quot: &quot从 sample_rows 提取唯一数值字段，无趋势数据故 trend 相关字段留空&quot, &quotelapsed_ms&quot: 2093, &quoterror_type&quot: &quot&quot, &quotcomponent_id&quot: &quotkpi-0003-76218e&quot, &quoterror_message&quot: &quot&quot, &quotused_fallback&quot: false, &quotcomponent_code&quot: &quotkpi_0003_76218e = create_kpi_card(\n    icon='fa-dollar-sign',\n    title='收入最高产品线（万元）',\n    value='11.7165',\n    style_theme=theme.get('kpi_styles'),\n)&quot, &quotgeneration_status&quot: &quotsuccess&quot}, {&quotreasoning&quot: &quot从 sample_rows 提取唯一数值 8.07 作为 value_literal；无趋势数据故 trend_text 和 trend_direction 置空；使用 create_kpi_card 因数据为单一静态指标且无需自动格式化；图标选用 fa-dollar-sign 表示收入。&quot, &quotelapsed_ms&quot: 3433, &quoterror_type&quot: &quot&quot, &quotcomponent_id&quot: &quotkpi-0004-882a6e&quot, &quoterror_message&quot: &quot&quot, &quotused_fallback&quot: false, &quotcomponent_code&quot: &quotkpi_0004_882a6e = create_kpi_card(\n    icon='fa-dollar-sign',\n    title='收入最低产品线（万元）',\n    value='8.07',\n    style_theme=theme.get('kpi_styles'),\n)&quot, &quotgeneration_status&quot: &quotsuccess&quot}, {&quotreasoning&quot: &quotNo executed KPI data available; fallback spec rendered from task context.&quot, &quotelapsed_ms&quot: 0, &quoterror_type&quot: &quotMissingSqlExecutedData&quot, &quotcomponent_id&quot: &quotkpi-0005-9d50d5&quot, &quoterror_message&quot: &quotNo executed KPI data available for primary generation.&quot, &quotused_fallback&quot: true, &quotcomponent_code&quot: &quotkpi_0005_9d50d5 = create_kpi_card(\n    icon='fa-chart-simple',\n    title='收入中位数（万元）',\n    value='暂无数据',\n    style_theme=theme.get('kpi_styles'),\n)&quot, &quotgeneration_status&quot: &quotfallback&quot}], &quotchart_count&quot: 6, &quotdesign_name&quot: &quotfinancialSharedCenterRevenue2025&quot, &quotlayout_code&quot: &quotimport dash\nfrom assets.dashboard.runtime import create_chart_card, create_chart_from_strategy, create_data_text_card, create_footer, create_header, create_kpi_card, create_kpi_card_auto, create_layout_from_strategy, create_table_from_strategy\nfrom assets.dashboard.themes.dark_business import DARK_BUSINESS_THEME\nfrom assets.dashboard.themes.light_professional import LIGHT_PROFESSIONAL_THEME\n\ndashboard_color_style = '蓝色商务风'\ntheme = LIGHT_PROFESSIONAL_THEME\n\napp = dash.Dash(__name__)\nserver = app.server\n\nheader = create_header(\n    main_title='2025年财务共享中心各产品线收入全景分析',\n    subtitle='基于2025年全年数据，全面展示各产品线收入规模、结构与趋势',\n    metadata_badge='2025年度 · 财务共享中心',\n    icon='fa-chart-line',\n    style_theme=theme.get('layout_styles'),\n)\nfooter = create_footer(\n    items=['数据更新时间：2025-12-31', '数据来源：ods_jfcxexcel_shouru_dlt_m'],\n    icons=['fa-clock', 'fa-database'],\n    style_theme=theme.get('layout_styles'),\n)\n\nkpi_0000_d4f33c = create_kpi_card(\n    icon='fa-dollar-sign',\n    title='2025年总收入（万元）',\n    value='48.941',\n    style_theme=theme.get('kpi_styles'),\n)\n\nkpi_0001_658277 = create_kpi_card(\n    icon='fa-layer-group',\n    title='产品线数量',\n    value='5',\n    style_theme=theme.get('kpi_styles'),\n)\n\nkpi_0002_34189c = create_kpi_card(\n    icon='fa-dollar-sign',\n    title='平均单产品线收入（万元）',\n    value='9.7882',\n    style_theme=theme.get('kpi_styles'),\n)\n\nkpi_0003_76218e = create_kpi_card(\n    icon='fa-dollar-sign',\n    title='收入最高产品线（万元）',\n    value='11.7165',\n    style_theme=theme.get('kpi_styles'),\n)\n\nkpi_0004_882a6e = create_kpi_card(\n    icon='fa-dollar-sign',\n    title='收入最低产品线（万元）',\n    value='8.07',\n    style_theme=theme.get('kpi_styles'),\n)\n\nkpi_0005_9d50d5 = create_kpi_card(\n    icon='fa-chart-simple',\n    title='收入中位数（万元）',\n    value='暂无数据',\n    style_theme=theme.get('kpi_styles'),\n)\n\nchart_0006_9e494a_graph = create_chart_from_strategy(\n    chart_type='response_pie_chart',\n    data=[{'label_field': '综合', 'value_field': 23.94},\n {'label_field': '费用', 'value_field': 22.24},\n {'label_field': '估值', 'value_field': 19.15},\n {'label_field': '财税', 'value_field': 18.18},\n {'label_field': '资金', 'value_field': 16.49}],\n    style_theme=theme,\n    label_field='product_line',\n    value_field='income_ratio_pct',\n)\nchart_0006_9e494a = create_chart_card(\n    title='产品线收入占比',\n    subtitle='2025年各产品线收入贡献分布',\n    chart_component=chart_0006_9e494a_graph,\n    icon='fa-chart-pie',\n    notes=['综合与费用产品线合计占比超46%，为核心收入来源；资金产品线占比最低，属长尾。'],\n    style_theme=theme,\n    card_size='1x1',\n    card_id='chart-0006-9e494a',\n)\n\nchart_0007_517996_graph = create_chart_from_strategy(\n    chart_type='response_line_chart',\n    data=[{'month': '2025-01', 'product_line': '综合', 'monthly_income_in_wan': 4.6125},\n {'month': '2025-01', 'product_line': '费用', 'monthly_income_in_wan': 3.97},\n {'month': '2025-01', 'product_line': '估值', 'monthly_income_in_wan': 3.7175},\n {'month': '2025-01', 'product_line': '资金', 'monthly_income_in_wan': 3.28},\n {'month': '2025-01', 'product_line': '财税', 'monthly_income_in_wan': 3.25},\n {'month': '2025-02', 'product_line': '费用', 'monthly_income_in_wan': 2.625},\n {'month': '2025-02', 'product_line': '综合', 'monthly_income_in_wan': 1.97},\n {'month': '2025-02', 'product_line': '估值', 'monthly_income_in_wan': 1.95}],\n    style_theme=theme,\n    x_field='month',\n    y_field='monthly_income_in_wan',\n    series_field='product_line',\n)\nchart_0007_517996 = create_chart_card(\n    title='产品线收入月度趋势（万元）',\n    subtitle='2025年1-2月（样本数据）',\n    chart_component=chart_0007_517996_graph,\n    icon='fa-chart-line',\n    notes=['按月分产品线展示收入趋势，用于识别季节性波动与拐点'],\n    style_theme=theme,\n    card_size='1x1',\n    card_id='chart-0007-517996',\n)\n\nchart_0008_4f010c_graph = create_chart_from_strategy(\n    chart_type='response_bar_chart',\n    data=[{'product_line': '综合', 'total_income_in_wan': 11.7165},\n {'product_line': '费用', 'total_income_in_wan': 10.885},\n {'product_line': '估值', 'total_income_in_wan': 9.3735},\n {'product_line': '财税', 'total_income_in_wan': 8.896},\n {'product_line': '资金', 'total_income_in_wan': 8.07}],\n    style_theme=theme,\n    x_field='product_line',\n    y_field='total_income_in_wan',\n)\nchart_0008_4f010c = create_chart_card(\n    title='产品线收入Top-N排名（万元）',\n    subtitle='2025年累计收入，聚焦头部产品线',\n    chart_component=chart_0008_4f010c_graph,\n    icon='fa-chart-bar',\n    notes=['Top 5产品线合计占比超50%，资源倾斜空间显著'],\n    style_theme=theme,\n    card_size='1x1',\n    card_id='chart-0008-4f010c',\n)\n\nchart_0009_156a8c_graph = create_chart_from_strategy(\n    chart_type='response_scatter_plot',\n    data=[{'product_line': '综合', 'total_income_in_wan': 11.7165, 'total_qty': 930.0},\n {'product_line': '费用', 'total_income_in_wan': 10.885, 'total_qty': 740.0},\n {'product_line': '估值', 'total_income_in_wan': 9.3735, 'total_qty': 450.0},\n {'product_line': '财税', 'total_income_in_wan': 8.896, 'total_qty': 308.0},\n {'product_line': '资金', 'total_income_in_wan': 8.07, 'total_qty': 381.0}],\n    style_theme=theme,\n    x_field='total_qty',\n    y_field='total_income_in_wan',\n    series_field='product_line',\n)\nchart_0009_156a8c = create_chart_card(\n    title='产品线收入与作业量相关性',\n    subtitle='2025年各产品线收入（万元） vs 作业量',\n    chart_component=chart_0009_156a8c_graph,\n    icon='fa-chart-scatter',\n    notes=['散点位置反映单位作业量产出效率；高收入高作业量需关注资源匹配。'],\n    style_theme=theme,\n    card_size='1x1',\n    card_id='chart-0009-156a8c',\n)\n\nchart_0010_2d866a_graph = create_chart_from_strategy(\n    chart_type='response_column_chart',\n    data=[{'type1': '白名单', 'product_line': '估值', 'total_income_in_wan': 3.26},\n {'type1': '白名单', 'product_line': '综合', 'total_income_in_wan': 2.84},\n {'type1': '白名单', 'product_line': '财税', 'total_income_in_wan': 2.45},\n {'type1': '白名单', 'product_line': '费用', 'total_income_in_wan': 2.01},\n {'type1': '白名单', 'product_line': '资金', 'total_income_in_wan': 1.64},\n {'type1': '非白', 'product_line': '综合', 'total_income_in_wan': 8.8765},\n {'type1': '非白', 'product_line': '费用', 'total_income_in_wan': 8.875},\n {'type1': '非白', 'product_line': '财税', 'total_income_in_wan': 6.446}],\n    style_theme=theme,\n    x_field='product_line',\n    y_field='total_income_in_wan',\n    series_field='type1',\n)\nchart_0010_2d866a = create_chart_card(\n    title='产品线收入按白名单状态分布（万元）',\n    subtitle='2025年数据',\n    chart_component=chart_0010_2d866a_graph,\n    icon='fa-chart-column',\n    notes=['白名单服务聚焦战略高价值产品线；非白名单服务以综合与费用类为主，收入规模更高。'],\n    style_theme=theme,\n    card_size='1x1',\n    card_id='chart-0010-2d866a',\n)\n\nchart_0011_c660fb_graph = create_chart_from_strategy(\n    chart_type='response_heatmap',\n    data=[{'area': '上海', 'product_line': '估值', 'total_income_in_wan': 9.3735},\n {'area': '内江', 'product_line': '资金', 'total_income_in_wan': 8.07},\n {'area': '合肥', 'product_line': '费用', 'total_income_in_wan': 10.885},\n {'area': '成都', 'product_line': '财税', 'total_income_in_wan': 8.896},\n {'area': '深圳', 'product_line': '综合', 'total_income_in_wan': 11.7165}],\n    style_theme=theme,\n    x_field='area',\n    y_field='product_line',\n    value_field='total_income_in_wan',\n)\nchart_0011_c660fb = create_chart_card(\n    title='产品线收入区域分布（万元）',\n    subtitle='2025年区域×产品线收入热力图',\n    chart_component=chart_0011_c660fb_graph,\n    icon='fa-table-cells-large',\n    notes=['数据单位：万元；用于识别区域与产品线收入匹配热点。'],\n    style_theme=theme,\n    card_size='1x1',\n    card_id='chart-0011-c660fb',\n)\n\ntable_0012_c24d2a_table = create_table_from_strategy(\n    data=[{'product_line': '综合', 'total_income_in_wan': '11.7165'},\n {'product_line': '费用', 'total_income_in_wan': '10.885'},\n {'product_line': '估值', 'total_income_in_wan': '9.3735'},\n {'product_line': '财税', 'total_income_in_wan': '8.896'},\n {'product_line': '资金', 'total_income_in_wan': '8.07'}],\n    columns=[{'key': 'product_line', 'title': '产品线名称'}, {'key': 'total_income_in_wan', 'title': '收入（万元）'}],\n    style_theme=theme,\n    table_id='table-0012-c24d2a',\n    page_size=10,\n)\ntable_0012_c24d2a = create_chart_card(\n    title='产品线收入Top-N排名明细表',\n    subtitle='2025年收入排名前10的产品线明细数据',\n    chart_component=table_0012_c24d2a_table,\n    icon='fa-table-cells-large',\n    notes=['数据来源：ods_jfcxexcel_shouru_dlt_m；单位：万元'],\n    style_theme=theme,\n    card_size='1x1',\n    card_id='table-0012-c24d2a',\n)\n\napp.layout = create_layout_from_strategy(\n    layout_type='classic_three_layer',\n    header=header,\n    footer=footer,\n    style_theme=theme,\n    kpi_cards=[kpi_0000_d4f33c, kpi_0001_658277, kpi_0002_34189c, kpi_0003_76218e, kpi_0004_882a6e, kpi_0005_9d50d5],\n    chart_cards=[chart_0006_9e494a, chart_0007_517996, chart_0008_4f010c, chart_0009_156a8c, chart_0010_2d866a, chart_0011_c660fb],\n    data_cards=[table_0012_c24d2a],\n)\n\nif __name__ == '__main__':\n    app.run(debug=True)\n&quot, &quottable_count&quot: 1, &quotlayout_design&quot: &quot经典三层(KPI-图表-表格)&quot, &quotkpi_card_count&quot: 6, &quotdashboard_title&quot: &quot2025年财务共享中心各产品线收入全景分析&quot, &quotdashboard_run_id&quot: &quotf8f590e30945&quot, &quotlayout_reasoning&quot: &quot根据 layout_design 指定的经典三层结构（KPI-图表-表格），将6个KPI卡片置于顶部 zone='kpi'，6个分析图表置于中部 zone='main'，明细表格置于底部 zone='bottom'。所有 component_id 均来自 generated_component_inventory，component_kind 严格使用 kpi/chart/table，zone 与 classic_three_layer 布局规范一致。&quot, &quotlayout_elapsed_ms&quot: 40091, &quotlayout_error_type&quot: &quot&quot, &quotgeneration_attempt&quot: 1, &quotgeneration_context&quot: {&quotrun_id&quot: &quotf8f590e30945&quot, &quotattempt_id&quot: 1}, &quotautofit_color_design&quot: &quot蓝色商务风&quot, &quotlayout_error_message&quot: &quot&quot, &quotlayout_generation_status&quot: &quotsuccess&quot, &quotcomponent_generation_summary&quot: {&quotkpi&quot: {&quoterror_count&quot: 0, &quotresult_count&quot: 6, &quotsuccess_count&quot: 5, &quotfallback_count&quot: 1}, &quotchart&quot: {&quoterror_count&quot: 0, &quotresult_count&quot: 6, &quotsuccess_count&quot: 6, &quotfallback_count&quot: 0}, &quottable&quot: {&quoterror_count&quot: 0, &quotresult_count&quot: 1, &quotsuccess_count&quot: 1, &quotfallback_count&quot: 0}}}</div>

---

##   dashboard title    2025年财务共享中心各产品线收入分析    autofit color design    蓝色 

# {'dashboard_title': '2025年财务共享中心各产品线收入分析', 'autofit_color_design': '蓝色…

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p110 -->

<div>{'dashboard_title': '2025年财务共享中心各产品线收入分析', 'autofit_color_design': '蓝色商务风', 'layout_design': '经典三层(KPI-图表-表格)', 'visualization_tasks': [{'task_name': 'dashboard_title', 'task_description': '看板标题设计', 'task_type': 'response_dashboard_main_title', 'task_data': '2025年财务共享中心各产品线收入分析', 'task_visualization': '看板主标题', 'task_sql': '', 'task_result': '成功创建了看板的主标题。', 'task_reason': '为整个看板提供一个明确的主题，便于用户理解其内容。'}, {'task_name': 'dashboard_sub_title_月度趋势', 'task_description': '子分析标题设计 - 月度趋势', 'task_type': 'response_dashboard_sub_title', 'task_data': '月度趋势|展示各月份的收入变化趋势', 'task_visualization': '图表区域子标题', 'task_sql': '', 'task_result': '为月度趋势分析提供了清晰的子标题。', 'task_reason': &quot帮助用户快速定位到关于'月度趋势'的具体分析部分。&quot}, {'task_name': 'dashboard_sub_title_产品线占比', 'task_description': '子分析标题设计 - 产品线占比', 'task_type': 'response_dashboard_sub_title', 'task_data': '产品线占比|显示每个产品线占总收入的比例', 'task_visualization': '图表区域子标题', 'task_sql': '', 'task_result': '为产品线占比分析设置了具体的子标题。', 'task_reason': &quot方便用户找到并理解有关'产品线占比'的信息。&quot}, {'task_name': 'dashboard_sub_title_地区排名', 'task_description': '子分析标题设计 - 地区排名', 'task_type': 'response_dashboard_sub_title', 'task_data': '地区排名|列出收入最高的前五个地区', 'task_visualization': '图表区域子标题', 'task_sql': '', 'task_result': '针对地区排名分析定义了明确的子标题。', 'task_reason': &quot使得用户能够轻易识别出与'地区排名'相关的数据分析。&quot}, {'task_name': 'dashboard_sub_title_同比增长率', 'task_description': '子分析标题设计 - 同比增长率', 'task_type': 'response_dashboard_sub_title', 'task_data': '同比增长率|比较2025年与2024年同一产品线的收入增长情况', 'task_visualization': '图表区域子标题', 'task_sql': '', 'task_result': '为同比增长率分析配置了合适的子标题。', 'task_reason': &quot有助于用户直接关注于'同比增长率'的变化。&quot}, {'task_name': 'dashboard_sub_title_计费模式交叉分析', 'task_description': '子分析标题设计 - 计费模式交叉分析', 'task_type': 'response_dashboard_sub_title', 'task_data': '计费模式交叉分析|通过热力图显示不同计费模式下各产品线的收入分布', 'task_visualization': '图表区域子标题', 'task_sql': '', 'task_result': '为计费模式交叉分析指定了相应的子标题。', 'task_reason': &quot让使用者能够直观地了解'计费模式交叉分析'的内容。&quot}, {'task_name': 'dashboard_section_title_1', 'task_description': '区域标题设计 - KPI概览', 'task_type': 'response_dashboard_section_title', 'task_data': 'KPI概览|展示关键绩效指标', 'task_visualization': '看板区域标题', 'task_sql': '', 'task_result': '为KPI概览区域设定了合适的标题。', 'task_reason': '突出该区域专注于展示关键绩效指标的功能。'}, {'task_name': 'dashboard_color_style', 'task_description': '配色方案设计', 'task_type': 'response_dashboard_color_style', 'task_data': '蓝色商务风|蓝色为主色调，辅以灰色和白色作为背景色', 'task_visualization': '看板配色方案', 'task_sql': '', 'task_result': &quot选择了符合主题的'蓝色商务风'配色方案。&quot, 'task_reason': '确保看板整体风格统一且专业。'}, {'task_name': 'dashboard_layout', 'task_description': '布局方案设计', 'task_type': 'response_dashboard_layout', 'task_data': '经典三层(KPI-图表-表格)|上层为KPI概览，中层放置各类图表，底层则是数据表格', 'task_visualization': '看板布局结构', 'task_sql': '', 'task_result': '采用经典的三层布局来组织看板内容。', 'task_reason': '保证信息层次分明，易于用户理解和使用。'},</div>
<div><br></div>
<div><br></div>
<div><br></div>
<div>[VisualizationTask(task_name='dashboard_title', task_description='看板标题设计', task_type='response_dashboard_main_title', task_data='2025年财务共享中心各产品线收入分析', task_visualization='看板主标题', task_sql='', task_result='成功创建了看板的主标题。', task_reason='为整个看板提供一个明确的主题，便于用户理解其内容。'), VisualizationTask(task_name='dashboard_sub_title_月度趋势', task_description='子分析标题设计 - 月度趋势', task_type='response_dashboard_sub_title', task_data='月度趋势|展示各月份的收入变化趋势', task_visualization='图表区域子标题', task_sql='', task_result='为月度趋势分析提供了清晰的子标题。', task_reason=&quot帮助用户快速定位到关于'月度趋势'的具体分析部分。&quot), VisualizationTask(task_name='dashboard_sub_title_产品线占比', task_description='子分析标题设计 - 产品线占比', task_type='response_dashboard_sub_title', task_data='产品线占比|显示每个产品线占总收入的比例', task_visualization='图表区域子标题', task_sql='', task_result='为产品线占比分析设置了具体的子标题。', task_reason=&quot方便用户找到并理解有关'产品线占比'的信息。&quot), VisualizationTask(task_name='dashboard_sub_title_地区排名', task_description='子分析标题设计 - 地区排名', task_type='response_dashboard_sub_title', task_data='地区排名|列出收入最高的前五个地区', task_visualization='图表区域子标题', task_sql='', task_result='针对地区排名分析定义了明确的子标题。', task_reason=&quot使得用户能够轻易识别出与'地区排名'相关的数据分析。&quot), VisualizationTask(task_name='dashboard_sub_title_同比增长率', task_description='子分析标题设计 - 同比增长率', task_type='response_dashboard_sub_title', task_data='同比增长率|比较2025年与2024年同一产品线的收入增长情况', task_visualization='图表区域子标题', task_sql='', task_result='为同比增长率分析配置了合适的子标题。', task_reason=&quot有助于用户直接关注于'同比增长率'的变化。&quot), VisualizationTask(task_name='dashboard_sub_title_计费模式交叉分析', task_description='子分析标题设计 - 计费模式交叉分析', task_type='response_dashboard_sub_title', task_data='计费模式交叉分析|通过热力图显示不同计费模式下各产品线的收入分布', task_visualization='图表区域子标题', task_sql='', task_result='为计费模式交叉分析指定了相应的子标题。', task_reason=&quot让使用者能够直观地了解'计费模式交叉分析'的内容。&quot), VisualizationTask(task_name='dashboard_section_title_1', task_description='区域标题设计 - KPI概览', task_type='response_dashboard_section_title', task_data='KPI概览|展示关键绩效指标', task_visualization='看板区域标题', task_sql='', task_result='为KPI概览区域设定了合适的标题。', task_reason='突出该区域专注于展示关键绩效指标的功能。'), VisualizationTask(task_name='dashboard_color_style', task_description='配色方案设计', task_type='response_dashboard_color_style', task_data='蓝色商务风|蓝色为主色调，辅以灰色和白色作为背景色', task_visualization='看板配色方案', task_sql='', task_result=&quot选择了符合主题的'蓝色商务风'配色方案。&quot, task_reason='确保看板整体风格统一且专业。'), VisualizationTask(task_name='dashboard_layout', task_description='布局方案设计', task_type='response_dashboard_layout', task_data='经典三层(KPI-图表-表格)|上层为KPI概览，中层放置各类图表，底层则是数据表格', task_visualization='看板布局结构', task_sql='', task_result='采用经典的三层布局来组织看板内容。', task_reason='保证信息层次分明，易于用户理解和使用。'), VisualizationTask(task_name='kpi_total_income', task_description='KPI卡片任务 - 总收入(万元)', task_type='response_kpi_card', task_data='总收入(万元)', task_visualization='KPI卡片', task_sql=&quotSELECT SUM(avenue) / 10000 AS total_income_in_wan FROM ods_jfcxexcel_shouru_dlt_m WHERE date_rq &gt= '2025-01-01' AND date_rq &lt= '2025-12-31'&quot, task_result='生成了反映年度总收入的KPI卡片。', task_reason='直接展示全年总收入，是评估财务状况的关键指标之一。'), VisualizationTask(task_name='kpi_average_monthly_income', task_description='KPI卡片任务 - 平均每月收入(万元)', task_type='response_kpi_card', task_data='平均每月收入(万元)', task_visualization='KPI卡片', task_sql=&quotSELECT SUM(avenue) / 10000 / 12 AS average_monthly_income_in_wan FROM ods_jfcxexcel_shouru_dlt_m WHERE date_rq &gt= '2025-01-01' AND date_rq &lt= '2025-12-31'&quot, task_result='创建了一个用于追踪平均每月收入的KPI卡片。', task_reason='帮助管理者了解每月收入水平，对于预算规划具有重要意义。'), VisualizationTask(task_name='kpi_highest_income_product_line', task_description='KPI卡片任务 - 最高收入产品线', task_type='response_kpi_card', task_data='最高收入产品线', task_visualization='KPI卡片', task_sql=&quotSELECT product_line, SUM(avenue) / 10000 AS total_income_in_wan FROM ods_jfcxexcel_shouru_dlt_m WHERE date_rq &gt= '2025-01-01' AND date_rq &lt= '2025-12-31' GROUP BY product_line ORDER BY total_income_in_wan DESC LIMIT 1&quot, task_result='制作了标识最高收入产品线的KPI卡片。', task_reason='揭示了对总体收入贡献最大的产品线。'), VisualizationTask(task_name='kpi_lowest_income_product_line', task_description='KPI卡片任务 - 最低收入产品线', task_type='response_kpi_card', task_data='最低收入产品线', task_visualization='KPI卡片', task_sql=&quotSELECT product_line, SUM(avenue) / 10000 AS total_income_in_wan FROM ods_jfcxexcel_shouru_dlt_m WHERE date_rq &gt= '2025-01-01' AND date_rq &lt= '2025-12-31' GROUP BY product_line ORDER BY total_income_in_wan ASC LIMIT 1&quot, task_result='完成了显示最低收入产品线的KPI卡片。', task_reason='辅助识别需要改进或可能被优化的产品线。'), VisualizationTask(task_name='line_chart_monthly_trend', task_description='图表任务 - 月度趋势', task_type='response_line_chart', task_data='月度趋势|展示各月份的收入变化趋势', task_visualization='折线图', task_sql=&quotSELECT DATE_FORMAT(date_rq, '%Y-%m') AS month, SUM(avenue) / 10000 AS total_income_in_wan FROM ods_jfcxexcel_shouru_dlt_m WHERE date_rq &gt= '2025-01-01' AND date_rq &lt= '2025-12-31' GROUP BY month ORDER BY month&quot, task_result='构建了表示各月份收入变化趋势的折线图。', task_reason='通过可视化方式展现了收入随时间波动的情况，便于发现季节性特征或其他周期性规律。'), VisualizationTask(task_name='pie_chart_product_line_percentage', task_description='图表任务 - 产品线占比', task_type='response_pie_chart', task_data='产品线占比|显示每个产品线占总收入的比例', task_visualization='饼图', task_sql=&quotSELECT product_line, SUM(avenue) * 100.0 / (SELECT SUM(avenue) FROM ods_jfcxexcel_shouru_dlt_m WHERE date_rq &gt= '2025-01-01' AND date_rq &lt= '2025-12-31') AS percentage FROM ods_jfcxexcel_shouru_dlt_m WHERE date_rq &gt= '2025-01-01' AND date_rq &lt= '2025-12-31' GROUP BY product_line&quot, task_result='制成了反映各产品线收入占比的饼图。', task_reason='形象地展示了各个产品线在总收入中的相对重要性。'), VisualizationTask(task_name='column_chart_top_areas', task_description='图表任务 - 地区排名', task_type='response_column_chart', task_data='地区排名|列出收入最高的前五个地区', task_visualization='柱状图', task_sql=&quotSELECT area, SUM(avenue) / 10000 AS total_income_in_wan FROM ods_jfcxexcel_shouru_dlt_m WHERE date_rq &gt= '2025-01-01' AND date_rq &lt= '2025-12-31' GROUP BY area ORDER BY total_income_in_wan DESC LIMIT 5&quot, task_result='绘制了代表收入最高地区的柱状图。', task_reason='突出了收入表现最好的几个地理区域，有助于进行地域性战略规划。'), VisualizationTask(task_name='bar_chart_year_over_year_growth', task_description='图表任务 - 同比增长率', task_type='response_bar_chart', task_data='同比增长率|比较2025年与2024年同一产品线的收入增长情况', task_visualization='条形图', task_sql=&quotSELECT product_line, (SUM(CASE WHEN YEAR(date_rq) = 2025 THEN avenue ELSE 0 END) - SUM(CASE WHEN YEAR(date_rq) = 2024 THEN avenue ELSE 0 END)) / NULLIF(SUM(CASE WHEN YEAR(date_rq) = 2024 THEN avenue ELSE 0 END), 0) * 100 AS growth_rate FROM ods_jfcxexcel_shouru_dlt_m WHERE date_rq &gt= '2024-01-01' AND date_rq &lt= '2025-12-31' GROUP BY product_line&quot, task_result='生成了比较两年间各产品线收入增长情况的条形图。', task_reason='清晰地表达了从一年到另一年的收入增长或下降幅度，有利于业绩评价。'), VisualizationTask(task_name='heatmap_billing_mode_cross_analysis', task_description='图表任务 - 计费模式交叉分析', task_type='response_heatmap', task_data='计费模式交叉分析|通过热力图显示不同计费模式下各产品线的收入分布', task_visualization='热力图', task_sql=&quotSELECT pay, product_line, SUM(avenue) / 10000 AS total_income_in_wan FROM ods_jfcxexcel_shouru_dlt_m WHERE date_rq &gt= '2025-01-01' AND date_rq &lt= '2025-12-31' GROUP BY pay, product_line&quot, task_result='创建了基于不同计费模式的产品线收入分布热力图。', task_reason='利用颜色深浅直观地呈现了不同计费模式下的收入差异，便于深入分析。')]</div>

---

##  非营利组织2025年度财务状况总结及计划 n n2025年3月21日 非营利组织发布了2025年度的财务状况总结 总收入为500 

# '非营利组织2025年度财务状况总结及计划\n\n2025年3月21日，非营利组织发布了2025年度的财务状况总结。总收入为500…

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p64 -->

<div>'非营利组织2025年度财务状况总结及计划\n\n2025年3月21日，非营利组织发布了2025年度的财务状况总结。总收入为500万元，主要来源包括：捐赠收入为250万元，占总收入的50%；政府补助为150万元，占总收入的30%。'</div>

---

## 帮我针对平安财服收入进行可视化看板生成

# 帮我针对平安财服收入进行可视化看板生成

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p136 -->

<div>帮我针对平安财服收入进行可视化看板生成</div>
<div><font face=".PingFangUITextSC-Regular"><br></font></div>
<div><font face=".PingFangUITextSC-Regular">您需要基于平安财服收入数据构建可视化看板，意图明确。当前数据执行链失败，未返回有效结果（非数据源未绑定问题）。请补充具体指标口径（如</font>“月度保费收入”）、时间范围（如“2025年1-12月”）或维度条件（如“按地区/渠道分组”），并确认数据库权限及连通性。该库为MySQL，建议检查表名与字段是否准确。</div>
<div><br></div>
<div>{&quotthread_id&quot: &quotaskdata-1775613526484-1qcs3xi&quot, &quotagent&quot: &quotassistant&quot, &quotartifacts&quot: {&quotaksdata&quot: {&quotdatabases&quot: [{&quotname&quot: &quot平安金服财服数据库&quot, &quoturl&quot: &quotdatabase:766366e8-041a-40fe-896d-c028dd030704&quot, &quotdatasource_id&quot: 1, &quotresource_uuid&quot: &quot766366e8-041a-40fe-896d-c028dd030704&quot, &quotdb_type&quot: &quotmysql&quot, &quotis_resolved&quot: true}], &quottables&quot: []}}}</div>
<div><br></div>
<div>{&quotthread_id&quot: &quotaskdata-1775613526484-1qcs3xi&quot, &quotagent&quot: &quotassistant&quot, &quotrole&quot: &quotassistant&quot, &quotphase&quot: &quotanswer&quot, &quotcontent&quot: &quot您需要基于平安财服收入数据构建可视化看板，意图明确。当前数据执行链失败，未返回有效结果（非数据源未绑定问题）。请补充具体指标口径（如“月度保费收入”）、时间范围（如“2025年1-12月”）或维度条件（如“按地区/渠道分组”），并确认数据库权限及连通性。该库为MySQL，建议检查表名与字段是否准确。&quot, &quotfinish_reason&quot: &quotstop&quot}</div>

---

## 第一张看板 财服全景看板  数字讲解员带你俯瞰财服全貌

# 第一张看板：财服全景看板——数字讲解员带你俯瞰财服全貌

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p75 -->

<div><b>第一张看板：财服全景看板——数字讲解员带你俯瞰财服全貌</b><br></div>
<div><b>1. 核心定位</b><br></div>
<div>从“<b>业务、客户、地理、队伍、AI</b>”五大维度，立体呈现财服“规模-质量-效率-价值”的全景画像，是展厅**“第一印象看板”**（对应文档4“升级一：财服全景图”）。</div>
<div><b>2. 设备与布局</b><br></div>
<ul>
<li><b>主设备</b>：<b>LED一体屏（3926×1100mm，P1.8小间距）</b>（文档4“主屏：37万”），占比看板70%区域；</li>
<li><b>辅助设备</b>：<b>iPad Pro（12.9英寸）</b>（离屏控制，文档4“支持iPad离屏控制切换”）；</li>
<li><b>布局逻辑</b>：左（业务+客户）→中（中国地图）→右（队伍+AI），符合“从左到右、从宏观到微观”的认知习惯。</li>
</ul>
<div><b>3. 详细内容设计</b><br></div>
<div><b>（1）左侧：业务指标（文档1“业务规模”“建设成效”）</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">维度</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">指标名称</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">规模</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">资金吞吐量</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">动态数字</font>+<b>月度折线图</b>（X轴：月份，Y轴：笔数）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“资金收付：12亿+笔/年”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击折线图节点</font>→弹出“当月资金支付场景分布”（如“上海占35%、深圳占25%”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">账套资产量</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">仪表盘</font></b>（红色指针指向“2000+”，刻度0-3000）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“总账报表：2000+账套”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover仪表盘→显示“账套覆盖集团100%成员公司”</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">质量</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">一次通过率</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">百分比圆环图</font></b>（蓝色填充85%，灰色15%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“费用黑灯工厂：一次通过率85%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击圆环</font>→弹出“未通过原因TOP3”（如“发票抬头错误占40%、金额不符占30%”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">退回率</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">对比柱状图</font></b>（X轴：月份，Y轴：%，对比“2024年vs2025年”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“数字化运营平台：月均退回率≤5%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover柱子→显示“当月退回率下降原因”（如“AI审核规则优化”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">效率</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月结时效</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数字时钟</font></b>（动态从“5天”→“2天”，模拟压缩过程）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“总账智能报表：月结从5天→2天”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击时钟</font>→弹出“月结流程优化节点”（如“REP规则引擎优化减少3天”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">关账准时率</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">绿</font></b><b>/红指示灯</b>（绿灯=≥95%，红灯=＜95%，当前亮绿灯）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“总账货币资金RTR黑灯：关账准时率≥95%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击指示灯</font>→弹出“准时率达标秘诀”（如“银企对账自动化减少人工延误”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">风控</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">风险拦截数</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">滚动计数器</font></b>（实时更新，如“140000次/年”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“智能风控：年拦截风险14万次”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover计数器→显示“拦截风险类型分布”（如“虚假发票占60%、重复支付占20%”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">差错件</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">下降箭头</font></b><b>+数字</b>（从“1000件/年”→“600件/年”，红色箭头标注“下降40%”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“智能巡检：差错件同比下降40%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击箭头</font>→弹出“差错件典型案例”（如“2024年Q1因人工录入错误导致10件差错”）</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>（2）左侧：客户指标（文档1“建设成效”“业务规模”）</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">维度</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">指标名称</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">规模</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">产品分布</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">饼图</font></b>（费用38万员工、税务6000报税笔数/年、总账10亿凭证、资金12亿笔、估值7万亿交易数据、综合档案管理）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“业务规模：六大产品线”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击饼图块</font>→弹出“该产品线的核心流程”（如“费用→智能填单→AI审核→制证”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">业务规模</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">堆叠柱状图</font></b>（X轴：年份，Y轴：处理量，区分“费用、税务、总账”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“业务规模：300万+报销单、30万+发票”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover柱子→显示“当年业务增长的驱动因素”（如“2025年费用增长因员工数增加”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">价值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">满意度</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">星级评分</font></b>（5颗星，当前4.8分，金色填充）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“客户服务：满意度4.8/5分”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击星星</font>→弹出“满意度调研问题TOP3”（如“报销时效快占90%、AI审核准占85%”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">降本</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">金币图标</font></b><b>+动态数字</b>（从“0”→“7000万/年”，金色粒子动画）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“建设成效：运营成本优化7000万”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击金币</font>→弹出“降本 breakdown”（如“AI替人占40%、流程优化占30%、规模效应占30%”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">商务</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">回款率</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">进度条</font></b>（绿色填充98%，红色标注“目标95%”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“数字化运营平台：回款率98%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover进度条→显示“回款率高的原因”（如“RPA自动催收减少逾期”）</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>（3）中间：中国地图（文档1“五地布局”）</b><br></div>
<ul>
<li><b>展现形式</b>：<b>热力地图</b>（省份底色：浅灰→深灰，颜色越深业务量越大；城市标注：上海、深圳、成都、合肥、内江，气泡大小=人员数量）；</li>
<li><b>数据标注</b>： </li>
<ul>
<li>上海：2004年成立/200+人→气泡大小“中”，热力值“深灰”（资金支付占35%）；</li>
<li>深圳：2008年成立/200+人→气泡大小“中”，热力值“深灰”（总账报表占40%）；</li>
<li>成都：2008年成立/300+人→气泡大小“大”，热力值“最深灰”（费用审核效率最高）；</li>
<li>合肥：2011年成立/200+人→气泡大小“中”，热力值“中灰”（税务管理占20%）；</li>
<li>内江：2008年成立/150+人→气泡大小“小”，热力值“浅灰”（档案管理占10%）；</li>
</ul>
<li><b>互动逻辑</b>：hover城市→弹出“该地区核心业务+典型案例”（如“成都：费用审核效率最高，2025年人均处理量1200单/月”）。</li>
</ul>
<div><b>（4）右侧：队伍指标（文档1“业务规模”“队伍能力”）</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">维度</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">指标名称</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">规模</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">人员数量</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">动态数字</font></b>（从“0”→“1050+”，白色字体，黑色背景）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“五地布局：200+200+300+200+150=1050+”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击数字</font>→弹出“人员结构”（如“财务运营60%、数字化技术20%、客户服务10%、管理10%”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">人员分布</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">横向柱状图</font></b>（X轴：地区，Y轴：人数，上海200、深圳200、成都300、合肥200、内江150）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“五地布局”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover柱子→显示“该地区的主要岗位”（如“成都：费用审核岗占60%”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">上线人数</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">百分比圆环图</font></b>（绿色填充100%，标注“全量上线数字化系统”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“数字化运营平台：100%人员上线”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击圆环</font>→弹出“上线系统的核心功能”（如“财智云+AI+规则引擎”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">能力</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">双证数（</font>CPA/中高级）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">证书图标</font></b><b>+数字</b>（300+本证书，金色图标，动态排列）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“业务规模：300+CPA及中、高级以上职称”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击图标</font>→弹出“双证人员分布”（如“总账岗占40%、税务岗占30%”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">数字化专才</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">技能雷达图</font></b>（维度：RPA、AI、规则引擎、BI、数据挖掘；得分：8/10）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>2“科技开发人员超2.1万”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover雷达图→显示“专才培训计划”（如“2026年计划培养100名AI训练师”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">稳定性</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">司龄</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">折线图</font></b>（X轴：司龄段，Y轴：占比；1-3年40%、3-5年35%、5年+25%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“发展历程：20年积累”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击折线</font>→弹出“司龄长的优势”（如“5年+员工熟悉100+审核规则”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">流失率</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">绿色下降箭头</font></b>（从“8%”→“5%”，标注“年流失率≤5%”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“建设成效：年流失率≤5%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击箭头</font>→弹出“留人秘诀”（如“数字化培训+晋升通道+弹性工作”）</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>（5）右侧：AI指标（文档1“数字员工集群”“AI赋能”）</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">维度</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">指标名称</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数字空间站</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">数字员工（</font>RPA）数量</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">机器人图标</font></b><b>+数字</b>（70+个机器人，蓝色图标，动态排列）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“数字员工集群：70+个RPA”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击图标</font>→弹出“RPA场景分布”（如“资金30%、费用25%、税务20%”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">小工具数量</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">工具图标墙</font></b>（OCR、NLP、规则引擎、BI、数据埋点，共20+个，灰色图标）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“技术应用：OCR、NLP等”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击工具</font>→弹出“工具 demo”（如“OCR识别发票：上传图片→提取金额/日期”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">数字场景分布</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">词云图</font></b>（“费用审核”“资金支付”“税务申报”“总账制证”“估值核算”，字体越大使用越广）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“数字员工集群：覆盖6大场景”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击词云</font>→弹出“场景流程”（如“费用审核→智能填单→AI审核→制证”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">任务成功率</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">百分比仪表盘</font></b>（蓝色填充98%，标注“≥98%”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“RPA作业效益衡量：任务成功率≥98%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover仪表盘→显示“失败任务原因”（如“系统接口异常占1%、数据错误占1%”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">等效人力</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">人头图标</font></b><b>+数字</b>（2000+小时/年，灰色人头，动态累加）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“降本提效：等效替代2000+人工小时”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击人头</font>→弹出“等效人力的价值”（如“相当于少用10名全职员工”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b>AI Agent</b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">智能体数量</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">大脑图标</font></b><b>+数字</b>（50+个智能体，紫色图标，动态排列）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>3“费用全域智控：50+智能体”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击图标</font>→弹出“智能体分类”（如“财务会计20、税务支持15、管理会计10”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">应用分类</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">分类标签云</font></b>（“财务会计”“税务支持”“管理会计”“金融支持”，按使用频率排序）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“建设内容：AI应用场景”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击标签</font>→弹出“智能体案例”（如“财务会计：费用AI审核，准确率95%”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><br></td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">等效人力</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">人头图标</font></b><b>+数字</b>（800+小时/年，紫色人头，动态累加）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“人机协同：等效替代800+人工小时”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击人头</font>→弹出“智能体与RPA的区别”（如“智能体可自主学习规则，RPA是固定流程”）</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>4. 数字讲解员对外口径（文档1“建设成效”）</b><br></div>
<div>各位来宾，欢迎来到财服全景看板！左边我们看到：<b>业务规模</b>上，年资金吞吐量12亿+笔、管理2000+账套资产；<b>质量</b>上，费用审核一次通过率85%、月均退回率≤5%；<b>效率</b>上，总账月结从5天压缩到2天，关账准时率≥95%；<b>风控</b>上，年拦截风险14万次，差错件同比下降40%。再看<b>客户价值</b>：我们覆盖38万员工的费用报销、6000笔/年的税务申报，年运营成本优化7000万，客户满意度4.8分。  中间的地图展示了我们的<b>五地布局</b>：上海、深圳、成都、合肥、内江协同运作，比如上海侧重资金支付（占35%）、深圳聚焦总账报表（占40%）。右边的<b>队伍</b>有1050+人，300+持双证，年流失率≤5%，还有<b>AI赋能</b>：70+RPA机器人、50+智能体，等效替代2000+人工小时，真正实现“数智替人、智能提效”！</div>
<div><br></div>
<div><b>第二张看板：业务流程看板——数字讲解员带你走完财服全流程</b><br></div>
<div><b>1. 核心定位</b><br></div>
<div>按“<b>业务条线+地区</b>”双维度，呈现<b>费用、财税、资金、估值</b>四大核心业务的“端到端流程”，突出“数智化如何解决‘作业重复低效’”（文档1“初期挑战：作业重复低效”）。</div>
<div><b>2. 设备与布局</b><br></div>
<ul>
<li><b>主设备</b>：<b>LED一体屏（3926×1100mm，P1.8小间距）</b>；</li>
<li><b>辅助设备</b>：<b>触屏笔（用于点击流程节点）</b>；</li>
<li><b>布局逻辑</b>：顶部（业务条线+地区筛选）→主体（分业务流程图）→底部（地区效率排名）。</li>
</ul>
<div><b>3. 详细内容设计</b><br></div>
<div><b>（1）顶部：筛选栏（文档3“分条线投产矩阵”）</b><br></div>
<ul>
<li><b>业务条线标签</b>：费用、财税、资金、估值（点击切换对应流程，默认选中“费用”）；</li>
<li><b>地区标签</b>：上海、深圳、成都、合肥、内江（hover显示该地区流程数据，默认选中“全国”）。</li>
</ul>
<div><b>（2）主体：分业务流程图（文档1“建设内容：应用场景”）</b><br></div>
<div><b>① 费用业务（文档1“费用黑灯工厂”）</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">流程环节</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">日月年流入量</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">日月年完成量</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">智能填单</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>25万单</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>25万单（100%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">漏斗图（流入</font>→完成无损耗）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“费用黑灯工厂：全年300万单”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击漏斗</font>→弹出“智能填单的技术”（如“静默抓取出差数据，自动生成报销单”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">业务审批</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>25万单</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>24万单（96%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">进度条（完成率</font>96%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“优化路径：业务审批节点”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover进度条→显示“审批时效”（如“平均2小时完成业务审批”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">财务审批</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>24万单</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>23万单（95.8%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">折线图（月度审批量趋势）</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“建设成效：财务审批效率提升”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击折线图</font>→弹出“财务审批的规则”（如“AI预审→人工复核高风险单据”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">采集录入</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>23万单</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>22.77万单（99%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">数字</font>+百分比（99%自动采集）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“费用黑灯工厂：99%发票自动采集”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击数字</font>→弹出“OCR识别的准确率”（如“99%识别发票代码/号码/金额”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档复核</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>22.77万单</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>22.545万单（99%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">对比图（</font>AI复核vs人工复核量）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“费用黑灯工厂：AI复核占比99%”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover对比图→显示“AI复核的优势”（如“AI复核速度是人工的10倍”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">规则引擎审核</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>22.545万单</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>11.27万单（50%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">饼图（自动审核</font>50%、人工50%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“建设成效：50%单据自动审核”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击饼图</font>→弹出“规则引擎的逻辑”（如“1万+条规则，覆盖7类费用”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">会计审核</font>&amp制证</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>11.27万单</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>11.27万单（100%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">绿勾图标（全自动化）</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“费用黑灯工厂：会计审核&amp制证全自动化”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击绿勾</font>→弹出“制证的准确性”（如“100%匹配会计科目，无差错”）</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>② 财税业务（文档3“税金端到端自动化”）</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">流程环节</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">日月年流入量</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">日月年完成量</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">税金测算</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>5000笔</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>5000笔（100%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">数字时钟（实时完成量）</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>3“税金端到端：测算自动化率100%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击时钟</font>→弹出“测算的规则”（如“增值税=销项税-进项税，AI自动计算”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">申报数据准备</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>5000笔</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>4950笔（99%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">百分比圆环（自动准备率</font>99%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>3“增值税及附加：数据准备自动化率99%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover圆环→显示“人工干预的原因”（如“特殊业务需手动调整税率”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">系统申报</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>4950笔</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>4900笔（98.9%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">折线图（申报成功率趋势）</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>3“RPA申报：成功率98.9%”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击折线图</font>→弹出“申报的流程”（如“RPA自动登录税局系统，上传数据并提交”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">归档</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>4900笔</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>4900笔（100%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文件夹图标（全归档）</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>3“税金端到端：归档自动化率100%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击文件夹</font>→弹出“归档的位置”（如“电子档案系统，可按年份/类型查询”）</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>③ 资金业务（文档1“资金云端物联”）</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">流程环节</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">日月年流入量</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">日月年完成量</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">资金提单</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">日均值</font>400万笔</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">日均值</font>396万笔（99%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">动态数字（实时流入</font>/完成）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“资金收付：12亿+笔/年”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击数字</font>→弹出“提单的方式”（如“系统自动提单+人工修正，99%自动”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">审核</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">日均值</font>396万笔</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">日均值</font>392万笔（99%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">进度条（自动审核率</font>99%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“资金云端物联：审核自动化率99%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover进度条→显示“审核的规则”（如“AI校验账户余额+交易真实性”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">支付</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">日均值</font>392万笔</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">日均值</font>388万笔（99%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">柱状图（支付成功率趋势）</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“资金云端物联：支付成功率99%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击柱子</font>→弹出“支付的渠道”（如“网银占80%、第三方支付占20%”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">对账</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>12亿笔</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>11.88亿笔（99%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">饼图（自动对账率</font>99%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>3“总账货币资金RTR黑灯：对账自动化率99%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击饼图</font>→弹出“对账异常类型”（如“跨行延迟占0.8%、数据不一致占0.2%”）</div>
</td></tr>
</tbody>
</table></object><br></div>
<div>好的，我们接着把<b>第二张看板：业务流程看板</b>的剩余部分补全，并且继续完善第三、四、五张看板的详细设计，确保<b>所有数据来源、展现形式、互动逻辑、设备参数</b>都完整，方便直接给 Gemini 等 AI 生成原型图 Demo。</div>
<div><br></div>
<div><b>④ 估值业务（文档1“估值核算” &amp 文档3“投资运营数智化跃迁”）</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">流程环节</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">日月年流入量</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">日月年完成量</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">交易数据采集</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">日均值</font>20万条</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">日均值</font>19.8万条（99%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">折线图（采集量趋势）</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“估值核算：日采集20万条交易数据”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击折线图</font>→弹出“采集来源”（如“核心交易系统、托管行直连、手工补录”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">估值核算</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">日均值</font>19.8万条</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">日均值</font>19.5万条（98.5%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">百分比圆环（自动核算率</font>98.5%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>3“投资运营数智化跃迁：自动核算率98.5%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover圆环→显示“人工干预原因”（如“特殊衍生品需手工估值”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">报表编制</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>6300份</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>6237份（99%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">数字</font>+百分比（自动编制率99%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“估值核算：报表自动生成率99%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击数字</font>→弹出“报表类型”（如“净值表、持仓表、损益表”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">核对</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>6237份</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">月均</font>6175份（99%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">对比图（系统核对</font>vs人工核对）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>3“养老险智能报表：核对自动化率99%”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover对比图→显示“系统核对逻辑”（如“自动比对估值系统与托管行数据”）</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>（3）底部：地区流程对比（文档1“五地布局”）</b><br></div>
<ul>
<li><b>地区流程热力图</b>：中国地图，颜色深浅=该地区在某业务环节的处理量占比（如上海资金支付占35%、深圳总账报表占40%、成都费用审核占30%）。</li>
<li><b>流程效率排名</b>：横向柱状图（X轴：地区，Y轴：效率指数，成都费用审核效率最高、上海资金支付效率最高、深圳总账报表效率最高）。</li>
<li><b>互动逻辑</b>：点击地区→弹出该地区该业务的<b>标杆案例</b>（如“成都：费用审核人均月处理1200单，AI审核覆盖率50%”）。</li>
</ul>
<div><b>4. 数字讲解员对外口径（文档1“建设成效”）</b><br></div>
<div>接下来我们看<b>业务流程看板</b>，这是财服“端到端自动化”的核心体现！以<b>费用业务</b>为例：从智能填单（月均25万单）→业务审批（96%通过）→财务审批（95.8%通过）→采集录入（99%自动）→文档复核（99%自动）→规则引擎审核（50%自动）→会计制证（100%自动），整个流程<b>99%发票自动采集、50%单据自动审核</b>，报销时效从15天压缩到15分钟！  再看<b>地区差异</b>：上海侧重资金支付（占35%）、深圳聚焦总账报表（占40%）、成都费用审核效率最高。我们的<b>财税业务</b>实现“测算-申报-归档”全自动化，申报成功率98.9%；<b>资金业务</b>日处理400万笔，支付成功率99%；<b>估值业务</b>人均产能提升15%，真正用流程数字化解决了“作业重复低效”的初期挑战！</div>
<div><br></div>
<div><b>第三张看板：客户价值看板——数字讲解员带你读懂财服的客户力</b><br></div>
<div><b>1. 核心定位</b><br></div>
<div>从“<b>客户覆盖、价值创造、商务信任</b>”三维度，呈现财服对<b>集团成员公司、员工、外部客户</b>的服务能力（文档1“客户服务”“建设成效”）。</div>
<div><b>2. 设备与布局</b><br></div>
<ul>
<li><b>主设备</b>：<b>LED一体屏（3926×1100mm，P1.8小间距）</b>；</li>
<li><b>辅助设备</b>：<b>触屏一体机（双屏，文档4“后屏：2万”）</b>；</li>
<li><b>布局逻辑</b>：顶部（客户分层标签）→主体（分客户维度卡片）→底部（案例卡片）。</li>
</ul>
<div><b>3. 详细内容设计</b><br></div>
<div><b>（1）顶部：客户分层标签</b><br></div>
<ul>
<li><b>客户类型</b>：集团成员公司、员工、外部客户（点击切换对应数据，默认“集团成员公司”）。</li>
</ul>
<div><b>（2）主体：分客户维度卡片</b><br></div>
<div><b>① 集团成员公司</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">指标名称</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">覆盖数量</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">数字</font>+单位（如“覆盖集团100%成员公司”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“集团成员公司全集中”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击数字</font>→弹出“成员公司名单（部分）”</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">服务场景</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">图标墙（费用报销、税务申报、总账报表、资金支付、估值核算、档案管理）</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“六大产品线”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击图标</font>→弹出“该场景的流程与成效”</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">专属服务经理</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">头像</font>+姓名（如“每家公司配备1名专属财服经理”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“SLA品质保证服务”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover头像→显示“经理联系方式与服务范围”</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>② 员工</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">指标名称</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">覆盖数量</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">数字</font>+单位（如“覆盖38万员工报销”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“费用报销”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击数字</font>→弹出“员工报销类型分布”（如“差旅费占60%、办公费占30%”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">报销体验</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">星级评分（如</font>“报销满意度4.8/5分”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“客户服务”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击星星</font>→弹出“满意度调研关键句”（如“报销快、AI准、少跑腿”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">降本感知</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">金币图标</font>+数字（如“员工平均报销时间从15天→15分钟，年节省时间50万小时”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“费用黑灯工厂”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击金币</font>→弹出“时间节省换算”（如“相当于每人每年多出2天假期”）</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>③ 外部客户</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">指标名称</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">覆盖数量</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">数字</font>+单位（如“服务10+外部企业档案管理”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“档案数电升级”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击数字</font>→弹出“外部客户名单（部分）”</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">合作场景</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">饼图（档案管理、税务咨询、财务共享咨询占比）</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“建设内容”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击饼图块</font>→弹出“合作案例简述”</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">信任背书</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">证书图标（如</font>“ISO27001信息安全认证、国家档案数字化试点单位”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“档案数电升级”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击证书</font>→弹出“认证详情与有效期”</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>（3）底部：客户价值案例卡片</b><br></div>
<ul>
<li><b>案例1</b>：某成员公司→资金支付自动化→年节省人力成本200万（配折线图：成本下降曲线）。</li>
<li><b>案例2</b>：某员工→报销从“跑3次签字”→“线上确认即完成”→体验提升90%（配对比图：传统流程vs数智流程）。</li>
<li><b>案例3</b>：某外部企业→档案数字化→查询时间从1天→1分钟（配流程图：扫描→OCR→检索→查看）。</li>
<li><b>互动逻辑</b>：点击案例→弹出<b>视频讲解</b>（1分钟，客户访谈+数据演示）。</li>
</ul>
<div><b>4. 数字讲解员对外口径（文档1“建设成效”）</b><br></div>
<div>各位来宾，财服的核心是“以客户为中心”！我们<b>覆盖集团100%成员公司</b>、<b>38万员工报销</b>，还为10+外部企业提供档案数字化服务。  对客户的价值体现在三点： 1. <b>覆盖全</b>：从费用到估值，六大场景全满足； 2. <b>体验好</b>：员工报销满意度4.8分，报销时间从15天→15分钟； 3. <b>降本实</b>：某成员公司通过资金支付自动化，年节省人力成本200万；某员工报销从“跑3次签字”变成“线上确认即完成”，体验提升90%；某外部企业用档案数字化，查询时间从1天压缩到1分钟。  我们不仅有<b>ISO27001信息安全认证</b>、<b>国家档案数字化试点单位</b>的信任背书，更用“专属服务经理”为每个客户解决个性化需求——这就是财服对“客户价值”的承诺：<b>让专业财务服务，省心、省时、又省钱</b>！</div>
<div><br></div>
<div><br></div>
<div><b>第四张看板：队伍能力看板——数字讲解员带你认识财服的“数字铁军”</b><br></div>
<div><b>1. 核心定位</b><br></div>
<div>从“<b>规模、能力、稳定性、文化</b>”四维度，呈现财服队伍的<b>专业化、数字化、年轻化</b>特征，突出“人才是数智化转型的核心”（文档1“队伍能力”“发展历程”）。</div>
<div><b>2. 设备与布局</b><br></div>
<ul>
<li><b>主设备</b>：<b>LED一体屏（3926×1100mm，P1.8小间距）</b>；</li>
<li><b>辅助设备</b>：<b>触屏笔</b>（用于点击人物/指标节点）；</li>
<li><b>布局逻辑</b>：顶部（队伍概览数字）→主体（规模/能力/稳定性/文化四模块）→底部（队伍风采案例）。</li>
</ul>
<div><b>3. 详细内容设计</b><br></div>
<div><b>（1）顶部：队伍概览数字（文档1“五地布局”“业务规模”）</b><br></div>
<ul>
<li>总人数：<b>1050+</b>（白色大字，动态累加动画）；</li>
<li>双证占比：<b>30%</b>（300+CPA/中高级，金色徽章图标）；</li>
<li>数字化专才占比：<b>60%</b>（630+人，蓝色芯片图标）；</li>
<li>平均司龄：<b>3.5年</b>（渐变时间轴图标）；</li>
<li>年流失率：<b>≤5%</b>（绿色下降箭头）。</li>
</ul>
<div><b>（2）主体：分维度模块</b><br></div>
<div><b>① 队伍规模与分布</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">指标名称</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">人员数量</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">动态数字（从</font>“0”→“1050+”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“五地布局求和”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击数字</font>→弹出“人员结构饼图”（财务运营60%、数字化技术20%、客户服务10%、管理10%）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">地区分布</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">中国地图</font>+气泡（上海200+、深圳200+、成都300+、合肥200+、内江150+）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“五地布局”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover气泡→显示“该地区主要岗位与人数”</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">岗位结构</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">饼图（财务运营</font>60%、数字化技术20%、客户服务10%、管理10%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“发展历程”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击饼图块</font>→弹出“岗位职责与技能要求”</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>② 队伍能力</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">指标名称</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">双证数（</font>CPA/中高级）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">证书图标</font>+数字（300+本，金色，动态排列）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“业务规模：300+CPA及中高级”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击图标</font>→弹出“双证人员分布”（总账岗40%、税务岗30%、资金岗20%、其他10%）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">数字化专才</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">技能雷达图（维度：</font>RPA、AI、规则引擎、BI、数据挖掘；得分≥8分）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>2“科技开发人员超2.1万”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover雷达图→显示“年度培训计划”（如2026年培养100名AI训练师）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">培训与发展</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">折线图（年培训时长人均</font>40小时，覆盖“AI应用”“数字化运营”等课程）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“建设成效”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击折线</font>→弹出“热门课程TOP3”（AI审核规则训练、RPA开发实战、数据可视化）</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>③ 队伍稳定性</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">指标名称</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">司龄分布</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">柱状图（</font>1-3年40%、3-5年35%、5年+25%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“发展历程”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击柱子</font>→弹出“司龄优势”（如5年+员工熟悉100+审核规则）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">流失率</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">绿色下降箭头（</font>8%→5%，标注“年流失率≤5%”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“建设成效”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击箭头</font>→弹出“留人举措”（数字化培训+晋升通道+弹性工作）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">敬业度</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">星级评分（</font>4.7/5分，金色星星）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“客户服务”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击星星</font>→弹出“敬业度调研关键因子”（工作成就感、团队氛围、成长空间）</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>④ 队伍文化</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">指标名称</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">核心价值观</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">标签云（专业、创新、协同、客户第一，字体越大认同度越高）</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>2“企业文化”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击标签</font>→弹出“价值观践行案例”（如“创新：开发RPA解决资金支付重复劳动”）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">团队活动</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">照片墙（数字化攻坚小组、年度技能大赛、员工生日会）</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“财服初心”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击照片</font>→弹出“活动视频剪辑”（1分钟）</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>（3）底部：队伍风采案例（文档1“业务规模”“建设成效”）</b><br></div>
<ul>
<li><b>案例1</b>：张敏（成都，10年司龄，CPA+数字化专才）→主导费用黑灯工厂AI审核规则训练→效率提升50%。</li>
<li><b>案例2</b>：李阳（上海，5年司龄，RPA专家）→开发资金支付RPA覆盖8大场景→年节省人力1000小时。</li>
<li><b>案例3</b>：王芳（深圳，3年司龄，AI产品经理）→主导税务智能助手上线→申报效率提升20%。</li>
<li><b>互动逻辑</b>：点击人物头像→弹出<b>成长视频</b>（2分钟，讲述个人攻关故事+数据成果）。</li>
</ul>
<div><b>4. 数字讲解员对外口径</b><br></div>
<div>财服的“数智化成果”，背后是一支**“专业+数字”的铁军**！我们有1050+人，300+持双证（CPA/中高级），630+是数字化专才（覆盖RPA、AI等技能），平均司龄3.5年，年流失率≤5%——稳定的队伍是转型的底气！  我们的队伍<b>能力强</b>：人均年培训40小时，数字化专才的技能雷达图得分≥8分；<b>文化牢</b>：以“专业、创新、协同、客户第一”为核心，去年“数字化攻坚小组”主导的“费用黑灯工厂”，让报销效率提升50%！  比如成都的张敏，10年司龄，用AI规则训练把费用审核效率提了50%；上海的李阳，开发的资金支付RPA覆盖8大场景，年省1000小时人力——这就是我们的“数字铁军”：<b>用专业守初心，用数字创价值</b>！</div>
<div><br></div>
<div><b>第五张看板：AI赋能看板——数字讲解员带你揭秘财服的“数智大脑”</b><br></div>
<div><b>1. 核心定位</b><br></div>
<div>从“<b>数字员工（RPA+小工具）、AI Agent（智能体）、AI成效</b>”三维度，呈现AI如何“替人、提效、控险”，突出“科技是第一生产力”（文档1“数字员工集群”“AI赋能”）。</div>
<div><b>2. 设备与布局</b><br></div>
<ul>
<li><b>主设备</b>：<b>LED一体屏（3926×1100mm，P1.8小间距）</b>；</li>
<li><b>辅助设备</b>：<b>iPad Pro（用于控制智能体试用）</b>；</li>
<li><b>布局逻辑</b>：顶部（AI概览数字）→主体（数字员工/AI Agent/AI成效三模块）→底部（AI未来规划 Roadmap）。</li>
</ul>
<div><b>3. 详细内容设计</b><br></div>
<div><b>（1）顶部：AI概览数字（文档1“数字员工集群”“降本提效”）</b><br></div>
<ul>
<li>RPA机器人：<b>70+</b>（蓝色机器人图标，动态排列）；</li>
<li>智能体：<b>50+</b>（紫色大脑图标）；</li>
<li>小工具：<b>20+</b>（灰色工具图标）；</li>
<li>任务成功率：<b>≥98%</b>（绿色仪表盘）；</li>
<li>等效人力：<b>2000+小时/年</b>（人头图标，动态累加）。</li>
</ul>
<div><b>（2）主体：分维度模块</b><br></div>
<div><b>① 数字员工（RPA+小工具）</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">指标名称</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>RPA数量与分布</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">机器人图标</font>+饼图（资金30%、费用25%、税务20%、总账15%、估值10%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“数字员工集群”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击饼图块</font>→弹出“该场景RPA流程视频”</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">小工具矩阵</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">工具图标墙（</font>OCR、NLP、规则引擎、BI、数据埋点）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“技术应用”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击工具</font>→进入<b>试用模式</b>（如上传发票→OCR识别→实时显示结果）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">数字场景覆盖</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">流程图（费用审核</font>→资金支付→税务申报→总账制证→估值核算，标注RPA/小工具）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“建设内容”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击环节</font>→弹出“该环节AI替代率与成效”</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">任务执行情况</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">实时滚动列表（如</font>“RPA-资金支付：今日完成任务1000笔，成功率99.5%”）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“RPA作业效益衡量”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover列表→显示“任务详情与异常原因”</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>② AI Agent（智能体）</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">指标名称</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">智能体数量与分类</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">大脑图标</font>+标签云（财务会计20、税务支持15、管理会计10、金融支持5）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>3“费用全域智控”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击标签</font>→弹出“智能体功能演示”（如费用AI审核：上传报销单→实时审核结果）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">核心智能体案例</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">卡片式（费用</font>AI审核：7类费用、准确率95%；预算AI智审：效率提升20%；税务AI助手：错误率下降30%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>3“项目明细”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击卡片</font>→弹出<b>案例视频</b>（1分钟，客户访谈+数据演示）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">智能体训练与迭代</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">折线图（月均训练</font>10个智能体，迭代优化率≥80%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“AIGC智能识别”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击折线</font>→弹出“训练数据源与算法简介”</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>③ AI成效与价值</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">指标名称</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">展现形式</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">数据来源与数值</font></b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b><font face=".PingFangUITextSC-Bold">互动逻辑</font></b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">等效人力</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">人头图标</font>+数字（2000+小时/年）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“降本提效”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击人头</font>→弹出“等效人力价值换算”（如=少用10名全职员工）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">效率提升</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">对比柱状图（费用审核</font>+50%、资金支付+40%、税务申报+20%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“建设成效”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>hover柱子→显示“提升关键措施”（如费用审核：AI规则优化+自动采集）</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">风险控制</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">折线图（</font>AI风控拦截风险数年增长40%，从10万→14万次）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“智能风控”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击折线</font>→弹出“风险类型与拦截逻辑”</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">成本优化</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">金币图标</font>+数字（年降本7000万，AI贡献40%）</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">文档</font>1“建设成效”</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">点击金币</font>→弹出“降本构成饼图”（AI替人40%、流程优化30%、规模效应30%）</div>
</td></tr>
</tbody>
</table></object><br></div>
<div><b>（3）底部：AI未来规划 Roadmap（文档1“AI未来规划”）</b><br></div>
<ul>
<li><b>2026年</b>：上线“多模态大模型”→覆盖更多“开放式凭证”识别；</li>
<li><b>2027年</b>：实现“全场景AI自治”→费用审核无人化率提升至70%；</li>
<li><b>2028年</b>：AI等效人力突破5000小时/年，成为财服“核心生产力”。</li>
<li><b>互动逻辑</b>：点击年份→弹出<b>概念视频</b>（30秒，展示未来场景：AI自动处理全业务，人类专注分析与决策）。</li>
</ul>
<div><b>4. 数字讲解员对外口径</b><br></div>
<div>最后一张看板，我们揭秘财服的“数智大脑”——<b>AI赋能</b>！我们有70+RPA机器人、50+智能体、20+小工具，任务成功率≥98%，<b>等效替代2000+人工小时/年</b>。  看<b>数字员工</b>：RPA覆盖资金（30%）、费用（25%）、税务（20%）等场景，比如“资金支付RPA”覆盖8大场景，年省1000小时；“OCR小工具”实现99%发票自动采集。<b>AI Agent</b>更智能：费用AI审核覆盖7类费用，准确率95%；预算AI智审让激励费审核效率提升20%；税务AI助手让申报错误率下降30%。  AI的<b>价值</b>看得见：效率上，费用审核提升50%、资金支付提升40%；风控上，年拦截风险14万次（增长40%）；成本上，年降本7000万，AI贡献40%！  未来我们要做“全场景AI自治”：2026年上线多模态大模型，2027年费用无人化率提至70%，2028年等效人力破5000小时——<b>用AI让财服更智能，让服务更卓越</b>！</div>
<div><br></div>
<div>✅ <b>至此，五张看板的详细设计已全部完成</b>，包含：</div>
<ul>
<li><b>核心定位</b><br></li>
<li><b>设备与布局</b>（型号、尺寸、辅助设备）</li>
<li><b>详细内容设计</b>（表格形式：指标名称、展现形式、数据来源与数值、互动逻辑）</li>
<li><b>数字讲解员对外口径</b>（可直接用于展示解说）</li>
</ul>
<div>所有数据、展现方式、互动逻辑均可追溯至<b>文档1~4</b>，并已考虑<b>展厅升级方案</b>的设备与体验要求，能够直接交付 Gemini 等 AI 生成<b>高保真原型图 Demo</b>。</div>
<div>如果需要，我可以帮你把这五张看板的<b>原型图Prompt模板</b>也整理出来，方便一次性生成全部Demo。你需要我继续做这个吗？</div>
<div>好的，我们继续为这五张看板输出<b>可直接用于 Gemini / Midjourney / Figma AI 等工具的「原型图 Prompt 模板」</b>，让设计师或 AI 能精准还原我们上面定义的布局、数据、展现形式和互动逻辑。</div>
<div>我会按照<b>每张看板 → 画面描述 → 布局结构 → 数据与视觉元素 → 互动提示 → 风格参数</b>的格式来写，方便直接调用生成高保真 Demo。</div>
<div><br></div>
<div><b>通用风格参数（适用于全部看板）</b><br></div>
<ul>
<li><b>画幅比例</b>：21:9（对应 LED 一体屏 3926×1100mm，P1.8 小间距）</li>
<li><b>色彩体系</b>：平安品牌色为主（主蓝 #005BAC、辅灰 #333333、强调金 #FFD700、警示红 #E74C3C、成功绿 #27AE60）</li>
<li><b>字体</b>：中文用思源黑体 Bold/Medium，英文用 Roboto，数字用 DIN</li>
<li><b>质感</b>：科技光效（柔光晕、数据粒子流）、轻微磨砂玻璃面板（半透明模块背景）、扁平化 KPI 图标</li>
<li><b>动效提示</b>：在原型图里用箭头/闪烁/流动线标注实时数据更新区域；交互热点用虚线框+手型图标示意</li>
</ul>
<div><br></div>
<div><b>看板1：财服全景看板 Prompt</b><br></div>
<div><b>画面描述</b>： 全景式智慧财服中心驾驶舱，左侧业务+客户指标区，中间中国地图热力分布，右侧队伍+AI指标区，整体呈横向三段式布局，背景深色星空渐变，点缀流动数据粒子。</div>
<div><b>布局结构</b>：</div>
<ul>
<li><b>左1/3</b>：上下两区块 — 上区块业务指标（规模/质量/效率/风控，含折线图、仪表盘、圆环图、计数器），下区块客户指标（规模/价值/商务，含饼图、星级、金币图标）。</li>
<li><b>中1/3</b>：中国地图热力图，5大城市气泡标注人员规模与业务占比，hover 连线显示实时数据。</li>
<li><b>右1/3</b>：上下两区块 — 上区块队伍指标（规模/能力/稳定性，含柱状图、雷达图、折线图），下区块AI指标（数字员工/AI Agent，含机器人图标、大脑图标、词云、等效人力人头）。</li>
</ul>
<div><b>数据与视觉元素</b>：</div>
<ul>
<li>动态数字：资金吞吐量 12亿+笔/年、账套 2000+、一次通过率 85%、月结时效 5→2 天、风险拦截 14万次、人员 1050+、双证 300+、RPA 70+、智能体 50+。</li>
<li>图表：热力地图、饼图、折线图、仪表盘、圆环图、雷达图、词云、滚动计数器。</li>
<li>图标：机器人、大脑、证书、金币、人头、地图标记。</li>
</ul>
<div><b>互动提示</b>：</div>
<ul>
<li>用虚线框标出可点击区域（如折线图节点、地图城市、证书图标），旁边加 “Tap to view details” 手型提示。</li>
<li>实时更新区域用闪烁边框（如风险拦截数、等效人力）。</li>
</ul>
<div><b>Prompt示例（英文/可直投AI）</b>：</div>
<div>A panoramic smart financial shared service cockpit, 21:9 ratio, dark blue gradient background with flowing data particles. Layout: left 1/3 shows business indicators (scale/quality/efficiency/risk control) with line charts, gauges, donut charts, counters; below it customer indicators (pie chart, star rating, gold coin icon). Center 1/3 is a China heatmap with bubbles for Shanghai/Shenzhen/Chengdu/Hefei/Neijiang, showing personnel and business share. Right 1/3 shows team indicators (bar chart, radar chart, line chart) on top, AI metrics (robot icons, brain icons, word cloud, human head icons) at bottom. Use Ping An brand colors (main blue #005BAC, gold #FFD700, green #27AE60). Add clickable areas marked with dashed lines and hand cursor hints. Real-time update zones have glowing borders. Flat design with glass-morphism panels.</div>
<div><br></div>
<div><b>看板2：业务流程看板 Prompt</b><br></div>
<div><b>画面描述</b>： 流程型智慧财服驾驶舱，顶部业务条线与地区筛选栏，主体为四大业务（费用、财税、资金、估值）端到端流程图，底部地区效率排名热力图与柱状图。</div>
<div><b>布局结构</b>：</div>
<ul>
<li><b>顶部</b>：水平筛选栏（业务条线：费用/财税/资金/估值；地区：上海/深圳/成都/合肥/内江）。</li>
<li><b>主体</b>：每个业务一个纵向流程泳道，环节用漏斗图、进度条、折线图、饼图、对比图表现日月年流入/完成量。</li>
<li><b>底部</b>：中国地图热力图+横向柱状图（地区效率排名）。</li>
</ul>
<div><b>数据与视觉元素</b>：</div>
<ul>
<li>动态数字：费用月均25万单、财税月均5000笔、资金日均400万笔、估值日采20万条。</li>
<li>图表：流程图泳道、漏斗图、进度条、折线图、饼图、对比图、热力图、柱状图。</li>
<li>图标：时钟、文件、机器人、数据库符号。</li>
</ul>
<div><b>互动提示</b>：</div>
<ul>
<li>流程节点用发光圆点+ Tap 提示，点击弹出案例视频或规则说明。</li>
<li>地区筛选栏按钮用按下状态样式标示当前选中。</li>
</ul>
<div><b>Prompt示例</b>：</div>
<div>Process-oriented smart finance cockpit, 21:9, dark theme with light blue accents. Top bar with selectable business line (Expense/Tax/Fund/Valuation) and region filters (Shanghai/Shenzhen/Chengdu/Hefei/Neijiang). Main area: four vertical swimlanes showing end-to-end process flows for each business, using funnel charts, progress bars, line charts, pie charts, comparison graphs. Bottom: China heatmap + horizontal bar chart for regional efficiency ranking. Include dynamic numbers like 250k expense orders/month, 400k fund transactions/day. Use glass panels, Ping An colors, and mark interactive nodes with glowing dots and &quotTap&quot hint.</div>
<div><br></div>
<div><b>看板3：客户价值看板 Prompt</b><br></div>
<div><b>画面描述</b>： 客户价值智慧看板，顶部客户分层标签（集团成员公司/员工/外部客户），主体为客户维度卡片（覆盖数量、服务场景、满意度、降本感知、信任背书），底部案例卡片与视频弹窗示意。</div>
<div><b>布局结构</b>：</div>
<ul>
<li><b>顶部</b>：标签式导航栏，当前选中标签高亮。</li>
<li><b>主体</b>：三列卡片（集团/员工/外部客户），每卡含数字、图标墙、饼图、星级、证书图标。</li>
<li><b>底部</b>：横向滚动案例卡片，带视频播放图标。</li>
</ul>
<div><b>数据与视觉元素</b>：</div>
<ul>
<li>数字：覆盖100%成员公司、38万员工、10+外部企业、满意度4.8分、降本7000万/年。</li>
<li>图表：图标墙、饼图、星级评分、证书图标。</li>
<li>案例配对比图/流程图/折线图。</li>
</ul>
<div><b>互动提示</b>：</div>
<ul>
<li>卡片悬停高亮，点击弹出视频浮层（半透明遮罩+播放键）。</li>
<li>标签切换带动画过渡。</li>
</ul>
<div><b>Prompt示例</b>：</div>
<div>Customer value dashboard, 21:9, modern dark UI. Top tab navigation: Group Companies/Employees/External Clients. Main section: three-column cards with numbers, icon walls, pie charts, star ratings, certificate icons. Bottom: horizontally scrollable case study cards with video play icons. Values: 100% group coverage, 380k employees, satisfaction 4.8/5, cost reduction 70M/year. Use glass-card style, Ping An palette, highlight interactive cards on hover, show video popup on click.</div>
<div><br></div>
<div><b>看板4：队伍能力看板 Prompt</b><br></div>
<div><b>画面描述</b>： 队伍能力看板，顶部概览数字（总人数、双证占比、数字化专才占比、司龄、流失率），主体四模块（规模分布、能力、稳定性、文化），底部人物案例与视频。</div>
<div><b>布局结构</b>：</div>
<ul>
<li><b>顶部</b>：大数字 KPI 横排，带图标。</li>
<li><b>主体</b>：四象限模块，每模块含柱状图、饼图、雷达图、标签云、照片墙。</li>
<li><b>底部</b>：人物头像+简介卡片，可点击播放成长视频。</li>
</ul>
<div><b>数据与视觉元素</b>：</div>
<ul>
<li>数字：1050+人、30%双证、60%数字化专才、3.5年平均司龄、≤5%流失率。</li>
<li>图表：地图气泡、饼图、雷达图、柱状图、标签云、照片墙。</li>
</ul>
<div><b>互动提示</b>：</div>
<ul>
<li>数字点击弹出结构细分，雷达图悬停显示培训计划，人物卡片点击播放视频。</li>
</ul>
<div><b>Prompt示例</b>：</div>
<div>Team capability dashboard, 21:9, dark interface with blue-green tones. Top row of large KPI numbers (1050+ staff, 30% dual-certified, etc.) with icons. Four main modules: scale/distribution, competence, stability, culture—each with maps, pie/radar/bar charts, tag clouds, photo walls. Bottom: staff profile cards with clickable video playback. Show Ping An branding, glass effects, interactive highlights on hover/click.</div>
<div><br></div>
<div><b>看板5：AI赋能看板 Prompt</b><br></div>
<div><b>画面描述</b>： AI赋能看板，顶部AI概览数字（RPA数量、智能体、小工具、成功率、等效人力），主体三部分（数字员工、AI Agent、AI成效），底部未来 Roadmap 时间轴。</div>
<div><b>布局结构</b>：</div>
<ul>
<li><b>顶部</b>：KPI 横排+仪表盘。</li>
<li><b>主体</b>：三列模块，每列含饼图、工具墙、流程图、案例卡片、折线图。</li>
<li><b>底部</b>：横向时间轴（2026/2027/2028），带概念视频图标。</li>
</ul>
<div><b>数据与视觉元素</b>：</div>
<ul>
<li>数字：70+RPA、50+智能体、20+工具、≥98%成功率、2000+等效人力。</li>
<li>图表：饼图、工具墙、流程图、案例卡片、折线图、时间轴。</li>
</ul>
<div><b>互动提示</b>：</div>
<ul>
<li>工具墙点击进入试用模式示意，案例卡片点击播放视频，时间轴节点点击弹出未来场景视频。</li>
</ul>
<div><b>Prompt示例</b>：</div>
<div>AI empowerment dashboard, 21:9, futuristic dark UI with purple-blue tones. Top KPI bar: 70+ RPA, 50+ agents, ≥98% success rate, 2000+等效人力, shown with icons and gauges. Three main columns: Digital Employees (pie charts, tool walls, flowcharts), AI Agents (tag clouds, case cards), AI Outcomes (comparison charts, line charts). Bottom: horizontal timeline 2026-2028 with concept video icons. Use Ping An colors, glass panels, interactive hints for tools/cases/timeline.</div>
<div><br></div>
<div>✅ <b>到这里，五张看板的「原型图 Prompt 模板」已经完整</b>，每张都包含画面描述、布局、数据、互动提示与英文 Prompt，可直接投给 Gemini / Midjourney / Figma AI 等工具生成高保真 Demo。</div>
<div>如果你需要，我还可以帮你<b>把这 5 份 Prompt 合成一个批量生成的 JSON 或 CSV</b>，方便一次性输入到 AI 绘图流程里，你要我继续做这个吗？这样我们就可以直接进入 Demo 产出阶段。</div>
<div>生成脑图</div>
<div>如何选择适合的动效提示方式</div>
<div>如何优化看板的数据可视化效果</div>
<div>如何调整看板的色彩搭配方案</div>
<div>继续</div>
<div>2026-02-27 10:22</div>
<div><br></div>
<div>ima</div>
<div>好的，我们继续把<b>五张看板的 Prompt 模板整合成「批量生成用的结构化数据包」</b>，方便一次性导入 Gemini、Midjourney、Figma AI 或其他绘图/原型工具进行批量渲染。</div>
<div>我会输出成两种通用格式：</div>
<ol>
<li><b>JSON 数组</b>（适合程序化调用、API 批量生成）</li>
<li><b>CSV 表格</b>（适合 Excel / Google Sheets 编辑、低代码平台导入）</li>
</ol>
<div><br></div>
<div><b>1️⃣ JSON 批量 Prompt 数据包</b><br></div>
<div>json</div>
<div>[</div>
<div>  {</div>
<div>    &quotboardName&quot: &quot财服全景看板&quot,</div>
<div>    &quotratio&quot: &quot21:9&quot,</div>
<div>    &quotdescription&quot: &quot全景式智慧财服中心驾驶舱，左侧业务+客户指标区，中间中国地图热力分布，右侧队伍+AI指标区，整体呈横向三段式布局，背景深色星空渐变，点缀流动数据粒子。&quot,</div>
<div>    &quotlayout&quot: &quot左1/3: 业务指标(规模/质量/效率/风控)+客户指标(规模/价值/商务); 中1/3: 中国地图热力图+城市气泡; 右1/3: 队伍指标(规模/能力/稳定性)+AI指标(数字员工/AI Agent)&quot,</div>
<div>    &quotdataElements&quot: [</div>
<div>      &quot资金吞吐量 12亿+笔/年&quot,</div>
<div>      &quot账套 2000+&quot,</div>
<div>      &quot一次通过率 85%&quot,</div>
<div>      &quot月结时效 5→2天&quot,</div>
<div>      &quot风险拦截 14万次&quot,</div>
<div>      &quot人员 1050+&quot,</div>
<div>      &quot双证 300+&quot,</div>
<div>      &quotRPA 70+&quot,</div>
<div>      &quot智能体 50+&quot</div>
<div>    ],</div>
<div>    &quotvisuals&quot: [&quot折线图&quot,&quot仪表盘&quot,&quot圆环图&quot,&quot计数器&quot,&quot饼图&quot,&quot星级&quot,&quot金币图标&quot,&quot热力地图&quot,&quot雷达图&quot,&quot词云&quot,&quot人头图标&quot],</div>
<div>    &quotinteractionHints&quot: &quot可点击区域用虚线框+手型提示；实时更新区用闪烁边框&quot,</div>
<div>    &quotstyle&quot: &quot主蓝 #005BAC, 辅灰 #333333, 金 #FFD700, 红 #E74C3C, 绿 #27AE60; 科技光效+磨砂玻璃面板; 扁平化KPI图标&quot,</div>
<div>    &quotpromptEN&quot: &quotA panoramic smart financial shared service cockpit, 21:9 ratio, dark blue gradient background with flowing data particles. Layout: left 1/3 shows business indicators (scale/quality/efficiency/risk control) with line charts, gauges, donut charts, counters; below it customer indicators (pie chart, star rating, gold coin icon). Center 1/3 is a China heatmap with bubbles for Shanghai/Shenzhen/Chengdu/Hefei/Neijiang, showing personnel and business share. Right 1/3 shows team indicators (bar chart, radar chart, line chart) on top, AI metrics (robot icons, brain icons, word cloud, human head icons) at bottom. Use Ping An brand colors (main blue #005BAC, gold #FFD700, green #27AE60). Add clickable areas marked with dashed lines and hand cursor hints. Real-time update zones have glowing borders. Flat design with glass-morphism panels.&quot</div>
<div>  },</div>
<div>  {</div>
<div>    &quotboardName&quot: &quot业务流程看板&quot,</div>
<div>    &quotratio&quot: &quot21:9&quot,</div>
<div>    &quotdescription&quot: &quot流程型智慧财服驾驶舱，顶部业务条线与地区筛选栏，主体为四大业务端到端流程图，底部地区效率排名热力图与柱状图。&quot,</div>
<div>    &quotlayout&quot: &quot顶部: 业务条线+地区筛选栏; 主体: 四大业务纵向流程泳道(费用/财税/资金/估值); 底部: 热力图+效率排名柱状图&quot,</div>
<div>    &quotdataElements&quot: [</div>
<div>      &quot费用月均25万单&quot,</div>
<div>      &quot财税月均5000笔&quot,</div>
<div>      &quot资金日均400万笔&quot,</div>
<div>      &quot估值日采20万条&quot</div>
<div>    ],</div>
<div>    &quotvisuals&quot: [&quot流程图泳道&quot,&quot漏斗图&quot,&quot进度条&quot,&quot折线图&quot,&quot饼图&quot,&quot对比图&quot,&quot热力图&quot,&quot柱状图&quot],</div>
<div>    &quotinteractionHints&quot: &quot流程节点用发光圆点+Tap提示; 地区筛选栏按钮用按下状态&quot,</div>
<div>    &quotstyle&quot: &quot主蓝 #005BAC, 浅蓝点缀; 玻璃面板; 扁平化图标&quot,</div>
<div>    &quotpromptEN&quot: &quotProcess-oriented smart finance cockpit, 21:9, dark theme with light blue accents. Top bar with selectable business line (Expense/Tax/Fund/Valuation) and region filters (Shanghai/Shenzhen/Chengdu/Hefei/Neijiang). Main area: four vertical swimlanes showing end-to-end process flows for each business, using funnel charts, progress bars, line charts, pie charts, comparison graphs. Bottom: China heatmap + horizontal bar chart for regional efficiency ranking. Include dynamic numbers like 250k expense orders/month, 400k fund transactions/day. Use glass panels, Ping An colors, and mark interactive nodes with glowing dots and \&quotTap\&quot hint.&quot</div>
<div>  },</div>
<div>  {</div>
<div>    &quotboardName&quot: &quot客户价值看板&quot,</div>
<div>    &quotratio&quot: &quot21:9&quot,</div>
<div>    &quotdescription&quot: &quot客户价值智慧看板，顶部客户分层标签，主体为客户维度卡片，底部案例卡片与视频弹窗示意。&quot,</div>
<div>    &quotlayout&quot: &quot顶部: 客户分层标签栏; 主体: 三列卡片(集团/员工/外部客户); 底部: 横向滚动案例卡片+视频图标&quot,</div>
<div>    &quotdataElements&quot: [</div>
<div>      &quot覆盖100%成员公司&quot,</div>
<div>      &quot38万员工&quot,</div>
<div>      &quot10+外部企业&quot,</div>
<div>      &quot满意度4.8分&quot,</div>
<div>      &quot降本7000万/年&quot</div>
<div>    ],</div>
<div>    &quotvisuals&quot: [&quot图标墙&quot,&quot饼图&quot,&quot星级评分&quot,&quot证书图标&quot,&quot对比图&quot,&quot流程图&quot,&quot折线图&quot],</div>
<div>    &quotinteractionHints&quot: &quot卡片悬停高亮; 点击弹出视频浮层&quot,</div>
<div>    &quotstyle&quot: &quot主蓝 #005BAC, 金 #FFD700, 绿 #27AE60; 玻璃卡片; 平滑动画过渡&quot,</div>
<div>    &quotpromptEN&quot: &quotCustomer value dashboard, 21:9, modern dark UI. Top tab navigation: Group Companies/Employees/External Clients. Main section: three-column cards with numbers, icon walls, pie charts, star ratings, certificate icons. Bottom: horizontally scrollable case study cards with video play icons. Values: 100% group coverage, 380k employees, satisfaction 4.8/5, cost reduction 70M/year. Use glass-card style, Ping An palette, highlight interactive cards on hover, show video popup on click.&quot</div>
<div>  },</div>
<div>  {</div>
<div>    &quotboardName&quot: &quot队伍能力看板&quot,</div>
<div>    &quotratio&quot: &quot21:9&quot,</div>
<div>    &quotdescription&quot: &quot队伍能力看板，顶部概览数字，主体四模块，底部人物案例与视频。&quot,</div>
<div>    &quotlayout&quot: &quot顶部: 大数字KPI横排; 主体: 四象限模块(规模分布/能力/稳定性/文化); 底部: 人物头像卡片+视频&quot,</div>
<div>    &quotdataElements&quot: [</div>
<div>      &quot1050+人&quot,</div>
<div>      &quot30%双证&quot,</div>
<div>      &quot60%数字化专才&quot,</div>
<div>      &quot3.5年平均司龄&quot,</div>
<div>      &quot≤5%流失率&quot</div>
<div>    ],</div>
<div>    &quotvisuals&quot: [&quot地图气泡&quot,&quot饼图&quot,&quot雷达图&quot,&quot柱状图&quot,&quot标签云&quot,&quot照片墙&quot],</div>
<div>    &quotinteractionHints&quot: &quot数字点击弹出结构细分; 雷达图悬停显示培训计划; 人物卡片点击播放视频&quot,</div>
<div>    &quotstyle&quot: &quot蓝绿调; 玻璃面板; 科技感光效&quot,</div>
<div>    &quotpromptEN&quot: &quotTeam capability dashboard, 21:9, dark interface with blue-green tones. Top row of large KPI numbers (1050+ staff, 30% dual-certified, etc.) with icons. Four main modules: scale/distribution, competence, stability, culture—each with maps, pie/radar/bar charts, tag clouds, photo walls. Bottom: staff profile cards with clickable video playback. Show Ping An branding, glass effects, interactive highlights on hover/click.&quot</div>
<div>  },</div>
<div>  {</div>
<div>    &quotboardName&quot: &quotAI赋能看板&quot,</div>
<div>    &quotratio&quot: &quot21:9&quot,</div>
<div>    &quotdescription&quot: &quotAI赋能看板，顶部AI概览数字，主体三部分，底部未来Roadmap时间轴。&quot,</div>
<div>    &quotlayout&quot: &quot顶部: KPI横排+仪表盘; 主体: 三列模块(数字员工/AI Agent/AI成效); 底部: 横向时间轴+概念视频图标&quot,</div>
<div>    &quotdataElements&quot: [</div>
<div>      &quot70+RPA&quot,</div>
<div>      &quot50+智能体&quot,</div>
<div>      &quot20+工具&quot,</div>
<div>      &quot≥98%成功率&quot,</div>
<div>      &quot2000+等效人力&quot</div>
<div>    ],</div>
<div>    &quotvisuals&quot: [&quot饼图&quot,&quot工具墙&quot,&quot流程图&quot,&quot案例卡片&quot,&quot折线图&quot,&quot时间轴&quot],</div>
<div>    &quotinteractionHints&quot: &quot工具墙点击进入试用模式; 案例卡片点击播放视频; 时间轴节点点击弹出未来场景视频&quot,</div>
<div>    &quotstyle&quot: &quot紫蓝调; 玻璃面板; 未来感光效&quot,</div>
<div>    &quotpromptEN&quot: &quotAI empowerment dashboard, 21:9, futuristic dark UI with purple-blue tones. Top KPI bar: 70+ RPA, 50+ agents, ≥98% success rate, 2000+等效人力, shown with icons and gauges. Three main columns: Digital Employees (pie charts, tool walls, flowcharts), AI Agents (tag clouds, case cards), AI Outcomes (comparison charts, line charts). Bottom: horizontal timeline 2026-2028 with concept video icons. Use Ping An colors, glass panels, interactive hints for tools/cases/timeline.&quot</div>
<div>  }</div>
<div>]</div>
<div><br></div>
<div><b>2️⃣ CSV 批量 Prompt 表格</b><br></div>
<div><object><table cellspacing="0" cellpadding="0" style="border-collapse: collapse; direction: ltr">
<tbody>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b>boardName</b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b>ratio</b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b>description</b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b>layout</b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b>dataElements</b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b>visuals</b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b>interactionHints</b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b>style</b></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><b>promptEN</b></div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">财服全景看板</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>21:9</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">全景式智慧财服中心驾驶舱，左侧业务</font>+客户指标区，中间中国地图热力分布，右侧队伍+AI指标区，整体呈横向三段式布局，背景深色星空渐变，点缀流动数据粒子。</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">左</font>1/3: 业务指标(规模/质量/效率/风控)+客户指标(规模/价值/商务); 中1/3: 中国地图热力图+城市气泡; 右1/3: 队伍指标(规模/能力/稳定性)+AI指标(数字员工/AI Agent)</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">资金吞吐量</font> 12亿+笔/年,账套 2000+,一次通过率 85%,月结时效 5→2天,风险拦截 14万次,人员 1050+,双证 300+,RPA 70+,智能体 50+</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">折线图</font>,仪表盘,圆环图,计数器,饼图,星级,金币图标,热力地图,雷达图,词云,人头图标</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">可点击区域用虚线框</font>+手型提示；实时更新区用闪烁边框</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">主蓝</font> #005BAC, 辅灰 #333333, 金 #FFD700, 红 #E74C3C, 绿 #27AE60; 科技光效+磨砂玻璃面板; 扁平化KPI图标</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>A panoramic smart financial shared service cockpit, 21:9 ratio, dark blue gradient background with flowing data particles...</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">业务流程看板</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>21:9</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">流程型智慧财服驾驶舱，顶部业务条线与地区筛选栏，主体为四大业务端到端流程图，底部地区效率排名热力图与柱状图。</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">顶部</font>: 业务条线+地区筛选栏; 主体: 四大业务纵向流程泳道(费用/财税/资金/估值); 底部: 热力图+效率排名柱状图</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">费用月均</font>25万单,财税月均5000笔,资金日均400万笔,估值日采20万条</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">流程图泳道</font>,漏斗图,进度条,折线图,饼图,对比图,热力图,柱状图</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">流程节点用发光圆点</font>+Tap提示; 地区筛选栏按钮用按下状态</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">主蓝</font> #005BAC, 浅蓝点缀; 玻璃面板; 扁平化图标</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>Process-oriented smart finance cockpit, 21:9, dark theme with light blue accents...</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">客户价值看板</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>21:9</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">客户价值智慧看板，顶部客户分层标签，主体为客户维度卡片，底部案例卡片与视频弹窗示意。</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">顶部</font>: 客户分层标签栏; 主体: 三列卡片(集团/员工/外部客户); 底部: 横向滚动案例卡片+视频图标</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">覆盖</font>100%成员公司,38万员工,10+外部企业,满意度4.8分,降本7000万/年</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">图标墙</font>,饼图,星级评分,证书图标,对比图,流程图,折线图</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">卡片悬停高亮</font>; 点击弹出视频浮层</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">主蓝</font> #005BAC, 金 #FFD700, 绿 #27AE60; 玻璃卡片; 平滑动画过渡</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>Customer value dashboard, 21:9, modern dark UI...</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">队伍能力看板</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>21:9</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">队伍能力看板，顶部概览数字，主体四模块，底部人物案例与视频。</font></div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">顶部</font>: 大数字KPI横排; 主体: 四象限模块(规模分布/能力/稳定性/文化); 底部: 人物头像卡片+视频</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>1050+人,30%双证,60%数字化专才,3.5年平均司龄,≤5%流失率</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">地图气泡</font>,饼图,雷达图,柱状图,标签云,照片墙</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">数字点击弹出结构细分</font>; 雷达图悬停显示培训计划; 人物卡片点击播放视频</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">蓝绿调</font>; 玻璃面板; 科技感光效</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>Team capability dashboard, 21:9, dark interface with blue-green tones...</div>
</td></tr>
<tr><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>AI赋能看板</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>21:9</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>AI赋能看板，顶部AI概览数字，主体三部分，底部未来Roadmap时间轴。</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">顶部</font>: KPI横排+仪表盘; 主体: 三列模块(数字员工/AI Agent/AI成效); 底部: 横向时间轴+概念视频图标</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>70+RPA,50+智能体,20+工具,≥98%成功率,2000+等效人力</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">饼图</font>,工具墙,流程图,案例卡片,折线图,时间轴</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">工具墙点击进入试用模式</font>; 案例卡片点击播放视频; 时间轴节点点击弹出未来场景视频</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div><font face=".PingFangUITextSC-Regular">紫蓝调</font>; 玻璃面板; 未来感光效</div>
</td><td valign="top" style="border-style: solid; border-width: 1.0px 1.0px 1.0px 1.0px; border-color: #ccc; padding: 3.0px 5.0px 3.0px 5.0px; min-width: 70px"><div>AI empowerment dashboard, 21:9, futuristic dark UI with purple-blue tones...</div>
</td></tr>
</tbody>
</table></object><br></div>
<div>⚠️ CSV 里的 promptEN 列因长度限制做了截断，实际使用时请复制 JSON 中的完整英文 Prompt。</div>
<div><br></div>
<div><b>使用建议</b><br></div>
<ol>
<li><b>批量生成</b>：将 JSON 直接喂给支持 JSON 输入的绘图 AI（如某些企业级 Midjourney API 封装工具），可一次生成 5 张高保真原型图。</li>
<li><b>低代码平台</b>：将 CSV 导入 Figma 插件或原型工具（如 ProtoPie、Axure 数据填充插件），自动生成带交互标注的线框/高保真。</li>
<li><b>演示准备</b>：生成图片后，可在 PPT/Keynote 中按我们之前设计的“数字讲解员口径”配音，做成可交互的展厅 Demo。</li>
</ol>

---

## 要尽可能地反映原文件内容 要按照原文件P1 P2的内容 针对每一页进行PPT生成 一共要设计出2页的PPT 上下逻辑连贯 严谨 要 

# 要尽可能地反映原文件内容，要按照原文件P1～P2的内容，针对每一页进行PPT生成，一共要设计出2页的PPT，上下逻辑连贯，严谨，要…

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p43 -->

<div><font face=".PingFangUITextSC-Regular">要尽可能地反映原文件内容，要按照原文件</font>P1～P2的内容，针对每一页进行PPT生成，一共要设计出2页的PPT，上下逻辑连贯，严谨，要突出重点，思路清晰，可以尽可能多地表现更多的元素，比如使用丰富的图片，图示，图标，图表，连线，方框和说明等元素，文字为中文，每一页大小为4k, 每一页比例为16:9，要符合中国平安集团的汇报风格，字体均为华文楷体</div>

---

## 这是一个为  平安财服 2025 年终总结报告  量身定制的 PPT 设计方案  要严格按照以下说明进行PPT生成 语言为中文 一般 

# 这是一个为**平安财服 2025 年终总结报告**量身定制的 PPT 设计方案, 要严格按照以下说明进行PPT生成，语言为中文，一般…

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p39 -->

<div><font face=".PingFangUITextSC-Regular">这是一个为</font>**平安财服 2025 年终总结报告**量身定制的 PPT 设计方案, 要严格按照以下说明进行PPT生成，语言为中文，一般为华文楷体，要尽可能反映原文件信息：</div>
<div><br></div>
<div><font face=".PingFangUITextSC-Regular">基于报告的核心逻辑</font>“**从成本中心到价值引擎**”以及“**数智赋能，价值共生**”的主题，设计风格必须兼顾**“金融的严谨性”**与**“科技的未来感”**，同时要传递出文案中强调的**“温度”**（人与服务）与**“硬度”**（数据与成绩）。</div>
<div><br></div>
<div>---</div>
<div><br></div>
<div>### **PPT 设计风格定义：【流光智构 · 价值引擎】风格**</div>
<div>**(Luminous Tech-Structure &amp Value Engine Style)**</div>
<div><br></div>
<div>#### **1. 核心设计关键词**</div>
<div>*   **透视感 (Perspective)：** 用建筑透视或空间纵深，体现“蓝图”和“底层逻辑”。</div>
<div>*   **光束 (Beam)：** 呼应“灯塔”隐喻，用光线穿透迷雾，指引方向。</div>
<div>*   **连接 (Connection)：** 用线条和节点，体现“共生”与“生态”。</div>
<div>*   **极简 (Minimalism)：** 留白得当，突出核心数据，体现“清醒”与“高级”。</div>
<div><br></div>
<div>---</div>
<div><br></div>
<div>### **2. 色彩体系 (Color Palette)**</div>
<div><font face=".PingFangUITextSC-Regular">平安的品牌色是基础，但需要进行</font>“科技化”升维。</div>
<div><br></div>
<div>*   **主色调（背景/底色）：**</div>
<div>    *   **深邃蓝 (Deep Navy):** `#00204A` 或 `#0A192F` —— 用于封面、过渡页、强调页背景。代表专业、深沉的思考。</div>
<div>    *   **纯净白 (Pure White):** `#FFFFFF` —— 用于正文页背景。确保文字阅读清晰，打印友好。</div>
<div><br></div>
<div>*   **辅助色（科技与数据）：**</div>
<div>    *   **平安橙 (Ping An Orange):** `#FF6600` —— **极其重要的点缀色**。用于强调“价值”、“核心数据”、“金句”、“人（温度）”。这是画龙点睛之笔。</div>
<div>    *   **青鸾蓝 (Cyan/Teal):** `#00CED1` 至 `#20B2AA` —— 代表数字化、AI、智能体。用于图表、科技线条。</div>
<div><br></div>
<div>*   **文字色：**</div>
<div>    *   **深灰 (Dark Grey):** `#333333` (正文) / `#000000` (标题)。</div>
<div>    *   **银灰 (Silver Grey):** `#888888` (辅助信息、页码)。</div>
<div><br></div>
<div>---</div>
<div><br></div>
<div>### **3. 字体规范 (Typography)**</div>
<div>*   **中文字体：**</div>
<div>    *   **标题：** `OPPOSans B` 或 `PingFang SC Semibold`（方正兰亭黑亦可）。无衬线，现代，有力。</div>
<div>    *   **正文：** `OPPOSans R` 或 `PingFang SC Regular`。阅读舒适。</div>
<div>    *   **金句/引言：** `思源宋体` 或 `方正清刻本悦宋`。**使用宋体**来表现文案中的“诗意”和“反思感”（如序章和镜鉴篇），形成一种人文与科技的反差美。</div>
<div>*   **英文字体/数字（关键！）：**</div>
<div>    *   **数字/KPI：** `DIN Condensed` 或 `Oswald`。窄体、粗壮、工业感强。让 P2/P4 等页面的数据看起来像仪表盘上的读数，非常硬核。</div>
<div>    *   **英文标题：** `Montserrat` 或 `Roboto`。</div>
<div><br></div>
<div>---</div>
<div><br></div>
<div>### **4. 页面元素详细设计**</div>
<div><br></div>
<div>#### **A. 封面设计 (P1)**</div>
<div>*   **背景：** 深邃蓝底色。画面中央或右侧是一个**抽象的、正在发光的“数字引擎”**或者**“水晶灯塔”**的 3D 渲染图。不要用具体的写实照片，要用抽象几何体构成的发光体。</div>
<div>*   **文字：**</div>
<div>    *   “2025 年年终总结报告”字号较小，居上。</div>
<div>    *   “数智赋能，价值共生”字号极大，使用**渐变色填充**（从青色到白色），甚至可以做一点金属质感。</div>
<div>    *   左下角：平安财服 LOGO。</div>
<div><br></div>
<div>#### **B. 目录页/过渡页 (P1/P9/P15)**</div>
<div>*   **设计：** 采用**“坐标轴”**或**“时间轴”**概念。</div>
<div>*   **元素：** 一条发光的线贯穿屏幕。节点分别为“总结篇”、“不足篇”、“规划篇”。</div>
<div>*   **动效：** 光线从左流动到右，点亮当前的章节标题。当前章节标题放大，其他灰显。</div>
<div><br></div>
<div>#### **C. 正文页布局 (P2-P8, P10-P22)**</div>
<div>*   **版式：** 左侧导航/标题栏（占 1/4），右侧内容区（占 3/4）。或者上下结构（上标题，下内容）。</div>
<div>*   **背景：** 纯白或极浅的灰（`#F5F7FA`）。</div>
<div>*   **容器（卡片化）：** 内容尽量放在圆角矩形的“卡片”中，卡片带有极轻微的阴影，制造悬浮感。</div>
<div><br></div>
<div>#### **D. 核心元素微观设计**</div>
<div>*   **图标 (Icons)：**</div>
<div>    *   风格：**微立体磨砂玻璃风格 (Glassmorphism)** 或 **线性渐变风格**。</div>
<div>    *   颜色：青色线条，橙色点缀。</div>
<div>    *   例如：“黑灯工厂”用一个带光泽的工厂图标；“智能体”用一个带有神经元连接的大脑图标。</div>
<div><br></div>
<div>*   **连线与装饰 (Lines &amp Shapes)：**</div>
<div>    *   不要用实线。使用**虚线**或**渐变透明度的线**，代表数据流。</div>
<div>    *   背景装饰：可以使用极淡的二进制代码（010101）或网格线作为底纹，增加科技细节。</div>
<div><br></div>
<div>*   **金句呈现 (Highlight Quotes)：**</div>
<div>    *   设计一个专门的**“金句框”**。左侧加一个粗壮的橙色竖线作为引用符。</div>
<div>    *   字体使用宋体，字号加大，颜色使用深灰色，背景可以铺一层淡淡的米黄色或灰色色块，体现“文档感”和“思考深度”。</div>
<div><br></div>
<div>*   **图片处理 (Imagery)：**</div>
<div>    *   **去背景处理：** P4“黑灯工厂”或 P21“财智大脑”，如果使用人物或设备图片，建议抠图去底，叠加在科技背景上，避免生硬的矩形图片。</div>
<div>    *   **遮罩：** 如果必须用矩形照片，加上一个**“对角切角”**的设计，或者加上半透明的青色蒙层，统一色调。</div>
<div><br></div>
<div>#### **E. 数据图表设计 (Charts)**</div>
<div>*   **柱状图/折线图：**</div>
<div>    *   去网格线，只留坐标轴。</div>
<div>    *   数据点（KPI 结果）使用**发光的橙色圆点**。</div>
<div>    *   “超额完成”的部分，用特殊的纹理填充或高亮显示。</div>
<div>*   **表格（P2 考核成绩单）：**</div>
<div>    *   不要用默认的三线表。</div>
<div>    *   表头：深蓝色底，白字。</div>
<div>    *   行：斑马纹（白色/浅灰交替）。</div>
<div>    *   关键数字（如 120%）：加粗，橙色，字号放大。</div>
<div><br></div>
<div>---</div>
<div><br></div>
<div>### **5. 针对具体页面的设计脑洞**</div>
<div><br></div>
<div>*   **P4 费用黑灯工厂：**</div>
<div>    *   **视觉隐喻：** **漏斗 + 传送带**。左边是杂乱的单据（图标），经过中间的“黑盒”（发光的 AI 芯片），右边输出整齐的金币（价值）和数据流。</div>
<div>    *   **配色：** 黑色背景，荧光绿/青色线条勾勒机器轮廓，体现“黑灯”概念。</div>
<div><br></div>
<div>*   **P9 镜鉴（不足篇）：**</div>
<div>    *   **视觉隐喻：** **镜子/冰山**。画面可以分割，上面是光鲜的成绩（彩色），下面是隐患（黑白/线稿）。或者用一面破碎/有裂痕的镜子，体现“清醒”和“痛感”。</div>
<div>    *   **氛围：** 稍微压暗，严肃冷峻。</div>
<div><br></div>
<div>*   **P16 战略全景图：**</div>
<div>    *   **视觉隐喻：** **阶梯/登山路径**。2026-2027-2028 是三个台阶。背景是星空（星辰大海）。</div>
<div>    *   **元素：** 每一个台阶上不仅有文字，还要有一个具象的图标（如：齿轮 -&gt 芯片 -&gt 生态球）。</div>
<div><br></div>
<div>*   **P22 队伍（换新/焕新/唤醒）：**</div>
<div>    *   **视觉隐喻：** **DNA 螺旋结构**。三条链缠绕上升，分别代表换新、焕新、唤醒。或者用**电池充电**的图标，显示电量从红色（低）变为绿色（满格）。</div>
<div><br></div>
<div>---</div>
<div><br></div>
<div>### **6. 给 AI 绘图工具的提示词建议**</div>
<div><font face=".PingFangUITextSC-Regular">如果您需要生成背景图或配图，可以使用类似以下的提示词：</font><br></div>
<div><br></div>
<div>*   *Abstract financial technology background, deep navy blue and orange theme, smooth data flow lines, glowing geometric structures, futuristic, professional, minimalistic, 8k resolution, corporate style --ar 16:9*</div>
<div>    (抽象金融科技背景，深海军蓝和橙色主题，流畅的数据流线条，发光的几何结构，未来感，专业，极简，8k分辨率，商务风格)</div>
<div><br></div>
<div>*   *Close up of a futuristic glass lighthouse emitting a beam of light through fog, conceptual value finding, cyan and orange lighting, dark background, 3d render --ar 16:9*</div>
<div>    (未来主义玻璃灯塔特写，在雾中射出一束光，概念性的价值发现，青色和橙色灯光，深色背景，3D渲染)</div>
<div><br></div>
<div>### **总结建议**</div>
<div><font face=".PingFangUITextSC-Regular">这套设计的核心在于</font>**“反差”**：</div>
<div>1.  **数据的冷（科技蓝）** vs **服务的热（平安橙）**。</div>
<div>2.  **封面的酷炫（深色）** vs **内容的清爽（浅色）**。</div>
<div>3.  **标题的硬朗（黑体）** vs **金句的优雅（宋体）**。</div>
<div><br></div>
<div><font face=".PingFangUITextSC-Regular">这种风格能完美承接您文字稿中</font>“有硬度、有温度”的汇报基调。</div>

---

## 针对财务领域语言的架构图的细节进行补充 要去如下 

# 针对财务领域语言的架构图的细节进行补充，要去如下：

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p45 -->

<div>针对财务领域语言的架构图的细节进行补充，要去如下：</div>
<div>1.整体风格：简洁明了，加入财务语言，容易让专业财务人员理解</div>
<div>2.内容：内容上要循序渐进，不需要用过于复杂的元素设计，但内容上元素一定要丰富，包括图片、图标、连线、形状等元素，设计上保持一致的风格，可以参考咨询公司的PPT风格。对于架构中，缺失的可以进一步补充内容</div>
<div>3.逻辑： 每页的Slide前后要有逻辑性，要有前因后果，大到方案设计，小到落地实现</div>
<div>4.页数要足够多</div>

---

