---
title: "vectors_mgt 向量管理模块"
type: module
created: 2026-05-03
last_updated: 2026-05-03
source_count: 2
confidence: medium
status: active
tags:
  - vectors_mgt
  - 向量数据库
  - RAG
  - 检索
  - 嵌入
sources:
  - vectors_mgt模块代码分析
  - README.md
---

# vectors_mgt 向量管理模块

## 模块概述
vectors_mgt是DSC Platform的核心向量处理引擎，提供从文档分块、向量嵌入、存储到智能检索的全链路功能，是RAG（检索增强生成）系统的核心组件。该模块支持多种分块策略、多向量数据库、多嵌入模型，提供高性能的语义检索能力，为AI应用提供准确的上下文信息支撑。

## 模块架构
vectors_mgt采用分层设计，各层职责明确，易于扩展：

```
┌─────────────────────────────────────────────────────┐
│                  API 接口层                          │
│  RESTful API / Python SDK / 第三方集成               │
├─────────────────────────────────────────────────────┤
│                  服务层                              │
│  分块服务 / 嵌入服务 / 检索服务 / 管理服务            │
├─────────────────────────────────────────────────────┤
│                  引擎层                              │
│  分块引擎 / 嵌入引擎 / 检索引擎 / 重排序引擎          │
├─────────────────────────────────────────────────────┤
│                  存储适配层                          │
│  Weaviate / Milvus / Chroma / PGVector / 自定义存储   │
└─────────────────────────────────────────────────────┘
```

## 核心组件

### 1. 文档分块器 (KnowledgeChunking)
负责将长文档拆分为适合向量检索和LLM处理的文本块，支持多种智能分块策略。

#### 支持的分块模式
```python
class ChunkingMode(Enum):
    FIXED_SIZE = "fixed_size"        # 固定大小分块
    SENTENCE = "sentence"            # 句子级分块
    PARAGRAPH = "paragraph"          # 段落级分块
    RECURSIVE = "recursive"          # 递归分块（推荐）
    TOKEN = "token"                  # Token级分块（适配LLM）
    SEMANTIC = "semantic"            # 语义分块（基于相似度）
    MARKDOWN = "markdown"            # Markdown结构化分块
    CUSTOM = "custom"                # 自定义分块规则
```

#### 分块特性
- **智能边界识别**：自动识别句子、段落、标题等语义边界
- **重叠配置**：支持相邻块之间的重叠，避免上下文丢失
- **长短自适应**：自动合并过短片段，拆分过长片段
- **元数据保留**：分块过程中保留原文档的元数据信息
- **格式感知**：针对Markdown、HTML等结构化文档优化分块策略

#### 使用示例
```python
from vectors_mgt import KnowledgeChunking, ChunkingMode

chunker = KnowledgeChunking(dataset_id="my_dataset")
chunks = await chunker.chunk_document(
    document_path="document.pdf",
    mode=ChunkingMode.RECURSIVE,
    chunk_size=500,
    overlap_size=50,
    min_chunk_size=50,
    remove_extra_spaces=True
)
```

### 2. 向量嵌入器 (KnowledgeEmbedding)
负责将文本块转换为向量表示并存储到向量数据库。

#### 支持的嵌入模型
| 模型类型 | 支持模型 | 向量维度 |
|---------|---------|---------|
| OpenAI | text-embedding-ada-002, text-embedding-3-small, text-embedding-3-large | 1536/3072 |
| 百度千问 | text-embedding-v1, text-embedding-v2 | 1536 |
| 智谱AI | embedding-2 | 1024 |
| 本地模型 | BGE-zh, BGE-m3, m3e, text2vec | 768/1024 |
| Ollama | 所有支持embedding的Ollama模型 | 自定义 |
| 自定义 | 支持通过接口集成自定义嵌入服务 | 自定义 |

#### 核心功能
- **批量处理**：支持大规模文档的批量向量化
- **增量更新**：支持文档修改后的增量更新
- **错误重试**：自动重试失败的嵌入请求
- **进度跟踪**：实时查看向量化进度
- **版本管理**：支持嵌入模型的版本切换和数据迁移

#### 使用示例
```python
from vectors_mgt import KnowledgeEmbedding

embedder = KnowledgeEmbedding(dataset_id="my_dataset")
result = await embedder.embed_document(
    document_path="document.pdf",
    document_id="doc_001",
    chunking_mode=ChunkingMode.RECURSIVE,
    chunk_size=500,
    metadata={"source": "manual", "category": "tech", "version": "1.0"}
)
print(f"成功插入 {result['chunks_inserted']} 个向量块")
```

### 3. 检索引擎 (KnowledgeRetrieval)
负责提供高效准确的向量检索能力，支持多种检索模式和优化策略。

