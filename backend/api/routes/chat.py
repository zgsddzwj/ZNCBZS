"""
对话式交互API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from backend.engine.coordinator import Coordinator
from backend.engine.coordinator import ConversationContext

router = APIRouter()


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # user, assistant, system
    content: str
    timestamp: Optional[float] = None


class ChatRequest(BaseModel):
    """对话请求"""
    message: str
    conversation_id: Optional[str] = None
    context: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    """对话响应"""
    response: str
    conversation_id: str
    context: List[ChatMessage]
    sources: Optional[List[dict]] = None  # 引用的知识来源


@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    """
    自然语言查询
    
    示例：
    - "贵州茅台2023年营收同比增长多少？"
    - "分析招商银行近三年不良率变化原因"
    """
    try:
        coordinator = Coordinator()
        
        # 构建对话上下文
        context = ConversationContext(
            conversation_id=request.conversation_id,
            history=request.context or [],
        )
        
        # 处理查询
        result = await coordinator.process_query(
            query=request.message,
            context=context,
        )
        
        return ChatResponse(
            response=result["answer"],
            conversation_id=result["conversation_id"],
            context=result["context"],
            sources=result.get("sources", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """获取对话历史"""
    try:
        coordinator = Coordinator()
        history = await coordinator.get_conversation_history(conversation_id)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{conversation_id}")
async def clear_conversation_history(conversation_id: str):
    """清空对话历史"""
    try:
        coordinator = Coordinator()
        await coordinator.clear_conversation_history(conversation_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

