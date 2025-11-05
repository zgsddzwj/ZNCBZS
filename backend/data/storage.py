"""
数据存储接口 - 向量数据库、知识图谱、关系数据库
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from backend.core.config import settings


class VectorStore:
    """向量数据库接口（Milvus/FAISS）"""
    
    def __init__(self):
        self.client = None
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self._init_client()
    
    def _init_client(self):
        """初始化向量数据库客户端"""
        try:
            from pymilvus import connections, Collection
            
            # 连接Milvus
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
            )
            
            # 获取或创建集合
            try:
                self.collection = Collection(self.collection_name)
            except:
                # 如果集合不存在，创建它
                from pymilvus import CollectionSchema, FieldSchema, DataType
                
                fields = [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
                    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1536),
                    FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
                ]
                schema = CollectionSchema(fields, "Financial reports collection")
                self.collection = Collection(self.collection_name, schema)
            
            logger.info(f"向量数据库连接成功: {self.collection_name}")
            
        except Exception as e:
            logger.warning(f"向量数据库初始化失败，将使用本地FAISS: {e}")
            self._init_faiss()
    
    def _init_faiss(self):
        """使用本地FAISS作为备选"""
        try:
            import faiss
            import numpy as np
            
            self.faiss_index = None
            self.faiss_dim = 1536
            logger.info("使用本地FAISS作为向量存储")
            
        except Exception as e:
            logger.error(f"FAISS初始化失败: {e}")
            self.faiss_index = None
    
    async def add(
        self,
        texts: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
    ):
        """添加文档到向量数据库"""
        try:
            if hasattr(self, 'collection'):
                # 使用Milvus
                data = [
                    list(range(len(texts))),  # ids
                    texts,
                    vectors,
                    [str(m) for m in metadata],
                ]
                self.collection.insert(data)
                self.collection.flush()
            else:
                # 使用FAISS（简化版）
                logger.warning("FAISS插入功能待实现")
                
        except Exception as e:
            logger.error(f"向量数据库插入失败: {e}")
            raise
    
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """向量检索"""
        try:
            if hasattr(self, 'collection'):
                # 使用Milvus
                search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
                
                results = self.collection.search(
                    data=[query_vector],
                    anns_field="vector",
                    param=search_params,
                    limit=top_k,
                    output_fields=["text", "metadata"],
                )
                
                # 格式化结果
                formatted_results = []
                for hits in results:
                    for hit in hits:
                        formatted_results.append({
                            "id": hit.id,
                            "content": hit.entity.get("text", ""),
                            "score": hit.score,
                            "metadata": hit.entity.get("metadata", {}),
                        })
                
                return formatted_results
            else:
                # 使用FAISS（简化版）
                logger.warning("FAISS检索功能待实现")
                return []
                
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []


class KnowledgeGraph:
    """知识图谱接口（Neo4j）"""
    
    def __init__(self):
        self.driver = None
        self._init_client()
    
    def _init_client(self):
        """初始化Neo4j客户端"""
        try:
            from neo4j import GraphDatabase
            
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
            
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            logger.info("知识图谱数据库连接成功")
            
        except Exception as e:
            logger.warning(f"知识图谱数据库初始化失败: {e}")
            self.driver = None
    
    async def add_entity(
        self,
        entity_type: str,
        entity_id: str,
        properties: Dict[str, Any],
    ):
        """添加实体到知识图谱"""
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                query = f"""
                MERGE (e:{entity_type} {{id: $id}})
                SET e += $properties
                RETURN e
                """
                session.run(query, id=entity_id, properties=properties)
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
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH (a), (b)
                WHERE a.id = $from_id AND b.id = $to_id
                MERGE (a)-[r:{relation_type}]->(b)
                SET r += $properties
                RETURN r
                """
                session.run(
                    query,
                    from_id=from_id,
                    to_id=to_id,
                    properties=properties or {},
                )
        except Exception as e:
            logger.error(f"添加关系失败: {e}")
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """在知识图谱中搜索"""
        if not self.driver:
            return []
        
        try:
            results = []
            with self.driver.session() as session:
                # 构建查询（简化版）
                cypher_query = """
                MATCH (n)
                WHERE n.name CONTAINS $query OR n.description CONTAINS $query
                RETURN n
                LIMIT $limit
                """
                
                result = session.run(cypher_query, query=query, limit=top_k)
                
                for record in result:
                    node = record["n"]
                    results.append({
                        "id": node.get("id", ""),
                        "content": node.get("description", str(node)),
                        "score": 1.0,  # 简化版，实际应该计算相关性
                        "metadata": dict(node),
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"知识图谱检索失败: {e}")
            return []


async def init_storage():
    """初始化所有存储系统"""
    logger.info("初始化数据存储系统...")
    
    # 初始化向量数据库
    vector_store = VectorStore()
    
    # 初始化知识图谱
    knowledge_graph = KnowledgeGraph()
    
    logger.info("数据存储系统初始化完成")

