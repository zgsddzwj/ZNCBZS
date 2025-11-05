"""
智能体API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from backend.services.agents import AgentManager
from backend.core.auth import get_current_user, require_role, UserRole

router = APIRouter()
agent_manager = AgentManager()


class AgentExecuteRequest(BaseModel):
    """智能体执行请求"""
    agent_id: str
    query: str
    context: Optional[Dict[str, Any]] = None


class CustomAgentRequest(BaseModel):
    """自定义智能体创建请求"""
    name: str
    description: str
    knowledge_base: Optional[str] = None
    capabilities: List[str] = []


@router.get("/list")
async def list_agents():
    """列出所有预置智能体"""
    agents = agent_manager.list_agents()
    return {"agents": agents}


@router.post("/execute")
async def execute_agent(
    request: AgentExecuteRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    执行智能体任务
    
    示例：
    - 波士顿矩阵：{"agent_id": "boston_matrix", "query": "", "context": {"products": [...]}}
    - SWOT分析：{"agent_id": "swot", "query": "分析某银行零售业务", "context": {...}}
    """
    try:
        agent = agent_manager.get_agent(request.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")
        
        result = await agent.execute(request.query, request.context)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.SENIOR))])
async def create_custom_agent(
    request: CustomAgentRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    创建自定义智能体（仅管理员和高级用户）
    
    流程：
    1. 命名与场景定义
    2. 知识库关联
    3. 功能配置
    4. 测试与上线
    """
    try:
        agent_id = await agent_manager.create_custom_agent(
            name=request.name,
            description=request.description,
            knowledge_base=request.knowledge_base,
            capabilities=request.capabilities,
        )
        
        return {
            "agent_id": agent_id,
            "message": "智能体创建成功",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}")
async def get_agent_info(agent_id: str):
    """获取智能体信息"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    return {
        "id": agent_id,
        "name": agent.name,
        "description": agent.description,
        "knowledge_base": agent.knowledge_base,
    }

