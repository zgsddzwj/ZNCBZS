from functools import lru_cache
from typing import Generator, Optional

from fastapi import Depends

from backend.engine.llm_service import LLMService
from backend.data.storage import VectorStore, KnowledgeGraph
from backend.models.reranker.bert_reranker import BERTReranker
from backend.engine.retrieval import RetrievalEngine
from backend.engine.coordinator import Coordinator


@lru_cache()
def get_llm_service() -> LLMService:
    """依赖注入：提供语言模型服务 (LLMService) 的单例。"""
    return LLMService()


@lru_cache()
def get_vector_store() -> VectorStore:
    """依赖注入：提供向量数据库 (VectorStore) 的单例。"""
    return VectorStore()


@lru_cache()
def get_knowledge_graph() -> KnowledgeGraph:
    """依赖注入：提供知识图谱 (KnowledgeGraph) 的单例。"""
    return KnowledgeGraph()


@lru_cache()
def get_bert_reranker() -> BERTReranker:
    """依赖注入：提供 BERT Reranker 模型的单例。"""
    return BERTReranker()


@lru_cache()
def get_retrieval_engine() -> RetrievalEngine:
    """依赖注入：提供检索服务 (RetrievalEngine) 的单例。"""
    return RetrievalEngine(
        llm_service=get_llm_service(),
        vector_store=get_vector_store(),
        knowledge_graph=get_knowledge_graph(),
        reranker=get_bert_reranker(),
    )


@lru_cache()
def get_coordinator() -> Coordinator:
    """依赖注入：提供核心业务协调器 (Coordinator) 的单例。"""
    return Coordinator(
        llm_service=get_llm_service(),
        retrieval_engine=get_retrieval_engine(),
    )
