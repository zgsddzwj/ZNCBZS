"""
深度分析API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class DeepInterpretationRequest(BaseModel):
    """深度解读请求"""
    company: str
    year: int
    report_type: str = "annual"


class PredictRequest(BaseModel):
    """预测请求"""
    company: str
    indicator: str
    years: int = 2


class AttributionRequest(BaseModel):
    """归因分析请求"""
    company: str
    indicator: str
    period: str  # 如 "2023Q3"
    change_type: str = "decrease"  # increase, decrease


class RiskAnalysisRequest(BaseModel):
    """风险分析请求"""
    company: str
    year: int
    indicators: Optional[List[str]] = None  # 如果为空，分析所有关键指标


class IndustryComparisonRequest(BaseModel):
    """行业对标请求"""
    company: str
    indicator: str
    benchmark_years: int = 3


@router.post("/attribution")
async def analyze_attribution(request: AttributionRequest):
    """
    指标波动归因分析
    
    分析指标异常变化的原因
    示例：分析某公司Q3净利润下降10%的原因
    """
    try:
        from backend.services.analysis_service import AnalysisService
        
        service = AnalysisService()
        result = await service.analyze_attribution(
            company=request.company,
            indicator=request.indicator,
            period=request.period,
            change_type=request.change_type,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk")
async def analyze_risk(request: RiskAnalysisRequest):
    """
    风险预警分析
    
    识别财报中的风险信号
    """
    try:
        from backend.services.analysis_service import AnalysisService
        
        service = AnalysisService()
        result = await service.analyze_risk(
            company=request.company,
            year=request.year,
            indicators=request.indicators,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/industry")
async def compare_industry(request: IndustryComparisonRequest):
    """
    行业对标分析
    
    基于行业数据生成企业竞争力分析
    """
    try:
        from backend.services.analysis_service import AnalysisService
        
        service = AnalysisService()
        result = await service.compare_industry(
            company=request.company,
            indicator=request.indicator,
            benchmark_years=request.benchmark_years,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend/{company}")
async def analyze_trend(
    company: str,
    indicator: str,
    years: int = 5,
):
    """
    趋势分析
    
    分析某公司近N年的指标趋势
    """
    try:
        from backend.services.analysis_service import AnalysisService
        
        service = AnalysisService()
        result = await service.analyze_trend(
            company=company,
            indicator=indicator,
            years=years,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interpretation")
async def deep_interpretation(request: DeepInterpretationRequest):
    """
    深度财报解读
    
    提取关键信息（管理层讨论与分析、风险提示、业务战略调整）
    """
    try:
        from backend.services.analysis_service import AnalysisService
        
        service = AnalysisService()
        result = await service.deep_interpretation(
            company=request.company,
            year=request.year,
            report_type=request.report_type,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict")
async def predict_trend(request: PredictRequest):
    """
    趋势预测
    
    预测未来1-2年的核心指标，附带置信度
    """
    try:
        from backend.services.analysis_service import AnalysisService
        
        service = AnalysisService()
        result = await service.predict_trend(
            company=request.company,
            indicator=request.indicator,
            years=request.years,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

