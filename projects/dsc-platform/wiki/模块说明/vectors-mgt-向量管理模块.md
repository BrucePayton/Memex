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
┌─────────────────────────────────────────────────────────┐
│                  API接口层                               │
│  管理接口 / 检索接口 / 处理接口                          │
├─────────────────────────────────────────────────────────┤
│                  服务编排层                               │
│  分块服务 / 嵌入服务 / 检索服务 / 管理服务                │
├─────────────────────────────────────────────────────────┤
│                  核心引擎层                               │
│  分块引擎 / 嵌入引擎 / 检索引擎 / 重排序引擎              │
├─────────────────────────────────────────────────────────┤
│                  存储适配层                               │
│  Weaviate / Milvus / Chroma / PGVector / 自定义存储       │
└─────────────────────────────────────────────────────────┘
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
- **智能边界识别**：自动识别句子、段落、标题等语义边界，避免上下文断裂
- **重叠配置**：支持相邻块之间的重叠（建议10%-20%），避免信息丢失
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

### 2. 嵌入生成器 (KnowledgeEmbedding)
负责将文本块转换为向量表示，支持多种嵌入模型和部署方式。

#### 支持的嵌入模型
| 模型提供商 | 支持模型 | 向量维度 | 适用场景 |
|---------|---------|---------|---------|
| OpenAI | text-embedding-ada-002、text-embedding-3-small、text-embedding-3-large | 1536/3072 | 通用场景、英文为主 |
| 百度千问 | text-embedding-v1、text-embedding-v2 | 1536 | 中文场景 |
| 智谱AI | embedding-2 | 1024 | 中文场景 |
| 百川 | baichuan-text-embedding | 1024 | 中文场景 |
| 开源模型 | BGE-zh、BGE-m3、M3E、text2vec | 768/1024 | 私有化部署、中文场景 |
| Ollama | 所有支持embedding的Ollama模型 | 自定义 | 本地化部署 |
| 自定义 | 支持通过接口集成自定义嵌入服务 | 自定义 | 特殊场景 |

#### 核心功能
- **批量处理**：支持大规模文档的批量向量化，自动分片和错误重试
- **增量更新**：支持文档修改后的增量向量化，避免全量重新计算
- **版本管理**：支持嵌入模型的版本切换和数据迁移
- **异步处理**：大文档向量化采用异步任务，避免阻塞请求
- **缓存机制**：对重复文本的嵌入结果进行缓存，提高处理效率

#### 使用示例
```python
from vectors_mgt import KnowledgeEmbedding

embedder = KnowledgeEmbedding(dataset_id="my_dataset")
result = await embedder.embed_document(
    document_path="document.pdf",
    document_id="doc_001",
    chunking_mode=ChunkingMode.RECURSIVE,
    chunk_size=500,
    metadata={"source": "manual", "category": "tech"}
)
print(f"成功插入 {result['chunks_inserted']} 个向量块")
```

### 3. 向量存储 (VectorStore)
负责向量的持久化存储和索引管理，支持多种向量数据库。

#### 支持的向量数据库
| 数据库 | 特点 | 适用场景 |
|---------|---------|---------|
| Weaviate | 支持混合检索、内置过滤、多租户 | 中小规模、功能需求丰富 |
| Milvus | 高性能、分布式、支持百亿级向量 | 大规模生产环境 |
| Chroma | 轻量级、部署简单、Python友好 | 开发测试、小规模应用 |
| PGVector | PostgreSQL扩展、支持关系型数据 + 向量 | 已有PG数据库的场景 |
| Elasticsearch | 支持全文检索 + 向量检索一体化 | 已有ES栈的场景 |

#### 核心功能
- **统一抽象**：所有向量数据库实现统一接口，切换成本低
- **索引管理**：支持索引的创建、更新、删除和优化
- **批量操作**：支持向量的批量插入、更新和删除
- **元数据过滤**：支持基于元数据的条件过滤检索
- **分布式部署**：支持集群模式，水平扩展存储和检索能力

