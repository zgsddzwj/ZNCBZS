"""
数据导入服务 - 负责数据入库流程
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from backend.data.storage import VectorStore, KnowledgeGraph
from backend.data.processor import DocumentProcessor
from backend.data.cleaner import DataCleaner
from backend.engine.llm_service import LLMService
import json


class DataImportService:
    """数据导入服务"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.knowledge_graph = KnowledgeGraph()
        self.document_processor = DocumentProcessor()
        self.data_cleaner = DataCleaner()
        self.llm_service = LLMService()
    
    async def import_bank_reports(
        self,
        reports: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        导入银行财报数据
        
        Args:
            reports: 财报信息列表（包含file_path等信息）
        
        Returns:
            导入结果统计
        """
        stats = {
            "total": len(reports),
            "success": 0,
            "failed": 0,
            "errors": [],
        }
        
        for report in reports:
            try:
                # 1. 处理文档
                file_path = report.get("file_path")
                if not file_path:
                    continue
                
                processed_data = await self.document_processor.process_document(
                    file_path=file_path,
                    file_type="pdf",
                    company=report.get("bank"),
                    year=report.get("year"),
                    report_type=report.get("report_type", "annual"),
                )
                
                # 2. 清洗数据
                cleaned_data = self.data_cleaner.clean_bank_report_data(processed_data)
                
                # 3. 提取指标到知识图谱
                await self._import_indicators_to_kg(
                    cleaned_data["bank"],
                    cleaned_data["year"],
                    cleaned_data["indicators"],
                )
                
                # 4. 导入文本到向量数据库
                await self._import_text_to_vector(
                    cleaned_data["text"],
                    {
                        "bank": cleaned_data["bank"],
                        "year": cleaned_data["year"],
                        "report_type": cleaned_data["report_type"],
                        "source": cleaned_data["metadata"].get("source", ""),
                    },
                )
                
                stats["success"] += 1
                logger.info(f"成功导入财报: {report.get('bank')} {report.get('year')}")
                
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append({
                    "report": report.get("bank", "unknown"),
                    "error": str(e),
                })
                logger.error(f"导入财报失败: {e}")
        
        return stats
    
    async def _import_indicators_to_kg(
        self,
        bank: str,
        year: int,
        indicators: Dict[str, float],
    ):
        """将指标导入知识图谱"""
        # 创建或更新银行节点
        await self.knowledge_graph.add_entity(
            entity_type="Bank",
            entity_id=f"{bank}_{year}",
            properties={
                "name": bank,
                "year": year,
                "type": "A股上市银行",
            },
        )
        
        # 创建指标节点并建立关系
        for indicator_name, value in indicators.items():
            # 创建指标节点
            indicator_id = f"indicator_{indicator_name}"
            await self.knowledge_graph.add_entity(
                entity_type="Indicator",
                entity_id=indicator_id,
                properties={
                    "name": indicator_name,
                    "category": self._get_indicator_category(indicator_name),
                },
            )
            
            # 建立银行-指标关系
            await self.knowledge_graph.add_relation(
                from_id=f"{bank}_{year}",
                to_id=indicator_id,
                relation_type="HAS_INDICATOR",
                properties={
                    "value": value,
                    "year": year,
                },
            )
    
    def _get_indicator_category(self, indicator_name: str) -> str:
        """获取指标分类"""
        categories = {
            "营收": "盈利能力",
            "净利润": "盈利能力",
            "ROE": "盈利能力",
            "ROA": "盈利能力",
            "总资产": "资产规模",
            "总负债": "资产规模",
            "不良率": "资产质量",
            "拨备覆盖率": "资产质量",
            "资本充足率": "资本充足率",
            "核心一级资本充足率": "资本充足率",
        }
        return categories.get(indicator_name, "其他")
    
    async def _import_text_to_vector(
        self,
        text: str,
        metadata: Dict[str, Any],
    ):
        """将文本导入向量数据库"""
        if not text:
            return
        
        # 分块（每块1000字符）
        chunk_size = 1000
        chunks = [
            text[i:i + chunk_size]
            for i in range(0, len(text), chunk_size)
        ]
        
        # 生成向量
        vectors = []
        for chunk in chunks:
            try:
                vector = await self.llm_service.embed(chunk)
                vectors.append(vector)
            except Exception as e:
                logger.warning(f"生成向量失败: {e}")
                continue
        
        if vectors:
            # 导入向量数据库
            texts = chunks[:len(vectors)]
            metadata_list = [metadata for _ in texts]
            
            await self.vector_store.add(
                texts=texts,
                vectors=vectors,
                metadata=metadata_list,
            )
    
    async def import_macro_data(
        self,
        macro_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """导入宏观经济数据"""
        stats = {
            "total": len(macro_data),
            "success": 0,
            "failed": 0,
        }
        
        for data in macro_data:
            try:
                # 清洗数据
                cleaned_data = self.data_cleaner.clean_macro_data(data)
                
                # 导入到知识图谱
                indicator_id = f"macro_{cleaned_data['indicator']}"
                await self.knowledge_graph.add_entity(
                    entity_type="MacroIndicator",
                    entity_id=indicator_id,
                    properties={
                        "name": cleaned_data["indicator"],
                        "unit": cleaned_data.get("unit", ""),
                        "frequency": cleaned_data.get("frequency", ""),
                    },
                )
                
                # 添加数据点
                for point in cleaned_data.get("data_points", []):
                    point_id = f"{indicator_id}_{point['date']}"
                    await self.knowledge_graph.add_entity(
                        entity_type="DataPoint",
                        entity_id=point_id,
                        properties=point,
                    )
                    
                    await self.knowledge_graph.add_relation(
                        from_id=indicator_id,
                        to_id=point_id,
                        relation_type="HAS_DATA",
                    )
                
                stats["success"] += 1
                
            except Exception as e:
                stats["failed"] += 1
                logger.error(f"导入宏观经济数据失败: {e}")
        
        return stats
    
    async def import_policy_files(
        self,
        policy_files: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """导入政策文件"""
        stats = {
            "total": len(policy_files),
            "success": 0,
            "failed": 0,
        }
        
        for file_info in policy_files:
            try:
                file_path = file_info.get("file_path")
                if not file_path:
                    continue
                
                # 处理文档
                processed_data = await self.document_processor.process_document(
                    file_path=file_path,
                    file_type="pdf",
                )
                
                # 导入到向量数据库
                await self._import_text_to_vector(
                    processed_data.get("text", ""),
                    {
                        "source": file_info.get("source", ""),
                        "title": file_info.get("title", ""),
                        "publish_date": file_info.get("publish_date", ""),
                        "type": "policy",
                    },
                )
                
                # 导入到知识图谱
                policy_id = f"policy_{file_info.get('source', 'unknown')}_{file_info.get('title', 'unknown')}"
                await self.knowledge_graph.add_entity(
                    entity_type="Policy",
                    entity_id=policy_id,
                    properties={
                        "title": file_info.get("title", ""),
                        "source": file_info.get("source", ""),
                        "publish_date": file_info.get("publish_date", ""),
                    },
                )
                
                stats["success"] += 1
                
            except Exception as e:
                stats["failed"] += 1
                logger.error(f"导入政策文件失败: {e}")
        
        return stats

