---
title: "RAG 检索增强生成"
type: concept
created: 2026-04-30
last_updated: 2026-04-30
source_count: 3
confidence: medium
status: active
tags:
  - RAG
  - 检索增强生成
  - AI
  - 知识检索
sources:
  - intelligent-customer-service-rag
  - intelligent-research-assistant
  - enterprise-kb-comprehensive-report
---

RAG（Retrieval-Augmented Generation，检索增强生成）是一种将知识检索与LLM生成能力结合的技术架构[^src-intelligent-customer-service-rag]。

## 核心技术流程

基于智能客服RAG工作流的实现[^src-intelligent-customer-service-rag]：

1. **用户提问**：接收自然语言问题
2. **意图解析**：NLU解析问题意图与关键词
3. **问题向量化**：使用text-embedding-3-large将问题转换为语义向量
4. **知识检索**：基于Pinecone向量库的Top-K相似度检索
5. **精排重排**：使用bge-reranker-large Cross-Encoder精排
6. **置信度判断**：相关性分数阈值≥0.7
7. **答案生成**：GPT-4o结合上下文生成答案（temperature=0.3）
8. **结果返回**：返回答案+参考来源

## 工作流中的Agent模式

[[智能研究助手多步推理]]展示了更复杂的Agent RAG模式[^src-intelligent-research-assistant]：

- **多步推理**：任务分解→历史记忆检索→资料搜索→数据分析→信息充分判断→质量反思→生成报告
- **工具调用**：Bing Search + Google Scholar + ArXiv + Python代码执行
- **递归搜索**：信息不足时自动继续搜索

## 在平安金服的应用

RAG技术广泛应用于智能客服、知识库问答等场景，是平安金服知识库建设的核心技术支撑[^src-enterprise-kb-comprehensive-report]。

## 关联文档

- [[智能客服-rag-知识问答]] - RAG工作流定义
- [[智能研究助手多步推理]] - Agent RAG模式
- [[智能客服 RAG 知识问答]] - 原始工作流文件

[^src-intelligent-customer-service-rag]: [[智能客服-rag-知识问答]]
[^src-intelligent-research-assistant]: [[智能研究助手多步推理]]
[^src-enterprise-kb-comprehensive-report]: [[企业知识库建设综合分析报告]]

