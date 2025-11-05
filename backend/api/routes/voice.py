"""
语音交互API
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from typing import Optional
from backend.services.voice_service import VoiceService
from backend.core.auth import get_current_user

router = APIRouter()
voice_service = VoiceService()


class VoiceQueryResponse(BaseModel):
    """语音查询响应"""
    text: str  # 识别的文本
    response: str  # 回答文本
    audio: Optional[str] = None  # 回答音频（base64编码）


@router.post("/recognize")
async def recognize_speech(
    audio: UploadFile = File(...),
    language: str = "zh-CN",
    current_user: dict = Depends(get_current_user),
):
    """
    语音识别
    
    支持语言：
    - zh-CN: 普通话
    - zh-HK: 粤语
    - en-US: 英语
    """
    try:
        audio_data = await audio.read()
        text = await voice_service.recognize_speech(audio_data, language)
        
        return {"text": text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
async def synthesize_speech(
    text: str,
    language: str = "zh-CN",
    current_user: dict = Depends(get_current_user),
):
    """
    文本转语音
    
    返回音频文件（WAV格式）
    """
    try:
        audio_data = await voice_service.text_to_speech(text, language)
        
        from fastapi.responses import Response
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=speech.wav"},
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=VoiceQueryResponse)
async def voice_query(
    audio: UploadFile = File(...),
    language: str = "zh-CN",
    current_user: dict = Depends(get_current_user),
):
    """
    语音查询（识别 -> 处理 -> 合成）
    
    完整的语音交互流程
    """
    try:
        audio_data = await audio.read()
        result = await voice_service.process_voice_query(audio_data, language)
        
        return VoiceQueryResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

