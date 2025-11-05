"""
数据集成API路由
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from loguru import logger
from backend.core.auth import get_current_user, UserRole
from backend.services.data_integration_service import DataIntegrationService

router = APIRouter(prefix="/data-integration", tags=["数据集成"])

data_integration_service = DataIntegrationService()


class BankReportIntegrationRequest(BaseModel):
    """银行财报集成请求"""
    bank_names: Optional[List[str]] = None
    years: Optional[List[int]] = None
    report_types: Optional[List[str]] = None
    auto_import: bool = True


class MacroDataIntegrationRequest(BaseModel):
    """宏观经济数据集成请求"""
    indicators: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    auto_import: bool = True


class PolicyFileIntegrationRequest(BaseModel):
    """政策文件集成请求"""
    sources: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    auto_import: bool = True


class FullIntegrationRequest(BaseModel):
    """完整集成请求"""
    include_banks: bool = True
    include_macro: bool = True
    include_policies: bool = True


@router.post("/bank-reports", summary="集成银行财报数据")
async def integrate_bank_reports(
    request: BankReportIntegrationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    集成银行财报数据
    
    需要管理员或高级用户权限
    """
    # 检查权限
    if current_user.get("role") not in [UserRole.ADMIN, UserRole.SENIOR]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        # 异步执行（后台任务）
        result = await data_integration_service.integrate_bank_reports(
            bank_names=request.bank_names,
            years=request.years,
            report_types=request.report_types,
            auto_import=request.auto_import,
        )
        
        return {
            "success": True,
            "data": result,
        }
        
    except Exception as e:
        logger.error(f"银行财报集成失败: {e}")
        raise HTTPException(status_code=500, detail=f"集成失败：{str(e)}")


@router.post("/macro-data", summary="集成宏观经济数据")
async def integrate_macro_data(
    request: MacroDataIntegrationRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    集成宏观经济数据
    
    需要管理员或高级用户权限
    """
    # 检查权限
    if current_user.get("role") not in [UserRole.ADMIN, UserRole.SENIOR]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        result = await data_integration_service.integrate_macro_data(
            indicators=request.indicators,
            start_date=request.start_date,
            end_date=request.end_date,
            auto_import=request.auto_import,
        )
        
        return {
            "success": True,
            "data": result,
        }
        
    except Exception as e:
        logger.error(f"宏观经济数据集成失败: {e}")
        raise HTTPException(status_code=500, detail=f"集成失败：{str(e)}")


@router.post("/policy-files", summary="集成政策文件")
async def integrate_policy_files(
    request: PolicyFileIntegrationRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    集成政策文件
    
    需要管理员或高级用户权限
    """
    # 检查权限
    if current_user.get("role") not in [UserRole.ADMIN, UserRole.SENIOR]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        result = await data_integration_service.integrate_policy_files(
            sources=request.sources,
            start_date=request.start_date,
            end_date=request.end_date,
            auto_import=request.auto_import,
        )
        
        return {
            "success": True,
            "data": result,
        }
        
    except Exception as e:
        logger.error(f"政策文件集成失败: {e}")
        raise HTTPException(status_code=500, detail=f"集成失败：{str(e)}")


@router.post("/full", summary="完整数据集成")
async def full_integration(
    request: FullIntegrationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    完整数据集成（所有数据源）
    
    需要管理员权限
    """
    # 检查权限
    if current_user.get("role") != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        # 后台执行（可能耗时较长）
        result = await data_integration_service.full_integration(
            include_banks=request.include_banks,
            include_macro=request.include_macro,
            include_policies=request.include_policies,
        )
        
        return {
            "success": True,
            "data": result,
            "message": "数据集成已开始，请稍后查看状态",
        }
        
    except Exception as e:
        logger.error(f"完整数据集成失败: {e}")
        raise HTTPException(status_code=500, detail=f"集成失败：{str(e)}")


@router.get("/status", summary="获取数据集成状态")
async def get_integration_status(
    current_user: dict = Depends(get_current_user),
):
    """
    获取数据集成状态
    
    所有用户可访问
    """
    try:
        status = await data_integration_service.get_integration_status()
        
        return {
            "success": True,
            "data": status,
        }
        
    except Exception as e:
        logger.error(f"获取集成状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败：{str(e)}")

