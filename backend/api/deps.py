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
    """获取LLM服务单例"""
    return LLMService()


@lru_cache()
def get_vector_store() -> VectorStore:
    """获取向量数据库单例"""
    return VectorStore()


@lru_cache()
def get_knowledge_graph() -> KnowledgeGraph:
    """获取知识图谱单例"""
    return KnowledgeGraph()


@lru_cache()
def get_bert_reranker() -> BERTReranker:
    """获取Reranker模型单例"""
    return BERTReranker()


@lru_cache()
def get_retrieval_engine() -> RetrievalEngine:
    """获取检索服务单例"""
    return RetrievalEngine(
        llm_service=get_llm_service(),
        vector_store=get_vector_store(),
        knowledge_graph=get_knowledge_graph(),
        reranker=get_bert_reranker(),
    )


@lru_cache()
def get_coordinator() -> Coordinator:
    """获取协调器单例"""
    return Coordinator(
        llm_service=get_llm_service(),
        retrieval_engine=get_retrieval_engine(),
    )