### 4. 检索引擎 (KnowledgeRetrieval)
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
- **混合检索**：结合向量语义和关键词匹配的优势，通过alpha参数调节权重（建议0.5-0.7），综合提高召回率和准确率
- **元数据过滤**：支持复杂的条件过滤，如按文档类型、上传时间、作者、标签等进行过滤
- **结果重排序**：支持MMR（最大边际相关性）、交叉编码器、自定义重排序策略
- **上下文检索**：自动获取相邻文本块，提供更完整的上下文信息
- **多查询检索**：支持同时传入多个查询，合并检索结果，提高召回率
- **多租户隔离**：不同数据集之间的数据完全隔离，权限控制到数据集级别
- **相似度阈值**：支持配置最小相似度阈值，过滤低相关结果

#### 检索优化
- **查询重写**：自动优化用户查询，提高检索准确性
- **HyDE（假设文档嵌入）**：先让大模型生成假设的相关文档，再进行检索
- **查询扩展**：基于同义词、相关词扩展查询
- **缓存机制**：对高频查询结果进行缓存，降低响应时间

#### 使用示例
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

### 5. 重排序器 (Reranker)
负责对初次检索结果进行二次排序，进一步提高相关性。

#### 支持的重排序策略
- **MMR（最大边际相关性）**：平衡相关性和多样性，避免结果过于相似
- **交叉编码器（CrossEncoder）**：基于预训练模型计算查询和结果的相似度，准确率高但速度较慢
- **规则重排序**：基于业务规则进行自定义排序，如按时间、优先级等
- **自定义重排序**：支持通过Python代码实现自定义排序逻辑

## API接口

### 向量数据集管理接口
| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/vectors/datasets` | GET | 获取向量数据集列表 |
| `/api/vectors/datasets` | POST | 创建向量数据集 |
| `/api/vectors/datasets/{dataset_id}` | DELETE | 删除向量数据集 |
| `/api/vectors/datasets/{dataset_id}/stats` | GET | 获取数据集统计信息（向量数量、占用空间等） |

### 向量处理接口
| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/vectors/embed/document` | POST | 向量化单个文档 |
| `/api/vectors/embed/batch` | POST | 批量向量化文档 |
| `/api/vectors/embed/status/{task_id}` | GET | 查询向量化任务状态 |
| `/api/vectors/documents/{doc_id}` | DELETE | 删除文档的向量数据 |
| `/api/vectors/cleanup` | POST | 清理无效/过期的向量数据 |

### 检索接口
| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/vectors/search` | POST | 向量检索 |
| `/api/vectors/hybrid_search` | POST | 混合检索 |
| `/api/vectors/keyword_search` | POST | 关键词检索 |
| `/api/vectors/multi_query_search` | POST | 多查询合并检索 |

## 核心特性

### 1. 高性能设计
- **异步架构**：全异步实现，支持高并发请求
- **批量处理**：支持大批量向量的并行生成和导入
- **索引优化**：自动优化向量索引结构，提高检索速度
- **分布式部署**：支持水平扩展，应对大规模数据和高并发请求

### 2. 多租户支持
- **数据隔离**：不同数据集之间的数据完全隔离，互不影响
- **资源配额**：支持按租户配置资源使用配额（向量数量、请求频率等）
- **独立配置**：每个数据集可以独立配置嵌入模型、分块策略、检索参数等
- **权限控制**：细粒度的数据集访问权限控制

### 3. 可扩展性
- **插件化设计**：支持自定义嵌入模型、分块策略、检索算法、重排序器
- **存储抽象**：统一的存储接口，方便扩展支持新的向量数据库
- **中间件支持**：支持在处理流程中插入自定义中间件（如内容审核、敏感词过滤等）
- **事件机制**：支持通过事件回调扩展处理逻辑（如向量化完成通知、检索事件审计等）

### 4. 可靠性保障
- **错误重试**：自动重试失败的嵌入请求和数据库操作
- **幂等设计**：所有接口支持幂等调用，避免重复处理和数据不一致
- **数据一致性**：确保元数据和向量数据的强一致性，通过事务和补偿机制保证
- **备份恢复**：支持数据集的备份和恢复功能，防止数据丢失

## 开发指南

### 自定义嵌入模型扩展
```python
from vectors_mgt.knowledge_vectors_basic import BaseEmbedding
from vectors_mgt.vector_config import VectorConfig

