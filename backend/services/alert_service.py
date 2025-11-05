"""
指标异常预警服务
"""
from typing import Dict, Any, List, Optional
from loguru import logger
from backend.services.analysis_service import AnalysisService
from backend.data.storage import KnowledgeGraph


class AlertService:
    """异常预警服务"""
    
    def __init__(self):
        self.analysis_service = AnalysisService()
        self.knowledge_graph = KnowledgeGraph()
        
        # 预警阈值
        self.INDUSTRY_DEVIATION_THRESHOLD = 0.15  # 行业均值±15%
        self.HISTORICAL_DEVIATION_THRESHOLD = 0.20  # 历史均值±20%
    
    async def check_indicator_alert(
        self,
        company: str,
        indicator: str,
        year: int,
        value: float,
    ) -> Optional[Dict[str, Any]]:
        """
        检查指标异常预警
        
        当指标偏离行业均值±15%或历史均值±20%时，触发预警
        """
        try:
            alerts = []
            
            # 1. 检查行业均值偏离
            industry_alert = await self._check_industry_deviation(
                company, indicator, year, value
            )
            if industry_alert:
                alerts.append(industry_alert)
            
            # 2. 检查历史均值偏离
            historical_alert = await self._check_historical_deviation(
                company, indicator, year, value
            )
            if historical_alert:
                alerts.append(historical_alert)
            
            if alerts:
                return {
                    "company": company,
                    "indicator": indicator,
                    "year": year,
                    "value": value,
                    "alerts": alerts,
                    "severity": self._calculate_severity(alerts),
                }
            
            return None
            
        except Exception as e:
            logger.error(f"指标预警检查失败: {e}")
            return None
    
    async def _check_industry_deviation(
        self,
        company: str,
        indicator: str,
        year: int,
        value: float,
    ) -> Optional[Dict[str, Any]]:
        """检查行业均值偏离"""
        try:
            # 查询行业均值
            query = f"行业平均 {indicator} {year}"
            results = await self.knowledge_graph.search(query, top_k=5)
            
            if not results:
                return None
            
            # 提取行业均值（简化版，实际应该从结果中解析）
            # 这里假设从知识库中获取了行业均值
            industry_avg = 0.0  # TODO: 从结果中解析
            
            if industry_avg == 0:
                return None
            
            # 计算偏离度
            deviation = abs(value - industry_avg) / industry_avg
            
            if deviation >= self.INDUSTRY_DEVIATION_THRESHOLD:
                direction = "高于" if value > industry_avg else "低于"
                return {
                    "type": "industry_deviation",
                    "message": f"{indicator}偏离行业均值{deviation*100:.1f}%，{direction}行业均值{abs(value - industry_avg):.2f}",
                    "industry_avg": industry_avg,
                    "deviation": deviation,
                    "threshold": self.INDUSTRY_DEVIATION_THRESHOLD,
                }
            
            return None
            
        except Exception as e:
            logger.error(f"行业均值检查失败: {e}")
            return None
    
    async def _check_historical_deviation(
        self,
        company: str,
        indicator: str,
        year: int,
        value: float,
    ) -> Optional[Dict[str, Any]]:
        """检查历史均值偏离"""
        try:
            # 查询历史数据（近5年）
            query = f"{company} {indicator}"
            results = await self.knowledge_graph.search(query, top_k=20)
            
            if len(results) < 3:
                return None  # 历史数据不足
            
            # 提取历史值（简化版）
            historical_values = []  # TODO: 从结果中解析历史值
            
            if not historical_values:
                return None
            
            # 计算历史均值
            historical_avg = sum(historical_values) / len(historical_values)
            
            # 计算偏离度
            deviation = abs(value - historical_avg) / historical_avg if historical_avg != 0 else 0
            
            if deviation >= self.HISTORICAL_DEVIATION_THRESHOLD:
                direction = "高于" if value > historical_avg else "低于"
                return {
                    "type": "historical_deviation",
                    "message": f"{indicator}偏离历史均值{deviation*100:.1f}%，{direction}历史均值{abs(value - historical_avg):.2f}",
                    "historical_avg": historical_avg,
                    "deviation": deviation,
                    "threshold": self.HISTORICAL_DEVIATION_THRESHOLD,
                }
            
            return None
            
        except Exception as e:
            logger.error(f"历史均值检查失败: {e}")
            return None
    
    def _calculate_severity(self, alerts: List[Dict[str, Any]]) -> str:
        """计算预警严重程度"""
        if not alerts:
            return "normal"
        
        max_deviation = max([a.get("deviation", 0) for a in alerts])
        
        if max_deviation >= 0.30:
            return "high"
        elif max_deviation >= 0.20:
            return "medium"
        else:
            return "low"
    
    async def analyze_alert_reason(
        self,
        alert: Dict[str, Any],
    ) -> str:
        """
        分析预警原因
        
        自动分析指标异常的可能原因
        """
        try:
            company = alert.get("company")
            indicator = alert.get("indicator")
            year = alert.get("year")
            alerts = alert.get("alerts", [])
            
            from backend.engine.llm_service import LLMService
            llm_service = LLMService()
            
            prompt = f"""
分析以下银行指标异常的原因：

银行：{company}
指标：{indicator}
年份：{year}

异常情况：
{chr(10).join([a.get("message", "") for a in alerts])}

请分析可能的原因，如：
- 区域经济下行
- 业务结构调整
- 监管政策影响
- 市场竞争加剧
- 内部管理问题

要求：
1. 列出3-5个可能原因
2. 按重要性排序
3. 提供简要分析
"""
            
            analysis = await llm_service.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1000,
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"预警原因分析失败: {e}")
            return "无法分析预警原因"

