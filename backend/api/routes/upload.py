"""
财报上传和解析API
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import Optional, Literal
from backend.data.processor import DocumentProcessor
from backend.core.auth import get_current_user

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


class UploadParams:
    """上传参数（依赖注入用）"""
    def __init__(
        self,
        company: Optional[str] = Field(None, max_length=100, description="公司名称"),
        year: Optional[int] = Field(None, ge=2000, le=2100, description="财报年份"),
        report_type: str = Field("annual", pattern="^(annual|quarterly|semi-annual)$", description="报告类型"),
    ):
        self.company = company
        self.year = year
        self.report_type = report_type


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
        file_ext = "." + file.filename.split(".")[-1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。支持格式：{', '.join(allowed_extensions)}"
            )

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
            filename=file.filename,
            status="success",
            extracted_data=extracted_data,
            message="文件解析成功",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败：{str(e)}")


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
        raise HTTPException(status_code=500, detail=f"查询状态失败: {str(e)}")
