"""
API路由模块
"""
from fastapi import APIRouter
from backend.api.routes import chat, report, analysis, upload, auth, agents, voice, data_integration

router = APIRouter()

# 注册各个路由模块
router.include_router(auth.router, prefix="/auth", tags=["认证授权"])
router.include_router(chat.router, prefix="/chat", tags=["对话"])
router.include_router(report.router, prefix="/reports", tags=["财报"])
router.include_router(analysis.router, prefix="/analysis", tags=["分析"])
router.include_router(upload.router, prefix="/upload", tags=["上传"])
router.include_router(agents.router, prefix="/agents", tags=["智能体"])
router.include_router(voice.router, prefix="/voice", tags=["语音交互"])
router.include_router(data_integration.router, tags=["数据集成"])

