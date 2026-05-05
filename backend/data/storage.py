"""
数据存储接口 - 向量数据库、知识图谱、关系数据库
增强版：连接健康检查、自动重试、操作统计
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from functools import wraps
from loguru import logger
from backend.core.config import settings


def _retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    重试装饰器：对存储操作进行自动重试
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟递增倍数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} 第 {attempt + 1} 次失败，"
                            f" {current_delay:.1f}s 后重试: {e}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} 已重试 {max_retries} 次仍失败: {e}"
                        )

            raise last_exception
        return wrapper
    return decorator


class VectorStore:
    """向量数据库接口（Milvus/FAISS）- 带连接健康检查和重试机制"""
    
    def __init__(self):
        self.client = None
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self._healthy = False
        self._last_check_time = 0
        self._check_interval = 300  # 健康检查间隔（秒）
        # 操作统计
        self._stats = {"search_count": 0, "add_count": 0, "error_count": 0}
        
        self._init_client()
    
    def _init_client(self):
        """初始化向量数据库客户端"""
        try:
            from pymilvus import connections, Collection
            
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                connect_timeout=10,
            )
            
            try:
                self.collection = Collection(self.collection_name)
            except Exception:
                from pymilvus import CollectionSchema, FieldSchema, DataType
                
                fields = [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
                    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1536),
                    FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
                ]
                schema = CollectionSchema(fields, "Financial reports collection")
                self.collection = Collection(self.collection_name, schema)
            
            self._healthy = True
            self._last_check_time = time.time()
            logger.info(f"向量数据库连接成功: {self.collection_name}")
            
        except Exception as e:
            logger.warning(f"向量数据库初始化失败，将使用本地FAISS: {e}")
            self._healthy = False
            self._init_faiss()
    
    def _init_faiss(self):
        """使用本地FAISS作为备选"""
        try:
            import faiss
            import numpy as np
            
            self.faiss_index = None
            self.faiss_dim = 1536
            self._faiss_data = []  # 存储向量数据（简化版）
            logger.info("使用本地FAISS作为向量存储")
            
        except Exception as e:
            logger.error(f"FAISS初始化失败: {e}")
            self.faiss_index = None
    
    def _should_health_check(self) -> bool:
        """判断是否需要进行健康检查"""
        return (time.time() - self._last_check_time) > self._check_interval
    
    async def _ensure_healthy(self) -> bool:
        """确保连接健康，必要时重新初始化"""
        if not self._healthy or self._should_health_check():
            logger.info("执行向量数据库健康检查...")
            try:
                if hasattr(self, 'collection') and self.collection:
                    # 简单的健康检查：尝试获取集合状态
                    _ = self.collection.num_entities
                    self._healthy = True
                else:
                    self._healthy = False
            except Exception as e:
                logger.warning(f"健康检查失败，尝试重新连接: {e}")
                self._healthy = False
                self._init_client()  # 尝试重新初始化
            
            self._last_check_time = time.time()
        
        return self._healthy

    @_retry_on_failure(max_retries=2, delay=0.5)
    async def add(
        self,
        texts: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
    ):
        """添加文档到向量数据库"""
        await self._ensure_healthy()
        
        try:
            if hasattr(self, 'collection') and self._healthy:
                data = [
                    list(range(len(texts))),
                    texts,
                    vectors,
                    [str(m) for m in metadata],
                ]
                self.collection.insert(data)
                self.collection.flush()
                self._stats["add_count"] += len(texts)
            else:
                logger.warning("FAISS插入功能待实现")
                
        except Exception as e:
            self._stats["error_count"] += 1
            logger.error(f"向量数据库插入失败: {e}")
            raise
    
    @_retry_on_failure(max_retries=2, delay=0.5)
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """向量检索"""
        await self._ensure_healthy()
        
        start_time = time.time()
        
        try:
            if hasattr(self, 'collection') and self._healthy:
                search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
                
                results = self.collection.search(
                    data=[query_vector],
                    anns_field="vector",
                    param=search_params,
                    limit=top_k,
                    output_fields=["text", "metadata"],
                )
                
                formatted_results = []
                for hits in results:
                    for hit in hits:
                        formatted_results.append({
                            "id": hit.id,
                            "content": hit.entity.get("text", ""),
                            "score": hit.score,
                            "metadata": hit.entity.get("metadata", {}),
                        })
                
                elapsed = (time.time() - start_time) * 1000
                self._stats["search_count"] += 1
                logger.debug(f"向量检索完成: {len(formatted_results)} 条结果, 耗时 {elapsed:.1f}ms")
                
                return formatted_results
            else:
                logger.warning("FAISS检索功能待实现")
                return []
                
        except Exception as e:
            self._stats["error_count"] += 1
            logger.error(f"向量检索失败: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储操作统计信息"""
        return {
            **self._stats,
            "healthy": self._healthy,
            "collection": self.collection_name,
        }


