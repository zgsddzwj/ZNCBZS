"""
财报上传和解析API
"""
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, Literal
from backend.data.processor import DocumentProcessor
from backend.core.auth import get_current_user
from backend.core.config import settings

router = APIRouter(dependencies=[Depends(get_current_user)])


class UploadResponse(BaseModel):
    """上传响应"""
    file_id: str = Field(..., description="文件唯一ID")
    filename: str = Field(..., description="原始文件名")
    status: str = Field(..., description="处理状态: success/pending/failed")
    extracted_data: Optional[dict] = Field(None, description="提取的结构化数据")
    message: Optional[str] = Field(None, description="状态说明")


class ProcessingStatusResponse(BaseModel):
    """处理状态响应"""
    file_id: str = Field(..., description="文件ID")
    status: Literal["pending", "processing", "completed", "failed"] = Field(..., description="当前状态")
    progress: int = Field(..., ge=0, le=100, description="处理进度百分比")
    message: Optional[str] = Field(None, description="状态说明")


# 文件类型 magic bytes 签名
_FILE_SIGNATURES = {
    b"%PDF": ".pdf",
    b"PK\x03\x04": ".docx",  # ZIP-based (docx, xlsx)
    b"\xd0\xcf\x11\xe0": ".doc",  # OLE2 (doc, xls)
}


def _detect_file_type(content: bytes) -> Optional[str]:
    """通过 magic bytes 检测文件真实类型"""
    for signature, ext in _FILE_SIGNATURES.items():
        if content.startswith(signature):
            return ext
    return None


def _safe_filename(filename: str) -> str:
    """清理文件名，移除路径遍历字符"""
    # 只保留文件名部分
    filename = os.path.basename(filename)
    # 移除可疑字符
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")
    return filename


@router.post("/report", response_model=UploadResponse)
async def upload_report(
    file: UploadFile = File(..., description="财报文件(PDF/Word/Excel)"),
    company: Optional[str] = Field(None, max_length=100, description="公司名称"),
    year: Optional[int] = Field(None, ge=2000, le=2100, description="财报年份"),
    report_type: str = Field("annual", pattern="^(annual|quarterly|semi-annual)$", description="报告类型"),
):
    """
    上传并解析财报文件

    支持格式：PDF、Word、Excel
    """
    try:
        allowed_extensions = [".pdf", ".docx", ".doc", ".xlsx", ".xls"]

        # 安全提取扩展名
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        file_ext = os.path.splitext(file.filename or "")[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。支持格式：{', '.join(allowed_extensions)}"
            )

        # 读取文件内容并验证大小
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="文件过大，最大支持 100MB")

        # 验证文件真实类型 (magic bytes)
        detected_ext = _detect_file_type(content)
        if detected_ext and detected_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="文件内容与扩展名不匹配")

        # 清理文件名
        safe_name = _safe_filename(file.filename)

        # 重置文件指针以便后续处理
        await file.seek(0)

        processor = DocumentProcessor()
        file_info = await processor.save_uploaded_file(file)

        extracted_data = await processor.process_document(
            file_path=file_info["path"],
            file_type=file_ext,
            company=company,
            year=year,
            report_type=report_type,
        )

        return UploadResponse(
            file_id=file_info["file_id"],
            filename=safe_name,
            status="success",
            extracted_data=extracted_data,
            message="文件解析成功",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="文件处理失败，请稍后重试")


@router.get("/status/{file_id}", response_model=ProcessingStatusResponse)
async def get_upload_status(
    file_id: str = Field(..., min_length=1, description="文件ID"),
):
    """查询上传文件处理状态"""
    try:
        processor = DocumentProcessor()
        status = await processor.get_processing_status(file_id)
        return ProcessingStatusResponse(
            file_id=file_id,
            status=status.get("status", "pending"),
            progress=status.get("progress", 0),
            message=status.get("message"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="查询状态失败，请稍后重试")
