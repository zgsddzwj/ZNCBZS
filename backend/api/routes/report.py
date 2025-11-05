"""
财报相关API
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class ReportQuery(BaseModel):
    """财报查询请求"""
    company: str  # 公司名称或代码
    year: Optional[int] = None
    quarter: Optional[int] = None
    report_type: str = "annual"  # annual, quarterly, semi-annual


class IndicatorQuery(BaseModel):
    """指标查询请求"""
    company: str
    indicator: str  # 指标名称，如"营收"、"净利润"、"ROE"
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    comparison_type: str = "yoy"  # yoy: 同比, qoq: 环比


class ComparisonQuery(BaseModel):
    """对比查询请求"""
    companies: List[str]
    indicators: List[str]
    year: int
    comparison_type: str = "absolute"  # absolute: 绝对值, growth: 增长率


@router.post("/query")
async def query_report(query: ReportQuery):
    """
    查询财报数据
    """
    try:
        from backend.services.report_service import ReportService
        
        service = ReportService()
        result = await service.get_report_data(
            company=query.company,
            year=query.year,
            quarter=query.quarter,
            report_type=query.report_type,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indicators")
async def query_indicator(query: IndicatorQuery):
    """
    查询财务指标
    
    示例：
    - 查询"贵州茅台2023年营收"
    - 查询"招商银行近三年不良率"
    """
    try:
        from backend.services.analysis_service import AnalysisService
        
        service = AnalysisService()
        result = await service.get_indicator(
            company=query.company,
            indicator=query.indicator,
            start_year=query.start_year,
            end_year=query.end_year,
            comparison_type=query.comparison_type,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_companies(query: ComparisonQuery):
    """
    跨公司对比
    
    示例：
    - 对比"工行与建行的拨备覆盖率"
    """
    try:
        from backend.services.analysis_service import AnalysisService
        
        service = AnalysisService()
        result = await service.compare_companies(
            companies=query.companies,
            indicators=query.indicators,
            year=query.year,
            comparison_type=query.comparison_type,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_reports(
    company: Optional[str] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    列出可用的财报
    """
    try:
        from backend.services.report_service import ReportService
        
        service = ReportService()
        result = await service.list_reports(
            company=company,
            start_year=start_year,
            end_year=end_year,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

