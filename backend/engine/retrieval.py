"""
知识检索引擎 - RAG技术实现
增强版：添加LRU缓存层减少重复检索，提升响应速度
"""
import time
import hashlib
from typing import List, Dict, Any, Optional
from collections import OrderedDict
from loguru import logger
from backend.engine.llm_service import LLMService
from backend.data.storage import VectorStore, KnowledgeGraph
from backend.models.reranker.bert_reranker import BERTReranker


class LRUCache:
    """
    简单的LRU缓存实现

    用于缓存检索结果，避免相同查询的重复计算。
    键为查询文本的hash，值为(结果列表, 过期时间)。
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        """
        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 缓存过期时间（秒）
        """
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._cache: OrderedDict[str, tuple] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _make_key(self, query: str, filters: Optional[Dict], top_k: int, use_hybrid: bool) -> str:
        """生成缓存键"""
        key_data = f"{query}:{sorted(filters.items()) if filters else ''}:{top_k}:{use_hybrid}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, query: str, filters: Optional[Dict], top_k: int, use_hybrid: bool) -> Optional[List[Dict]]:
        """获取缓存结果"""
        key = self._make_key(query, filters, top_k, use_hybrid)

        if key in self._cache:
            results, expire_time = self._cache[key]
            if time.time() < expire_time:
                # 命中且未过期，移到末尾（最近使用）
                self._cache.move_to_end(key)
                self._hits += 1
                return results
            else:
                # 已过期，删除
                del self._cache[key]

        self._misses += 1
        return None

    def set(self, query: str, filters: Optional[Dict], top_k: int, use_hybrid: bool, results: List[Dict]):
        """设置缓存结果"""
        key = self._make_key(query, filters, top_k, use_hybrid)

        # 如果已满，移除最久未使用的
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._cache.popitem(last=False)

        self._cache[key] = (results, time.time() + self.ttl)
        self._cache.move_to_end(key)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "ttl_seconds": self.ttl,
        }

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0


class RetrievalEngine:
    """知识检索引擎 - 集成关键词检索、向量检索、混合排序、结果缓存"""

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        vector_store: Optional[VectorStore] = None,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        reranker: Optional[BERTReranker] = None,
        cache_enabled: bool = True,
    ):
        self.llm_service = llm_service or LLMService()
        self.vector_store = vector_store or VectorStore()
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()
        self.reranker = reranker or BERTReranker()

        # 初始化缓存
        self.cache_enabled = cache_enabled
        self._cache = LRUCache(max_size=100, ttl_seconds=300) if cache_enabled else None

        # 统计
        self._stats = {
            "total_queries": 0,
            "cached_queries": 0,
            "vector_queries": 0,
            "keyword_queries": 0,
            "hybrid_queries": 0,
        }

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        use_hybrid: bool = True,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        检索相关知识

        Args:
            query: 查询文本
            top_k: 返回top K结果
            filters: 过滤条件（如公司、时间等）
            use_hybrid: 是否使用混合检索
            use_cache: 是否使用缓存

        Returns:
            检索结果列表，每个结果包含content, source, score等
        """
        self._stats["total_queries"] += 1

        # 1. 尝试从缓存获取
        if use_cache and self._cache and self.cache_enabled:
            cached = self._cache.get(query, filters, top_k, use_hybrid)
            if cached is not None:
                self._stats["cached_queries"] += 1
                logger.debug(f"缓存命中: {query[:30]}...")
                return cached

        try:
            results = []
            start_time = time.time()

            if use_hybrid:
                self._stats["hybrid_queries"] += 1
                # 混合检索：向量检索 + 关键词检索
                vector_results = await self._vector_retrieve(query, top_k, filters)
                keyword_results = await self._keyword_retrieve(query, top_k, filters)

                # 合并和去重
                results = self._merge_results(vector_results, keyword_results)

                # 重排序
                results = await self._rerank(query, results, top_k)
            else:
                self._stats["vector_queries"] += 1
                # 仅向量检索
                results = await self._vector_retrieve(query, top_k, filters)

            elapsed = (time.time() - start_time) * 1000
            logger.info(f"检索完成: {query[:40]}... | {len(results)}条结果 | {elapsed:.1f}ms")

            # 写入缓存
            if use_cache and self._cache and self.cache_enabled:
                self._cache.set(query, filters, top_k, use_hybrid, results[:top_k])

            return results[:top_k]

        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []

    async def _vector_retrieve(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """向量语义检索"""
        query_vector = await self.llm_service.embed(query)

        results = await self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k * 2,
            filters=filters,
        )

        return results

    async def _keyword_retrieve(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """关键词精确检索"""
        self._stats["keyword_queries"] += 1

        results = await self.knowledge_graph.search(
            query=query,
            top_k=top_k * 2,
            filters=filters,
        )

        return results

    def _merge_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """合并检索结果并去重"""
        seen_ids = set()
        merged = []

        # 优先添加向量检索结果
        for result in vector_results:
            doc_id = result.get("id")
            if doc_id and doc_id not in seen_ids:
                result["score"] = result.get("score", 0) * 0.7
                merged.append(result)
                seen_ids.add(doc_id)

        # 添加关键词检索结果
        for result in keyword_results:
            doc_id = result.get("id")
            if doc_id and doc_id not in seen_ids:
                result["score"] = result.get("score", 0) * 0.3
                merged.append(result)
                seen_ids.add(doc_id)

        # 按分数排序
        merged.sort(key=lambda x: x.get("score", 0), reverse=True)

        return merged

    async def _rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """使用Reranker模型重排序"""
        if not results:
            return []

        try:
            if self.reranker and self.reranker.model:
                reranked = self.reranker.rerank(query, results, top_k)
                return reranked
            else:
                logger.warning("Reranker模型未加载，使用原始排序")
                return results[:top_k]

        except Exception as e:
            logger.warning(f"重排序失败，使用原始结果: {e}")
            return results[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        """获取检索引擎统计信息"""
        stats = {
            **self._stats,
            "cache_enabled": self.cache_enabled,
        }
        if self._cache:
            stats["cache"] = self._cache.get_stats()
        return stats

    def clear_cache(self):
        """清空检索缓存"""
        if self._cache:
            self._cache.clear()
            logger.info("检索缓存已清空")
