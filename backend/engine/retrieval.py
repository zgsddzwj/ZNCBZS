"""
知识检索引擎 - RAG技术实现
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from backend.engine.llm_service import LLMService
from backend.data.storage import VectorStore, KnowledgeGraph
from backend.models.reranker.bert_reranker import BERTReranker


class RetrievalEngine:
    """知识检索引擎 - 集成关键词检索、向量检索、混合排序"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.vector_store = VectorStore()
        self.knowledge_graph = KnowledgeGraph()
        self.reranker = BERTReranker()  # 使用BERT Reranker模型
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        use_hybrid: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        检索相关知识
        
        Args:
            query: 查询文本
            top_k: 返回top K结果
            filters: 过滤条件（如公司、时间等）
            use_hybrid: 是否使用混合检索
            
        Returns:
            检索结果列表，每个结果包含content, source, score等
        """
        try:
            results = []
            
            if use_hybrid:
                # 混合检索：向量检索 + 关键词检索
                vector_results = await self._vector_retrieve(query, top_k, filters)
                keyword_results = await self._keyword_retrieve(query, top_k, filters)
                
                # 合并和去重
                results = self._merge_results(vector_results, keyword_results)
                
                # 重排序（使用Reranker模型）
                results = await self._rerank(query, results, top_k)
            else:
                # 仅向量检索
                results = await self._vector_retrieve(query, top_k, filters)
            
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
        # 生成查询向量
        query_vector = await self.llm_service.embed(query)
        
        # 从向量数据库检索
        results = await self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k * 2,  # 检索更多结果用于重排序
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
        # 从知识图谱检索
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
        # 使用文档ID去重
        seen_ids = set()
        merged = []
        
        # 优先添加向量检索结果
        for result in vector_results:
            doc_id = result.get("id")
            if doc_id and doc_id not in seen_ids:
                result["score"] = result.get("score", 0) * 0.7  # 向量检索权重
                merged.append(result)
                seen_ids.add(doc_id)
        
        # 添加关键词检索结果
        for result in keyword_results:
            doc_id = result.get("id")
            if doc_id and doc_id not in seen_ids:
                result["score"] = result.get("score", 0) * 0.3  # 关键词检索权重
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
            # 使用BERT Reranker模型进行重排序
            if self.reranker and self.reranker.model:
                reranked = self.reranker.rerank(query, results, top_k)
                return reranked
            else:
                # 如果Reranker模型未加载，使用简化版
                logger.warning("Reranker模型未加载，使用原始排序")
                return results[:top_k]
            
        except Exception as e:
            logger.warning(f"重排序失败，使用原始结果: {e}")
            return results[:top_k]

