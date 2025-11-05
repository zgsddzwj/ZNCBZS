"""
数据模型和Schema定义
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class Company(BaseModel):
    """公司模型"""
    id: str
    name: str
    code: Optional[str] = None
    industry: Optional[str] = None
    market: Optional[str] = None  # A股、港股、美股


class FinancialIndicator(BaseModel):
    """财务指标模型"""
    id: str
    name: str
    value: float
    unit: str
    period: str  # 如 "2023Q3"
    company_id: str


class Report(BaseModel):
    """财报模型"""
    id: str
    company_id: str
    year: int
    quarter: Optional[int] = None
    report_type: str  # annual, quarterly, semi-annual
    file_path: Optional[str] = None
    upload_time: datetime
    status: str  # pending, processed, failed


class AnalysisResult(BaseModel):
    """分析结果模型"""
    id: str
    company_id: str
    indicator: str
    analysis_type: str  # trend, attribution, risk, industry
    result: Dict[str, Any]
    created_at: datetime

