"""
定时任务调度器 - 自动更新数据
"""
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio
from loguru import logger
from backend.services.data_integration_service import DataIntegrationService


class DataScheduler:
    """数据定时任务调度器"""
    
    def __init__(self):
        self.data_service = DataIntegrationService()
        self.running = False
        self.tasks = {}
    
    async def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行")
            return
        
        self.running = True
        logger.info("数据调度器已启动")
        
        # 启动定时任务
        asyncio.create_task(self._daily_update_task())
        asyncio.create_task(self._weekly_update_task())
    
    async def stop(self):
        """停止调度器"""
        self.running = False
        logger.info("数据调度器已停止")
    
    async def _daily_update_task(self):
        """每日更新任务"""
        while self.running:
            try:
                # 每天凌晨2点执行
                now = datetime.now()
                next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
                
                if next_run <= now:
                    next_run += timedelta(days=1)
                
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"下次每日更新将在 {next_run} 执行（等待 {wait_seconds/3600:.1f} 小时）")
                
                await asyncio.sleep(wait_seconds)
                
                # 执行更新
                logger.info("开始执行每日数据更新...")
                await self._execute_daily_update()
                
            except Exception as e:
                logger.error(f"每日更新任务失败: {e}")
                await asyncio.sleep(3600)  # 错误后等待1小时重试
    
    async def _weekly_update_task(self):
        """每周更新任务"""
        while self.running:
            try:
                # 每周一凌晨3点执行
                now = datetime.now()
                days_ahead = 7 - now.weekday()  # 周一
                if days_ahead <= 0:
                    days_ahead += 7
                
                next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
                next_run += timedelta(days=days_ahead)
                
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"下次每周更新将在 {next_run} 执行（等待 {wait_seconds/86400:.1f} 天）")
                
                await asyncio.sleep(wait_seconds)
                
                # 执行更新
                logger.info("开始执行每周数据更新...")
                await self._execute_weekly_update()
                
            except Exception as e:
                logger.error(f"每周更新任务失败: {e}")
                await asyncio.sleep(86400)  # 错误后等待1天重试
    
    async def _execute_daily_update(self):
        """执行每日更新"""
        try:
            # 1. 更新最新财报（检查是否有新发布的财报）
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            # 如果是季度末，检查是否有新财报
            if current_month in [4, 7, 10, 1]:  # 季度末
                logger.info("检测到季度末，更新最新财报...")
                await self.data_service.integrate_bank_reports(
                    years=[current_year],
                    report_types=["quarterly"],
                    auto_import=True,
                )
            
            # 2. 更新宏观经济数据（最近30天）
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            await self.data_service.integrate_macro_data(
                start_date=start_date,
                end_date=end_date,
                auto_import=True,
            )
            
            # 3. 更新政策文件（最近7天）
            policy_start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            
            await self.data_service.integrate_policy_files(
                start_date=policy_start_date,
                end_date=end_date,
                auto_import=True,
            )
            
            logger.info("每日数据更新完成")
            
        except Exception as e:
            logger.error(f"执行每日更新失败: {e}")
            raise
    
    async def _execute_weekly_update(self):
        """执行每周更新"""
        try:
            # 完整更新所有数据（可能需要较长时间）
            logger.info("开始执行每周完整数据更新...")
            
            await self.data_service.full_integration(
                include_banks=True,
                include_macro=True,
                include_policies=True,
            )
            
            logger.info("每周完整数据更新完成")
            
        except Exception as e:
            logger.error(f"执行每周更新失败: {e}")
            raise
    
    async def trigger_manual_update(
        self,
        update_type: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        手动触发更新
        
        Args:
            update_type: 更新类型（bank_reports, macro_data, policy_files, full）
            **kwargs: 更新参数
        """
        try:
            if update_type == "bank_reports":
                result = await self.data_service.integrate_bank_reports(**kwargs)
            elif update_type == "macro_data":
                result = await self.data_service.integrate_macro_data(**kwargs)
            elif update_type == "policy_files":
                result = await self.data_service.integrate_policy_files(**kwargs)
            elif update_type == "full":
                result = await self.data_service.full_integration(**kwargs)
            else:
                raise ValueError(f"不支持的更新类型: {update_type}")
            
            return {
                "success": True,
                "result": result,
            }
            
        except Exception as e:
            logger.error(f"手动触发更新失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }


# 全局调度器实例
scheduler = DataScheduler()