#### 支持的检索模式
```python
class SearchMode(Enum):
    VECTOR = "vector"                # 纯向量相似度检索
    KEYWORD = "keyword"              # BM25关键词检索
    HYBRID = "hybrid"                # 混合检索（推荐）
    SEMANTIC = "semantic"            # 语义检索（带重排序）
    MULTI_QUERY = "multi_query"      # 多查询合并检索
```

#### 检索特性
- **混合检索**：结合向量语义和关键词匹配的优势，提高召回率
- **元数据过滤**：支持复杂的条件过滤，如按文档类型、时间范围等
- **结果重排序**：支持MMR、交叉编码器、自定义重排序策略
- **上下文扩展**：自动获取检索结果的相邻上下文块
- **多租户隔离**：不同数据集之间的数据完全隔离
- **相似度阈值**：支持配置最小相似度阈值，过滤低相关结果

#### 高级检索功能
```python
from vectors_mgt import KnowledgeRetrieval, SearchMode

retriever = KnowledgeRetrieval(dataset_id="my_dataset")
results = await retriever.search(
    query="如何优化向量检索性能？",
    mode=SearchMode.HYBRID,
    limit=10,
    alpha=0.7,  # 向量检索权重，0.5表示关键词和向量各占一半
    filters={
        "category": "tech",
        "version": {"$gte": "1.0"}
    },
    rerank=True,  # 启用结果重排序
    expand_context=True  # 扩展上下文
)

for result in results:
    print(f"相似度: {result['score']:.4f}")
    print(f"内容: {result['content']}")
    print(f"来源: {result['metadata']['source']}")
```

### 4. 基础操作层 (KnowledgeVectorsBasic)
提供向量数据库的基础操作封装，屏蔽底层数据库差异。

#### 支持的向量数据库
- **Weaviate**：官方推荐，支持混合检索、过滤、多租户
- **Milvus**：高性能开源向量数据库，适合大规模场景
- **Chroma**：轻量级向量数据库，适合开发和小规模场景
- **PGVector**：PostgreSQL扩展，适合关系型数据库一体化场景
- **Elasticsearch**：支持向量+全文检索一体化

#### 核心功能
- 集合（Collection）的创建、删除、管理
- 向量的增删改查操作
- 批量数据导入导出
- Schema管理和迁移
- 性能监控和统计

## API接口

### 向量管理接口
| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/vectors/datasets` | GET | 获取向量数据集列表 |
| `/api/vectors/datasets` | POST | 创建向量数据集 |
| `/api/vectors/datasets/{dataset_id}` | DELETE | 删除向量数据集 |
| `/api/vectors/datasets/{dataset_id}/stats` | GET | 获取数据集统计信息 |

### 文档向量化接口
| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/vectors/embed/document` | POST | 向量化单个文档 |
| `/api/vectors/embed/batch` | POST | 批量向量化文档 |
| `/api/vectors/embed/status/{task_id}` | GET | 查询向量化任务状态 |
| `/api/vectors/documents/{doc_id}` | DELETE | 删除文档的向量数据 |

### 检索接口
| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/vectors/search` | POST | 向量检索 |
| `/api/vectors/hybrid_search` | POST | 混合检索 |
| `/api/vectors/keyword_search` | POST | 关键词检索 |
| `/api/vectors/multi_query_search` | POST | 多查询检索 |

## 核心特性

### 1. 高性能设计
- **异步架构**：全异步实现，支持高并发请求
- **批量处理**：支持大批量向量的并行处理
- **索引优化**：自动优化向量索引结构，提高检索速度
- **缓存机制**：对高频查询结果进行缓存，降低响应时间

### 2. 多租户支持
- **数据隔离**：不同数据集之间的数据完全隔离
- **资源配额**：支持按租户配置资源使用配额
- **权限控制**：细粒度的数据集访问权限控制
- **独立Schema**：每个数据集可以有独立的元数据Schema

### 3. 可扩展性
- **插件化设计**：支持自定义嵌入模型、分块策略、检索算法
- **存储抽象**：统一的存储接口，方便扩展支持新的向量数据库
- **中间件支持**：支持在处理流程中插入自定义中间件
- **事件机制**：支持通过事件回调扩展处理逻辑

### 4. 可靠性保障
- **错误重试**：自动重试失败的操作，提高成功率
- **幂等设计**：所有接口支持幂等调用，避免重复处理
- **数据一致性**：确保元数据和向量数据的一致性
- **备份恢复**：支持数据集的备份和恢复功能

## 开发指南

### 自定义分块策略
```python
from vectors_mgt import BaseChunker, register_chunker