class CustomEmbeddingProvider(BaseEmbedding):
    """自定义嵌入模型提供商"""
    
    def __init__(self, config: VectorConfig):
        super().__init__(config)
        self.api_key = config.embedding_api_key
        self.api_endpoint = config.embedding_api_endpoint or "https://api.custom.com/embeddings"
        self.model_name = config.embedding_model or "custom-embedding-v1"
        self.dimension = config.embedding_dimension or 1024
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量"""
        # 实现调用自定义嵌入服务的逻辑
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "input": texts,
            "encoding_format": "float"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                # 提取向量结果
                embeddings = [item["embedding"] for item in result["data"]]
                return embeddings
    
    async def embed_query(self, query: str) -> List[float]:
        """生成查询向量（有些模型对查询有特殊处理）"""
        return (await self.embed_texts([query]))[0]
    
    def get_dimension(self) -> int:
        """返回向量维度"""
        return self.dimension
```

#### 注册提供商
在`vectors_mgt/knowledge_embedding.py`中注册：
```python
from vectors_mgt.embedding_providers.custom_provider import CustomEmbeddingProvider

EMBEDDING_PROVIDERS = {
    # 已有提供商...
    "custom": CustomEmbeddingProvider
}
```

#### 配置使用
在环境变量中配置：
```env
EMBEDDING_PROVIDER=custom
EMBEDDING_API_KEY=your-api-key
EMBEDDING_API_ENDPOINT=https://api.custom.com/embeddings
EMBEDDING_MODEL=custom-embedding-v1
EMBEDDING_DIMENSION=1024
```

### 自定义分块策略
```python
from vectors_mgt.chunkers.base_chunker import BaseChunker, register_chunker

@register_chunker("custom_chunking")
class CustomChunker(BaseChunker):
    """自定义分块策略"""
    
    async def chunk_text(self, text: str, **kwargs) -> List[Dict]:
        """实现自定义分块逻辑"""
        chunks = []
        chunk_size = kwargs.get("chunk_size", 500)
        overlap_size = kwargs.get("overlap_size", 50)
        
        # 实现具体的分块算法
        current_pos = 0
        text_length = len(text)
        
        while current_pos < text_length:
            end_pos = min(current_pos + chunk_size, text_length)
            # 智能调整边界到最近的句子结束位置
            end_pos = self._adjust_boundary(text, current_pos, end_pos)
            
            chunk_text = text[current_pos:end_pos].strip()
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "start_index": current_pos,
                    "end_index": end_pos
                })
            
            current_pos = end_pos - overlap_size
        
        return chunks
    
    def _adjust_boundary(self, text: str, start: int, end: int) -> int:
        """调整分块边界到语义分割点（句子结束、段落结束等）"""
        separators = ["。", "！", "？", "\n\n", ".", "!", "?"]
        for sep in separators:
            pos = text.rfind(sep, start, end)
            if pos != -1 and pos > start + 100:  # 确保块不会太短
                return pos + len(sep)
        return end
```

### 自定义重排序器
```python
from vectors_mgt.rerankers.base_reranker import BaseReranker, register_reranker

@register_reranker("custom_reranker")
class CustomReranker(BaseReranker):
    """自定义重排序器"""
    
    async def rerank(self, query: str, chunks: List[Dict], **kwargs) -> List[Dict]:
        """对检索结果进行重排序"""
        # 实现自定义排序逻辑
        for chunk in chunks:
            # 计算自定义得分（示例：结合相似度、时间权重、业务优先级）
            time_weight = self._calculate_time_weight(chunk["metadata"].get("update_time"))
            priority_weight = chunk["metadata"].get("priority", 1.0)
            chunk["custom_score"] = chunk["score"] * 0.6 + time_weight * 0.3 + priority_weight * 0.1
        
        # 按自定义得分降序排序
        chunks.sort(key=lambda x: x["custom_score"], reverse=True)
        return chunks
    
    def _calculate_time_weight(self, update_time: Optional[datetime]) -> float:
        """计算时间权重，越新的文档权重越高"""
        if not update_time:
            return 1.0
        days_diff = (datetime.now() - update_time).days
        if days_diff < 7:
            return 1.2
        elif days_diff < 30:
            return 1.0
        elif days_diff < 180:
            return 0.8
        else:
            return 0.6
```

## 性能指标

### 处理性能
- 单实例支持1000+ QPS的检索请求
- 向量化处理速度：5000+ 字符/秒（取决于嵌入模型）
- 支持百亿级向量的毫秒级检索

### 检索效果
- 支持Top1准确率>85%，Top3准确率>95%
- 混合检索相比纯向量检索召回率提升20%+
- 重排序策略可以进一步提升准确率10%+

## 最佳实践

### 分块策略选择
1. **通用场景**：推荐使用递归分块（RECURSIVE），chunk_size=500-1000，overlap=10%-20%
2. **LLM对话场景**：推荐使用Token分块（TOKEN），chunk_size适配模型上下文窗口（如ChatGPT 3.5建议512-1024 Token）
3. **结构化文档（Markdown/HTML）**：推荐使用Markdown分块（MARKDOWN），保留文档结构
4. **知识库场景**：推荐使用语义分块（SEMANTIC），提高检索相关性，适合内容关联性强的文档

### 嵌入模型选择
1. **中文场景**：优先选择中文训练的模型，如BGE-zh、M3E、千问嵌入，效果优于通用模型
2. **英文场景**：OpenAI ada-002或text-embedding-3-small是不错的选择，性价比高
3. **私有化部署**：推荐使用BGE系列开源模型，效果好，部署简单，支持CPU/GPU运行
4. **多模态场景**：选择支持多模态的嵌入模型，如BGE-m3，支持文本、图片等多模态检索

### 检索优化
1. **混合检索**：优先使用HYBRID模式，alpha值建议0.5-0.7，根据业务场景调整：更注重语义匹配调大alpha，更注重关键词匹配调小alpha
2. **重排序**：对检索结果要求高的场景，建议启用交叉编码器重排序，虽然会增加延迟，但准确率提升明显
3. **元数据过滤**：尽可能使用元数据过滤减少检索范围，提高检索速度和准确率
4. **上下文扩展**：RAG场景建议启用上下文扩展，将相邻的文本块一起返回给大模型，提供更完整的上下文信息

### 部署优化
1. **小规模场景（<100万向量）**：推荐使用Weaviate或Chroma，部署简单，功能足够
2. **大规模场景（>100万向量）**：推荐使用Milvus分布式部署，性能更高，扩展性更好
3. **已有PG数据库场景**：优先使用PGVector，减少技术栈复杂度，一体化存储关系型数据和向量数据
4. **性能瓶颈**：检索延迟过高时，考虑增加向量数据库副本，或者使用缓存机制缓存高频查询结果

## 常见问题

### Q: 支持多大规模的向量数据？
A: 理论上支持无限规模，取决于底层向量数据库的部署方式。分布式部署的Milvus可以轻松支持百亿级向量，单节点Weaviate支持百万到千万级向量。

### Q: 向量检索的响应时间是多少？
A: 取决于数据量和检索参数：
- 百万级向量数据集：通常在100-300ms
- 千万级向量数据集：通常在300-1000ms
- 亿级以上向量数据集：需要分布式部署，响应时间在1s左右

### Q: 如何选择合适的向量数据库？
A: - 开发测试：Chroma简单易用，无需额外部署
   - 中小规模：Weaviate功能全面，混合检索能力强，内置多租户支持
   - 大规模生产：Milvus性能更好，生态完善，支持分布式部署
   - 已有PostgreSQL数据库：PGVector一体化部署方便，减少技术栈

### Q: 向量维度越高越好吗？
A: 不是。更高的维度通常带来更高的准确率，但会增加存储成本（维度翻倍，存储翻倍）和检索延迟。需要在准确率和性能之间做平衡，通常768-1536维是比较好的选择，能够满足绝大多数场景的需求。

### Q: 更换嵌入模型后，已有的向量数据怎么办？
A: 更换嵌入模型后，需要重新处理所有文档，生成新的向量数据。建议在更换模型前备份原有数据，或者使用新的向量数据集进行切换，平滑过渡。系统提供批量重向量化工具，可以自动化完成这个过程。

### Q: 如何提高检索准确率？
A: 可以从以下几个方面优化：
1. **数据质量**：确保知识库中的文档内容准确、格式规范，避免垃圾数据
2. **分块策略**：根据文档类型和使用场景选择合适的分块策略和参数
3. **模型选择**：选择适合业务场景的嵌入模型，中文场景优先选择中文模型
4. **检索策略**：使用混合检索，调整alpha参数，启用重排序
5. **查询优化**：优化用户查询，使用更精确的查询词，或者启用查询重写功能
6. **效果评估**：定期对检索效果进行评估，持续优化策略和参数
