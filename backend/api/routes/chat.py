"""
对话式交互API
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from backend.engine.coordinator import Coordinator
from backend.engine.coordinator import ConversationContext
from backend.api.deps import get_coordinator

router = APIRouter()


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="消息角色: user, assistant, system")
    content: str = Field(..., min_length=1, max_length=10000, description="消息内容")
    timestamp: Optional[float] = Field(None, description="时间戳")


class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户输入的消息")
    conversation_id: Optional[str] = Field(None, description="对话ID，为空则创建新对话")
    context: Optional[List[ChatMessage]] = Field(None, description="历史消息上下文")


class SourceItem(BaseModel):
    """知识来源项"""
    source: str = Field("", description="来源名称")
    relevance: float = Field(0.0, ge=0, le=1, description="相关度分数")


class ChatResponse(BaseModel):
    """对话响应"""
    response: str = Field(..., description="AI回复内容")
    conversation_id: str = Field(..., description="对话ID")
    context: List[ChatMessage] = Field(default_factory=list, description="对话上下文")
    sources: List[SourceItem] = Field(default_factory=list, description="引用的知识来源")


class HistoryResponse(BaseModel):
    """历史记录响应"""
    history: List[dict] = Field(default_factory=list, description="消息历史列表")


class StatusResponse(BaseModel):
    """状态响应"""
    status: str = Field(..., description="操作状态")
    message: Optional[str] = Field(None, description="附加信息")


@router.post("/query", response_model=ChatResponse, summary="执行自然语言查询")
async def chat_query(
    request: ChatRequest, coordinator: Coordinator = Depends(get_coordinator)
):
    """
    自然语言查询

    示例：
    - "贵州茅台2023年营收同比增长多少？"
    - "分析招商银行近三年不良率变化原因"
    """
    try:
        context = ConversationContext(
            conversation_id=request.conversation_id,
            history=[msg.model_dump() for msg in (request.context or [])],
        )

        result = await coordinator.process_query(
            query=request.message,
            context=context,
        )

        sources = [
            SourceItem(source=s.get("source", ""), relevance=s.get("relevance", 0))
            for s in result.get("sources", [])
        ]

        return ChatResponse(
            response=result["answer"],
            conversation_id=result["conversation_id"],
            context=[ChatMessage(**m) for m in result.get("context", [])],
            sources=sources,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理查询失败: {str(e)}")


@router.get("/history/{conversation_id}", response_model=HistoryResponse, summary="获取指定对话的历史记录")
async def get_conversation_history(
    conversation_id: str = Field(..., min_length=1, description="对话ID"),
    coordinator: Coordinator = Depends(get_coordinator),
):
    """获取对话历史"""
    try:
        history = await coordinator.get_conversation_history(conversation_id)
        return HistoryResponse(history=history)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.delete("/history/{conversation_id}", response_model=StatusResponse, summary="清除指定对话的历史记录")
async def clear_conversation_history(
    conversation_id: str = Field(..., min_length=1, description="对话ID"),
    coordinator: Coordinator = Depends(get_coordinator),
):
    """清除指定对话的上下文"""
    try:
        await coordinator.clear_conversation_history(conversation_id)
        return StatusResponse(status="success", message="对话历史已清除")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除历史记录失败: {str(e)}")