@register_chunker("custom_chunking")
class CustomChunker(BaseChunker):
    """自定义分块策略"""
    
    async def chunk_text(self, text: str, **kwargs) -> List[Dict]:
        """实现自定义分块逻辑"""
        chunks = []
        # 自定义分块逻辑
        chunk_size = kwargs.get("chunk_size", 500)
        
        # 实现具体的分块算法
        current_pos = 0
        text_length = len(text)
        
        while current_pos < text_length:
            end_pos = min(current_pos + chunk_size, text_length)
            # 智能调整边界
            end_pos = self._adjust_boundary(text, current_pos, end_pos)
            
            chunk_text = text[current_pos:end_pos].strip()
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "start_index": current_pos,
                    "end_index": end_pos
                })
            
            current_pos = end_pos - kwargs.get("overlap_size", 0)
        
        return chunks
    
    def _adjust_boundary(self, text: str, start: int, end: int) -> int:
        """调整分块边界到语义分割点"""
        # 找到最近的句子结尾
        separators = [".", "。", "!", "！", "?", "？", "\n\n"]
        for sep in separators:
            pos = text.rfind(sep, start, end)
            if pos != -1 and pos > start + 100:  # 确保块不会太短
                return pos + len(sep)
        return end
```

### 自定义嵌入模型
```python
from vectors_mgt import BaseEmbedding, register_embedding

@register_embedding("custom_embedding")
class CustomEmbedding(BaseEmbedding):
    """自定义嵌入模型"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.endpoint = config.get("endpoint", "https://api.custom.com/embeddings")
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量"""
        # 调用自定义嵌入服务API
        response = await self._async_http_post(
            url=self.endpoint,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"input": texts, "model": self.model_name}
        )
        
        # 处理返回结果
        embeddings = [item["embedding"] for item in response["data"]]
        return embeddings
    
    def get_dimension(self) -> int:
        """返回向量维度"""
        return 1024
```

### 自定义检索后处理
```python
from vectors_mgt import register_post_process_hook

@register_post_process_hook("custom_rerank")
async def custom_rerank(results: List[Dict], query: str, context: Dict) -> List[Dict]:
    """自定义结果重排序逻辑"""
    # 实现自定义的重排序算法
    for result in results:
        # 计算自定义评分
        custom_score = calculate_custom_score(result, query)
        result["custom_score"] = custom_score
    
    # 按自定义评分重新排序
    results.sort(key=lambda x: x["custom_score"], reverse=True)
    
    return results
```

## 性能指标

### 处理性能
- 单实例支持1000+ QPS的检索请求
- 向量化处理速度：5000+ 字符/秒（取决于嵌入模型）
- 支持亿级向量的毫秒级检索

### 检索效果
- 支持Top1准确率>85%，Top3准确率>95%
- 混合检索相比纯向量检索召回率提升20%+
- 重排序策略可以进一步提升准确率10%+

## 最佳实践

### 分块策略选择
1. **通用场景**：推荐使用递归分块（RECURSIVE），chunk_size=500-1000，overlap=10%-20%
2. **LLM对话场景**：推荐使用Token分块（TOKEN），chunk_size适配模型上下文窗口
3. **结构化文档**：推荐使用Markdown分块（MARKDOWN），保留文档结构
4. **知识库场景**：推荐使用语义分块（SEMANTIC），提高检索相关性

### 嵌入模型选择
1. **中文场景**：优先选择中文训练的模型，如BGE-zh、m3e、千问嵌入
2. **通用场景**：OpenAI ada-002或text-embedding-3-small是不错的选择
3. **私有化部署**：推荐使用BGE系列开源模型，效果好，部署简单
4. **多模态场景**：选择支持多模态的嵌入模型，如BGE-m3

### 检索优化
1. **混合检索**：优先使用HYBRID模式，alpha值建议0.5-0.7
2. **重排序**：对检索结果要求高的场景，建议启用重排序
3. **元数据过滤**：尽可能使用元数据过滤减少检索范围
4. **上下文扩展**：RAG场景建议启用上下文扩展，提供更完整的上下文信息

## 常见问题

### Q: 支持多大规模的向量数据？
A: 理论上支持无限规模，取决于底层向量数据库的部署方式。分布式部署可以支持千亿级向量。

### Q: 如何选择合适的向量数据库？
A: - 开发测试：Chroma简单易用
   - 中小规模：Weaviate功能全面，混合检索能力强
   - 大规模：Milvus性能更好，生态完善
   - 已有PG数据库：PGVector一体化部署方便

### Q: 向量维度越高越好吗？
A: 不是。更高的维度通常带来更高的准确率，但会增加存储成本和检索延迟。需要在准确率和性能之间做平衡，通常768-1536维是比较好的选择。

### Q: 如何处理文档更新？
A: 系统支持增量更新，当文档内容修改时，会自动删除旧的向量并插入新的向量，无需重新处理整个知识库。

### Q: 支持跨数据集检索吗？
A: 支持，可以通过配置跨数据集检索权限，实现多个知识库的联合检索。
