"""
定时任务调度器 - 自动更新数据
增强版：任务执行日志、失败告警、执行统计
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import traceback
from loguru import logger
from backend.services.data_integration_service import DataIntegrationService


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class TaskExecutionLog:
    """任务执行日志记录"""
    task_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_name": self.task_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "details": self.details,
        }


class AlertService:
    """
    简单告警服务
    生产环境可扩展为发送邮件/钉钉/企业微信等
    """

    def __init__(self):
        self.alert_history: List[Dict[str, Any]] = []
        self.max_history = 50

    def send_alert(self, title: str, message: str, level: str = "warning"):
        """发送告警"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "title": title,
            "message": message,
        }
        self.alert_history.append(alert)

        # 限制历史记录数量
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]

        # 记录到日志
        log_func = logger.warning if level == "warning" else logger.error
        log_func(f"[ALERT] {title}: {message}")

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近告警"""
        return self.alert_history[-limit:]


class DataScheduler:
    """数据定时任务调度器 - 带执行日志和告警"""

    def __init__(self):
        self.data_service = DataIntegrationService()
        self.running = False
        self.tasks = {}
        self.alert_service = AlertService()

        # 执行日志
        self.execution_logs: List[TaskExecutionLog] = []
        self.max_logs = 100

        # 统计
        self._stats = {
            "total_executions": 0,
            "success_count": 0,
            "failure_count": 0,
            "last_execution": None,
        }

    def _add_log(self, log: TaskExecutionLog):
        """添加执行日志"""
        self.execution_logs.append(log)
        if len(self.execution_logs) > self.max_logs:
            self.execution_logs = self.execution_logs[-self.max_logs:]

    def _record_success(self, log: TaskExecutionLog):
        """记录成功"""
        log.status = TaskStatus.SUCCESS
        log.end_time = datetime.now()
        if log.start_time:
            log.duration_ms = (log.end_time - log.start_time).total_seconds() * 1000
        self._stats["success_count"] += 1
        self._stats["last_execution"] = log.end_time.isoformat()

    def _record_failure(self, log: TaskExecutionLog, error: Exception, alert: bool = True):
        """记录失败"""
        log.status = TaskStatus.FAILED
        log.end_time = datetime.now()
        log.error_message = str(error)
        if log.start_time:
            log.duration_ms = (log.end_time - log.start_time).total_seconds() * 1000
        self._stats["failure_count"] += 1

        if alert:
            self.alert_service.send_alert(
                title=f"调度任务失败: {log.task_name}",
                message=f"错误: {str(error)}\n时间: {log.end_time.isoformat()}\n重试次数: {log.retry_count}",
                level="error",
            )

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
            log = TaskExecutionLog(
                task_name="daily_update",
                start_time=datetime.now(),
            )
            self._add_log(log)

            try:
                # 每天凌晨2点执行
                now = datetime.now()
                next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)

                if next_run <= now:
                    next_run += timedelta(days=1)

                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"下次每日更新将在 {next_run} 执行（等待 {wait_seconds/3600:.1f} 小时）")

                await asyncio.sleep(wait_seconds)

                if not self.running:
                    break

                # 执行更新
                logger.info("开始执行每日数据更新...")
                await self._execute_daily_update(log)
                self._record_success(log)

            except Exception as e:
                self._record_failure(log, e)
                logger.error(f"每日更新任务失败: {e}")
                await asyncio.sleep(3600)

    async def _weekly_update_task(self):
        """每周更新任务"""
        while self.running:
            log = TaskExecutionLog(
                task_name="weekly_update",
                start_time=datetime.now(),
            )
            self._add_log(log)

            try:
                # 每周一凌晨3点执行
                now = datetime.now()
                days_ahead = 7 - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7

                next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
                next_run += timedelta(days=days_ahead)

                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"下次每周更新将在 {next_run} 执行（等待 {wait_seconds/86400:.1f} 天）")

                await asyncio.sleep(wait_seconds)

                if not self.running:
                    break

                # 执行更新
                logger.info("开始执行每周数据更新...")
                await self._execute_weekly_update(log)
                self._record_success(log)

            except Exception as e:
                self._record_failure(log, e)
                logger.error(f"每周更新任务失败: {e}")
                await asyncio.sleep(86400)

    async def _execute_daily_update(self, log: TaskExecutionLog):
        """执行每日更新"""
        log.status = TaskStatus.RUNNING
        details = {}

        try:
            # 1. 更新最新财报
            current_year = datetime.now().year
            current_month = datetime.now().month

            if current_month in [4, 7, 10, 1]:
                logger.info("检测到季度末，更新最新财报...")
                await self.data_service.integrate_bank_reports(
                    years=[current_year],
                    report_types=["quarterly"],
                    auto_import=True,
                )
                details["bank_reports_updated"] = True

            # 2. 更新宏观经济数据
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

            await self.data_service.integrate_macro_data(
                start_date=start_date,
                end_date=end_date,
                auto_import=True,
            )
            details["macro_data_updated"] = True

            # 3. 更新政策文件
            policy_start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            await self.data_service.integrate_policy_files(
                start_date=policy_start_date,
                end_date=end_date,
                auto_import=True,
            )
            details["policy_files_updated"] = True

            log.details = details
            logger.info("每日数据更新完成")

        except Exception as e:
            log.details = {"error_stage": "daily_update", "error": str(e)}
            raise

    async def _execute_weekly_update(self, log: TaskExecutionLog):
        """执行每周更新"""
        log.status = TaskStatus.RUNNING

        try:
            logger.info("开始执行每周完整数据更新...")

            await self.data_service.full_integration(
                include_banks=True,
                include_macro=True,
                include_policies=True,
            )

            log.details = {"full_integration": True}
            logger.info("每周完整数据更新完成")

        except Exception as e:
            log.details = {"error_stage": "weekly_update", "error": str(e)}
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
        log = TaskExecutionLog(
            task_name=f"manual_{update_type}",
            start_time=datetime.now(),
            details={"manual": True, "params": kwargs},
        )
        self._add_log(log)

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

            self._record_success(log)
            return {
                "success": True,
                "result": result,
                "execution_log": log.to_dict(),
            }

        except Exception as e:
            self._record_failure(log, e)
            return {
                "success": False,
                "error": str(e),
                "execution_log": log.to_dict(),
            }

    def get_execution_logs(
        self,
        task_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """获取执行日志"""
        logs = self.execution_logs

        if task_name:
            logs = [l for l in logs if l.task_name == task_name]
        if status:
            logs = [l for l in logs if l.status.value == status]

        return [log.to_dict() for log in logs[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        """获取调度器统计"""
        return {
            **self._stats,
            "running": self.running,
            "total_logs": len(self.execution_logs),
            "recent_alerts": self.alert_service.get_recent_alerts(5),
        }

    def get_health(self) -> Dict[str, Any]:
        """健康检查"""
        recent_failures = [
            l for l in self.execution_logs[-10:]
            if l.status == TaskStatus.FAILED
        ]

        # 最近10次执行中失败超过5次则告警
        is_healthy = len(recent_failures) < 5

        return {
            "healthy": is_healthy,
            "running": self.running,
            "recent_failure_count": len(recent_failures),
            "last_execution": self._stats["last_execution"],
        }


# 全局调度器实例
scheduler = DataScheduler()
