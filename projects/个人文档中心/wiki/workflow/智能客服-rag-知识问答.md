---
title: "智能客服 RAG 知识问答"
type: source-summary
created: 2026-04-30
last_updated: 2026-04-30
source_count: 1
confidence: medium
status: active
tags:
  - workflow
  - 知识
  - RAG
  - 客服
  - AI
sources:
  - intelligent-customer-service-rag
---

---
title: "智能客服 RAG 知识问答"
type: source-summary
tags:
  - workflow
  - 知识
  - RAG
  - 客服
  - AI
created: 2026-04-29
last_updated: 2026-04-29
source_count: 1
confidence: high
status: active
---

# 智能客服 RAG 知识问答

[[source-intelligent-customer-service-rag|智能客服 RAG 知识问答]] 版本 v1.0，属于知识类型（knowledge）工作流，定义了基于检索增强生成（RAG）的企业客服知识库问答流程。[^src-intelligent-customer-service-rag]

## 流程概述

该流程实现了从用户提问到答案返回的完整RAG链路：

1. **用户提问**：接收用户自然语言问题作为输入。[^src-intelligent-customer-service-rag]
2. **意图解析**：使用NLU解析问题意图与关键词，采用 text-embedding-ada-002 嵌入模型。[^src-intelligent-customer-service-rag]
3. **问题向量化**：将问题转换为语义向量，使用 text-embedding-3-large 嵌入模型。[^src-intelligent-customer-service-rag]
4. **知识检索**：通过 Pinecone 向量数据库进行 Top-K 相似度检索，Top-5 Recall@0.85。[^src-intelligent-customer-service-rag]
5. **精排重排**：使用 Cross-Encoder（bge-reranker-large）对检索结果进行精排重排。[^src-intelligent-customer-service-rag]
6. **置信度判断**：判断相关性分数是否达到阈值（置信度≥0.7则进入答案生成，否则返回重新检索）。[^src-intelligent-customer-service-rag]
7. **答案生成**：使用 GPT-4o 模型（temperature=0.3）结合检索到的上下文生成答案。[^src-intelligent-customer-service-rag]
8. **结果返回**：返回答案及参考来源，完成流程。[^src-intelligent-customer-service-rag]

## 技术架构

- **向量数据库**：Pinecone，用于存储和检索知识向量
- **嵌入模型**：text-embedding-ada-002（意图解析阶段）、text-embedding-3-large（向量化阶段）
- **重排模型**：bge-reranker-large（Cross-Encoder架构）
- **生成模型**：GPT-4o，temperature设置为0.3以保证回答稳定性

## 关键特征

- 支持置信度阈值判断，低于阈值时自动触发重新检索循环
- 采用两阶段检索策略：粗排（Top-K相似度）+ 精排（Cross-Encoder），提升检索准确性
- 返回答案时附带参考来源，增强可信度和可追溯性

[^src-intelligent-customer-service-rag]: [[source-intelligent-customer-service-rag]]

