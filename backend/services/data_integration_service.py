"""
数据集成服务 - 统一管理数据采集、清洗、导入
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from backend.data.collector import (
    BankReportCollector,
    MacroDataCollector,
    PolicyFileCollector,
)
from backend.data.cleaner import DataCleaner
from backend.data.import_service import DataImportService


class DataIntegrationService:
    """数据集成服务"""
    
    def __init__(self):
        self.bank_collector = BankReportCollector()
        self.macro_collector = MacroDataCollector()
        self.policy_collector = PolicyFileCollector()
        self.data_cleaner = DataCleaner()
        self.import_service = DataImportService()
    
    async def integrate_bank_reports(
        self,
        bank_names: Optional[List[str]] = None,
        years: Optional[List[int]] = None,
        report_types: Optional[List[str]] = None,
        auto_import: bool = True,
    ) -> Dict[str, Any]:
        """
        集成银行财报数据（采集+清洗+导入）
        
        Args:
            bank_names: 银行名称列表
            years: 年份列表
            report_types: 报告类型列表
            auto_import: 是否自动导入
        
        Returns:
            集成结果
        """
        logger.info("开始集成银行财报数据...")
        
        # 1. 采集数据
        collected_reports = await self.bank_collector.collect_bank_reports(
            bank_names=bank_names,
            years=years,
            report_types=report_types,
        )
        
        if not collected_reports:
            return {
                "status": "failed",
                "message": "未采集到任何财报数据",
                "collected": 0,
                "imported": 0,
            }
        
        # 2. 导入数据
        import_stats = {}
        if auto_import:
            import_stats = await self.import_service.import_bank_reports(
                collected_reports
            )
        
        return {
            "status": "success",
            "collected": len(collected_reports),
            "import_stats": import_stats,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def integrate_macro_data(
        self,
        indicators: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        auto_import: bool = True,
    ) -> Dict[str, Any]:
        """
        集成宏观经济数据
        
        Args:
            indicators: 指标列表
            start_date: 开始日期
            end_date: 结束日期
            auto_import: 是否自动导入
        
        Returns:
            集成结果
        """
        logger.info("开始集成宏观经济数据...")
        
        # 1. 采集数据
        collected_data = await self.macro_collector.collect_macro_data(
            indicators=indicators,
            start_date=start_date,
            end_date=end_date,
        )
        
        if not collected_data:
            return {
                "status": "failed",
                "message": "未采集到宏观经济数据",
                "collected": 0,
                "imported": 0,
            }
        
        # 2. 导入数据
        import_stats = {}
        if auto_import:
            import_stats = await self.import_service.import_macro_data(
                collected_data
            )
        
        return {
            "status": "success",
            "collected": len(collected_data),
            "import_stats": import_stats,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def integrate_policy_files(
        self,
        sources: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        auto_import: bool = True,
    ) -> Dict[str, Any]:
        """
        集成政策文件
        
        Args:
            sources: 数据源列表
            start_date: 开始日期
            end_date: 结束日期
            auto_import: 是否自动导入
        
        Returns:
            集成结果
        """
        logger.info("开始集成政策文件...")
        
        # 1. 采集数据
        collected_files = await self.policy_collector.collect_policy_files(
            sources=sources,
            start_date=start_date,
            end_date=end_date,
        )
        
        if not collected_files:
            return {
                "status": "failed",
                "message": "未采集到政策文件",
                "collected": 0,
                "imported": 0,
            }
        
        # 2. 导入数据
        import_stats = {}
        if auto_import:
            import_stats = await self.import_service.import_policy_files(
                collected_files
            )
        
        return {
            "status": "success",
            "collected": len(collected_files),
            "import_stats": import_stats,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def full_integration(
        self,
        include_banks: bool = True,
        include_macro: bool = True,
        include_policies: bool = True,
    ) -> Dict[str, Any]:
        """
        完整数据集成（所有数据源）
        
        Args:
            include_banks: 是否包含银行财报
            include_macro: 是否包含宏观经济数据
            include_policies: 是否包含政策文件
        
        Returns:
            完整集成结果
        """
        logger.info("开始完整数据集成...")
        
        results = {
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "results": {},
        }
        
        # 银行财报
        if include_banks:
            try:
                bank_result = await self.integrate_bank_reports()
                results["results"]["bank_reports"] = bank_result
            except Exception as e:
                logger.error(f"银行财报集成失败: {e}")
                results["results"]["bank_reports"] = {
                    "status": "failed",
                    "error": str(e),
                }
        
        # 宏观经济数据
        if include_macro:
            try:
                macro_result = await self.integrate_macro_data()
                results["results"]["macro_data"] = macro_result
            except Exception as e:
                logger.error(f"宏观经济数据集成失败: {e}")
                results["results"]["macro_data"] = {
                    "status": "failed",
                    "error": str(e),
                }
        
        # 政策文件
        if include_policies:
            try:
                policy_result = await self.integrate_policy_files()
                results["results"]["policy_files"] = policy_result
            except Exception as e:
                logger.error(f"政策文件集成失败: {e}")
                results["results"]["policy_files"] = {
                    "status": "failed",
                    "error": str(e),
                }
        
        results["status"] = "completed"
        results["end_time"] = datetime.now().isoformat()
        
        logger.info("完整数据集成完成")
        return results
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """获取数据集成状态"""
        # 统计已导入的数据量
        # 这里可以查询数据库获取统计信息
        return {
            "last_update": datetime.now().isoformat(),
            "status": "ready",
            "statistics": {
                "bank_reports": 0,  # 需要从数据库查询
                "macro_indicators": 0,
                "policy_files": 0,
            },
        }

