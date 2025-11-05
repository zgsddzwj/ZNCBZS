"""
财报上传和解析API
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from backend.data.processor import DocumentProcessor

router = APIRouter()


class UploadResponse(BaseModel):
    """上传响应"""
    file_id: str
    filename: str
    status: str
    extracted_data: Optional[dict] = None
    message: Optional[str] = None


@router.post("/report", response_model=UploadResponse)
async def upload_report(
    file: UploadFile = File(...),
    company: Optional[str] = None,
    year: Optional[int] = None,
    report_type: str = "annual",
):
    """
    上传并解析财报文件
    
    支持格式：PDF、Word、Excel
    """
    try:
        # 验证文件类型
        allowed_extensions = [".pdf", ".docx", ".doc", ".xlsx", ".xls"]
        file_ext = "." + file.filename.split(".")[-1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。支持格式：{', '.join(allowed_extensions)}"
            )
        
        # 保存文件
        processor = DocumentProcessor()
        file_info = await processor.save_uploaded_file(file)
        
        # 解析文件
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


@router.get("/status/{file_id}")
async def get_upload_status(file_id: str):
    """查询上传文件处理状态"""
    try:
        from backend.data.processor import DocumentProcessor
        
        processor = DocumentProcessor()
        status = await processor.get_processing_status(file_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

