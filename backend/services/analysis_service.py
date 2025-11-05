"""
分析服务 - 指标分析、归因分析、风险分析、行业对标
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from backend.engine.llm_service import LLMService
from backend.data.storage import KnowledgeGraph
from backend.services.alert_service import AlertService
from backend.models.attribution.xgboost_attribution import XGBoostAttributionModel


class AnalysisService:
    """分析服务"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.knowledge_graph = KnowledgeGraph()
        self.alert_service = AlertService()
        self.attribution_model = XGBoostAttributionModel()  # XGBoost归因模型
    
    async def get_indicator(
        self,
        company: str,
        indicator: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        comparison_type: str = "yoy",
    ) -> Dict[str, Any]:
        """
        查询财务指标
        
        Args:
            company: 公司名称
            indicator: 指标名称
            start_year: 起始年份
            end_year: 结束年份
            comparison_type: 对比类型（yoy: 同比, qoq: 环比）
        """
        try:
            # 从知识图谱查询指标数据
            query = f"{company} {indicator}"
            if start_year and end_year:
                query += f" {start_year}-{end_year}"
            
            results = await self.knowledge_graph.search(
                query=query,
                top_k=10,
            )
            
            # 计算对比数据
            comparison_data = self._calculate_comparison(results, comparison_type)
            
            # 检查异常预警（如果是最新年份）
            alert = None
            if end_year and results:
                # 尝试获取最新值
                latest_value = self._extract_latest_value(results, end_year)
                if latest_value:
                    alert = await self.alert_service.check_indicator_alert(
                        company=company,
                        indicator=indicator,
                        year=end_year,
                        value=latest_value,
                    )
            
            return {
                "company": company,
                "indicator": indicator,
                "values": results,
                "comparison": comparison_data,
                "alert": alert,
            }
            
        except Exception as e:
            logger.error(f"查询指标失败: {e}")
            raise
    
    async def compare_companies(
        self,
        companies: List[str],
        indicators: List[str],
        year: int,
        comparison_type: str = "absolute",
    ) -> Dict[str, Any]:
        """
        跨公司对比
        """
        try:
            comparison_results = {}
            
            for company in companies:
                for indicator in indicators:
                    key = f"{company}_{indicator}"
                    query = f"{company} {indicator} {year}"
                    
                    results = await self.knowledge_graph.search(
                        query=query,
                        top_k=5,
                    )
                    
                    comparison_results[key] = results
            
            return {
                "year": year,
                "comparison_type": comparison_type,
                "results": comparison_results,
            }
            
        except Exception as e:
            logger.error(f"公司对比失败: {e}")
            raise
    
    async def analyze_attribution(
        self,
        company: str,
        indicator: str,
        period: str,
        change_type: str = "decrease",
    ) -> Dict[str, Any]:
        """
        指标波动归因分析
        """
        try:
            # 构建分析提示
            prompt = f"""
分析{company}在{period}期间{indicator}的{change_type}原因。

请从以下维度分析：
1. 主要影响因素
2. 各因素的影响程度（百分比）
3. 关键驱动因素

返回JSON格式的分析结果。
"""
            
            # 使用XGBoost模型进行归因分析（如果可用）
            # 否则使用LLM
            try:
                # TODO: 从数据中提取特征
                features = self._extract_features_for_attribution(
                    company, indicator, period
                )
                attribution_result = self.attribution_model.analyze_attribution(features)
                analysis_result = attribution_result
            except Exception as e:
                logger.warning(f"XGBoost归因分析失败，使用LLM: {e}")
                # 使用LLM进行归因分析
                analysis_result = await self.llm_service.generate(
                    prompt=prompt,
                    temperature=0.2,
                    max_tokens=1000,
                )
            
            return {
                "company": company,
                "indicator": indicator,
                "period": period,
                "change_type": change_type,
                "attribution": analysis_result,
            }
            
        except Exception as e:
            logger.error(f"归因分析失败: {e}")
            raise
    
    async def analyze_risk(
        self,
        company: str,
        year: int,
        indicators: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        风险预警分析
        """
        try:
            # 默认分析关键指标
            if not indicators:
                indicators = ["资产负债率", "流动比率", "不良率", "ROE"]
            
            # 查询指标数据
            risk_signals = []
            for indicator in indicators:
                query = f"{company} {indicator} {year}"
                results = await self.knowledge_graph.search(query, top_k=5)
                
                # 评估风险（简化版）
                risk_level = self._assess_risk(indicator, results)
                if risk_level != "low":
                    risk_signals.append({
                        "indicator": indicator,
                        "risk_level": risk_level,
                        "data": results,
                    })
            
            return {
                "company": company,
                "year": year,
                "risk_signals": risk_signals,
                "overall_risk": self._calculate_overall_risk(risk_signals),
            }
            
        except Exception as e:
            logger.error(f"风险分析失败: {e}")
            raise
    
    async def compare_industry(
        self,
        company: str,
        indicator: str,
        benchmark_years: int = 3,
    ) -> Dict[str, Any]:
        """
        行业对标分析
        """
        try:
            # 查询公司指标
            company_query = f"{company} {indicator}"
            company_data = await self.knowledge_graph.search(company_query, top_k=10)
            
            # 查询行业均值（简化版）
            industry_query = f"行业平均 {indicator}"
            industry_data = await self.knowledge_graph.search(industry_query, top_k=5)
            
            # 计算百分位排名
            percentile_rank = self._calculate_percentile_rank(company_data, industry_data)
            
            return {
                "company": company,
                "indicator": indicator,
                "company_data": company_data,
                "industry_data": industry_data,
                "percentile_rank": percentile_rank,
                "competitiveness": self._assess_competitiveness(percentile_rank),
            }
            
        except Exception as e:
            logger.error(f"行业对标失败: {e}")
            raise
    
    async def analyze_trend(
        self,
        company: str,
        indicator: str,
        years: int = 5,
    ) -> Dict[str, Any]:
        """
        趋势分析
        """
        try:
            # 查询多年数据
            query = f"{company} {indicator}"
            results = await self.knowledge_graph.search(query, top_k=years * 4)
            
            # 提取时间序列数据
            time_series = self._extract_time_series(results, years)
            
            # 计算趋势
            trend = self._calculate_trend(time_series)
            
            return {
                "company": company,
                "indicator": indicator,
                "time_series": time_series,
                "trend": trend,
            }
            
        except Exception as e:
            logger.error(f"趋势分析失败: {e}")
            raise
    
    def _calculate_comparison(self, results: List[Dict], comparison_type: str) -> Dict:
        """计算对比数据（简化版）"""
        return {"type": comparison_type, "change": 0}
    
    def _assess_risk(self, indicator: str, data: List[Dict]) -> str:
        """评估风险等级"""
        # 简化版，实际应该基于业务规则
        return "low"
    
    def _calculate_overall_risk(self, risk_signals: List[Dict]) -> str:
        """计算整体风险"""
        if not risk_signals:
            return "low"
        
        high_count = sum(1 for s in risk_signals if s["risk_level"] == "high")
        if high_count >= 2:
            return "high"
        elif high_count >= 1:
            return "medium"
        return "low"
    
    def _calculate_percentile_rank(self, company_data: List, industry_data: List) -> float:
        """计算百分位排名"""
        # 简化版
        return 50.0
    
    def _assess_competitiveness(self, percentile_rank: float) -> str:
        """评估竞争力"""
        if percentile_rank >= 75:
            return "强"
        elif percentile_rank >= 50:
            return "中等"
        else:
            return "弱"
    
    def _extract_time_series(self, results: List[Dict], years: int) -> List[Dict]:
        """提取时间序列数据"""
        # 简化版
        return []
    
    def _calculate_trend(self, time_series: List[Dict]) -> str:
        """计算趋势"""
        return "上升"
    
    def _extract_features_for_attribution(
        self,
        company: str,
        indicator: str,
        period: str,
    ) -> Dict[str, float]:
        """提取归因分析所需的特征"""
        # TODO: 从知识图谱中提取相关特征数据
        # 这里返回示例数据
        return {
            "net_interest_margin": 2.5,
            "operating_cost_ratio": 0.6,
            "loan_growth_rate": 0.1,
            "deposit_growth_rate": 0.08,
            "npl_ratio": 0.015,
            "provision_coverage": 1.5,
            "roe": 0.12,
            "asset_quality_score": 0.85,
        }
    
    def _extract_latest_value(self, results: List[Dict], year: int) -> Optional[float]:
        """提取最新年份的值"""
        # 简化版，实际应该从results中解析
        return None
    
    async def deep_interpretation(
        self,
        company: str,
        year: int,
        report_type: str = "annual",
    ) -> Dict[str, Any]:
        """
        深度财报解读
        
        提取关键信息（管理层讨论与分析、风险提示、业务战略调整）
        """
        try:
            # 检索财报文本
            query = f"{company} {year} {report_type} 财报文本"
            from backend.engine.retrieval import RetrievalEngine
            retrieval = RetrievalEngine()
            docs = await retrieval.retrieve(query, top_k=20)
            
            # 提取关键信息
            prompt = f"""
分析以下财报内容，提取关键信息：

财报内容：
{chr(10).join([d.get("content", "")[:1000] for d in docs[:10]])}

请提取：
1. 管理层讨论与分析要点
2. 风险提示
3. 业务战略调整
4. 关键财务数据变化

返回结构化JSON格式。
"""
            
            interpretation = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=3000,
            )
            
            return {
                "company": company,
                "year": year,
                "report_type": report_type,
                "interpretation": interpretation,
                "sources": [{"source": d.get("source", ""), "page": d.get("page")} for d in docs[:5]],
            }
            
        except Exception as e:
            logger.error(f"深度财报解读失败: {e}")
            raise
    
    async def predict_trend(
        self,
        company: str,
        indicator: str,
        years: int = 2,
    ) -> Dict[str, Any]:
        """
        趋势预测
        
        基于历史财报数据、宏观经济指标及行业趋势，预测未来1-2年核心指标
        """
        try:
            # 获取历史数据
            query = f"{company} {indicator}"
            historical_results = await self.knowledge_graph.search(query, top_k=20)
            
            # 获取宏观经济数据
            macro_query = "GDP 利率 通胀率"
            macro_results = await self.knowledge_graph.search(macro_query, top_k=10)
            
            # 构建预测提示
            prompt = f"""
基于以下历史数据和宏观经济指标，预测{company}未来{years}年的{indicator}：

历史数据：
{historical_results[:10]}

宏观经济指标：
{macro_results[:5]}

请预测：
1. 未来{years}年的{indicator}值
2. 预测趋势（上升/下降/平稳）
3. 置信度（0-100%）
4. 主要影响因素

返回JSON格式，包含：
- predicted_values: [{{year: 2024, value: xxx, confidence: 80%}}, ...]
- trend: "上升/下降/平稳"
- confidence: 80
- factors: ["影响因素1", "影响因素2", ...]
"""
            
            prediction = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=2000,
                use_deepseek=True,  # 使用DeepSeek处理长文本
            )
            
            return {
                "company": company,
                "indicator": indicator,
                "prediction_years": years,
                "prediction": prediction,
                "historical_data": historical_results[:10],
            }
            
        except Exception as e:
            logger.error(f"趋势预测失败: {e}")
            raise

