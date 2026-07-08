"""
财报相关API
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from backend.core.auth import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


class ReportQuery(BaseModel):
    """财报查询请求"""
    company: str = Field(..., min_length=1, max_length=100, description="公司名称或代码")
    year: Optional[int] = Field(None, ge=2000, le=2100, description="年份")
    quarter: Optional[int] = Field(None, ge=1, le=4, description="季度")
    report_type: str = Field("annual", pattern="^(annual|quarterly|semi-annual)$", description="报告类型")


class IndicatorQuery(BaseModel):
    """指标查询请求"""
    company: str = Field(..., min_length=1, max_length=100, description="公司名称")
    indicator: str = Field(..., min_length=1, max_length=50, description="指标名称，如营收、净利润、ROE")
    start_year: Optional[int] = Field(None, ge=2000, le=2100, description="起始年份")
    end_year: Optional[int] = Field(None, ge=2000, le=2100, description="结束年份")
    comparison_type: str = Field("yoy", pattern="^(yoy|qoq)$", description="对比类型: yoy同比, qoq环比")


class ComparisonQuery(BaseModel):
    """对比查询请求"""
    companies: List[str] = Field(..., min_length=2, max_length=10, description="公司列表")
    indicators: List[str] = Field(..., min_length=1, max_length=20, description="指标列表")
    year: int = Field(..., ge=2000, le=2100, description="对比年份")
    comparison_type: str = Field("absolute", pattern="^(absolute|growth)$", description="对比方式")


class ReportListResponse(BaseModel):
    """财报列表响应"""
    items: List[dict] = Field(default_factory=list, description="财报列表")
    total: int = Field(0, description="总数")
    limit: int = Field(20, description="每页数量")
    offset: int = Field(0, description="偏移量")


class IndicatorResponse(BaseModel):
    """指标查询响应"""
    company: str = Field(..., description="公司名称")
    indicator: str = Field(..., description="指标名称")
    values: List[dict] = Field(default_factory=list, description="指标数值")
    comparison: Optional[dict] = Field(None, description="对比数据")
    alert: Optional[dict] = Field(None, description="预警信息")


class ComparisonResponse(BaseModel):
    """对比响应"""
    year: int = Field(..., description="对比年份")
    comparison_type: str = Field(..., description="对比方式")
    results: dict = Field(default_factory=dict, description="对比结果")


@router.post("/query", response_model=IndicatorResponse)
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indicators", response_model=IndicatorResponse)
async def query_indicator(query: IndicatorQuery):
    """
    查询财务指标

    示例：
    - 查询"贵州茅台2023年营收"
    - 查询"招商银行近三年不良率"
    """
    try:
        from backend.services.analysis_service import AnalysisService
        from backend.api.deps import get_analysis_service

        service = AnalysisService()
        result = await service.get_indicator(
            company=query.company,
            indicator=query.indicator,
            start_year=query.start_year,
            end_year=query.end_year,
            comparison_type=query.comparison_type,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=ComparisonResponse)
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=ReportListResponse)
async def list_reports(
    company: Optional[str] = Query(None, max_length=100, description="公司名称筛选"),
    start_year: Optional[int] = Query(None, ge=2000, le=2100, description="起始年份"),
    end_year: Optional[int] = Query(None, ge=2000, le=2100, description="结束年份"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
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
        return ReportListResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