class KnowledgeGraph:
    """知识图谱接口（Neo4j）- 带连接池和重试机制"""
    
    def __init__(self):
        self.driver = None
        self._healthy = False
        self._last_check_time = 0
        self._check_interval = 300
        # 操作统计
        self._stats = {
            "entity_count": 0,
            "relation_count": 0,
            "search_count": 0,
            "error_count": 0,
        }
        
        self._init_client()
    
    def _init_client(self):
        """初始化Neo4j客户端（带连接池配置）"""
        try:
            from neo4j import GraphDatabase
            
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                # 连接池配置
                max_connection_pool_size=20,
                connection_timeout=30,
                max_retry_time=30,
            )
            
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1 AS ready")
            
            self._healthy = True
            self._last_check_time = time.time()
            logger.info("知识图谱数据库连接成功")
            
        except Exception as e:
            logger.warning(f"知识图谱数据库初始化失败: {e}")
            self.driver = None
            self._healthy = False
    
    async def _ensure_healthy(self) -> bool:
        """确保 Neo4j 连接健康"""
        if not self._healthy or (time.time() - self._last_check_time) > self._check_interval:
            try:
                if self.driver:
                    with self.driver.session() as session:
                        session.run("RETURN 1")
                    self._healthy = True
                else:
                    self._init_client()
            except Exception as e:
                logger.warning(f"Neo4j 健康检查失败: {e}")
                self._healthy = False
                # 尝试重建连接
                self._init_client()
            
            self._last_check_time = time.time()
        
        return self._healthy
    
    async def _execute_cypher(self, query: str, **params) -> Any:
        """
        执行 Cypher 查询（带重试和错误处理）
        
        Args:
            query: Cypher 查询语句
            **params: 查询参数
        
        Returns:
            查询结果或 None
        """
        if not self.driver:
            return None
        
        await self._ensure_healthy()
        
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                with self.driver.session() as session:
                    result = session.run(query, **params)
                    return result
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Cypher 执行第 {attempt+1} 次失败，重试中: {e}")
                    await asyncio.sleep(0.5 * (attempt + 1))
                    # 尝试恢复连接
                    if attempt == max_retries - 1:
                        self._init_client()
                else:
                    self._stats["error_count"] += 1
                    logger.error(f"Cypher 执行失败（已重试）: {e}")
                    raise
        
        return None
    
    async def add_entity(
        self,
        entity_type: str,
        entity_id: str,
        properties: Dict[str, Any],
    ):
        """添加实体到知识图谱"""
        try:
            query = f"""
            MERGE (e:{entity_type.replace(' ', '_')} {{id: $id}})
            SET e += $properties
            RETURN e
            """
            result = await self._execute_cypher(query, id=entity_id, properties=properties)
            if result:
                self._stats["entity_count"] += 1
        except Exception as e:
            logger.error(f"添加实体失败: {e}")
    
    async def add_relation(
        self,
        from_id: str,
        to_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ):
        """添加关系到知识图谱"""
        try:
            safe_type = relation_type.replace(' ', '_').replace('-', '_')
            query = f"""
            MATCH (a), (b)
            WHERE a.id = $from_id AND b.id = $to_id
            MERGE (a)-[r:{safe_type}]->(b)
            SET r += $properties
            RETURN r
            """
            result = await self._execute_cypher(
                query,
                from_id=from_id,
                to_id=to_id,
                properties=properties or {},
            )
            if result:
                self._stats["relation_count"] += 1
        except Exception as e:
            logger.error(f"添加关系失败: {e}")
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """在知识图谱中搜索"""
        result = await self._execute_cypher(
            """
            MATCH (n)
            WHERE n.name CONTAINS $query OR n.description CONTAINS $query
            RETURN n
            LIMIT $limit
            """,
            query=query,
            limit=top_k,
        )
        
        if not result:
            return []
        
        results = []
        try:
            for record in result:
                node = record["n"]
                results.append({
                    "id": node.get("id", ""),
                    "content": node.get("description", str(node)),
                    "score": 1.0,
                    "metadata": dict(node),
                })
            self._stats["search_count"] += 1
        except Exception as e:
            logger.error(f"知识图谱搜索结果解析失败: {e}")
            self._stats["error_count"] += 1
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识图谱操作统计"""
        return {
            **self._stats,
            "healthy": self._healthy,
            "uri": settings.NEO4J_URI,
        }


async def init_storage():
    """初始化所有存储系统并输出摘要"""
    logger.info("正在初始化数据存储系统...")
    
    vector_store = VectorStore()
    knowledge_graph = KnowledgeGraph()
    
    # 输出初始化摘要
    vs_stats = vector_store.get_stats()
    kg_stats = knowledge_graph.get_stats()
    
    logger.info("=" * 50)
    logger.info("数据存储系统初始化完成:")
    logger.info(f"  向量库(Milvus/FAISS): {'✅ 健康' if vs_stats['healthy'] else '❌ 不可用'}")
    logger.info(f"  知识图谱(Neo4j):       {'✅ 健康' if kg_stats['healthy'] else '❌ 不可用'}")
    logger.info("=" * 50)
