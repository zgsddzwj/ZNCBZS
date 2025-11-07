"""
协同引擎 - 任务调度和流程控制（基于MCP架构）
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json
from loguru import logger

from backend.engine.llm_service import LLMService
from backend.engine.retrieval import RetrievalEngine
from backend.mcp.client import MCPClient


@dataclass
class ConversationContext:
    """对话上下文"""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    history: List[Dict[str, Any]] = field(default_factory=list)
    max_history: int = 10
    
    def add_message(self, role: str, content: str):
        """添加消息到历史"""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        # 保持历史记录在限制内
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history * 2:]


class Coordinator:
    """
    协同引擎 - 负责任务拆解、工具调用、上下文管理（基于MCP架构）
    
    使用MCP Client来调用工具和数据源，实现标准化的工具调用接口
    """
    
    def __init__(self, use_mcp: bool = True):
        """
        初始化协同引擎
        
        Args:
            use_mcp: 是否使用MCP架构（默认True）
        """
        self.llm_service = LLMService()
        self.retrieval_engine = RetrievalEngine()
        self.conversations: Dict[str, ConversationContext] = {}
        
        # MCP Client
        self.use_mcp = use_mcp
        self.mcp_client: Optional[MCPClient] = None
        if use_mcp:
            self.mcp_client = MCPClient()
            logger.info("已启用MCP架构")
    
    async def process_query(
        self,
        query: str,
        context: Optional[ConversationContext] = None,
    ) -> Dict[str, Any]:
        """
        处理用户查询
        
        流程：
        1. 理解用户意图
        2. 检索相关知识
        3. 生成回答
        4. 更新上下文
        """
        try:
            # 获取或创建对话上下文
            if context is None:
                context = ConversationContext()
            elif context.conversation_id in self.conversations:
                context = self.conversations[context.conversation_id]
            
            # 保存上下文
            self.conversations[context.conversation_id] = context
            
            # 添加用户消息
            context.add_message("user", query)
            
            # 1. 理解意图和提取实体
            intent_result = await self._understand_intent(query, context)
            
            # 2. 检索相关知识（优先使用MCP资源）
            if self.use_mcp and self.mcp_client:
                retrieved_docs = await self.mcp_client.search_knowledge(query, top_k=10)
            else:
                retrieved_docs = await self._retrieve_knowledge(
                    query=query,
                    intent=intent_result,
                )
            
            # 3. 判断是否需要调用工具
            tool_result = None
            if self.use_mcp and self.mcp_client:
                tool_result = await self._call_mcp_tools(query, intent_result, context)
            
            # 4. 生成回答
            answer = await self._generate_answer(
                query=query,
                context=context,
                retrieved_docs=retrieved_docs,
                intent=intent_result,
                tool_result=tool_result,
            )
            
            # 添加助手回复
            context.add_message("assistant", answer)
            
            result = {
                "answer": answer,
                "conversation_id": context.conversation_id,
                "context": context.history,
                "sources": [
                    {
                        "source": doc.get("source", ""),
                        "relevance": doc.get("score", 0),
                    }
                    for doc in retrieved_docs[:3]
                ],
            }
            
            # 添加工具调用结果
            if tool_result:
                result["tool_result"] = tool_result
            
            return result
            
        except Exception as e:
            logger.error(f"处理查询失败: {e}")
            raise
    
    async def _understand_intent(
        self,
        query: str,
        context: ConversationContext,
    ) -> Dict[str, Any]:
        """理解用户意图"""
        # 使用LLM提取意图和实体
        prompt = f"""
分析以下问题的意图和关键信息：
问题：{query}

对话历史：
{self._format_history(context.history[-3:])}

请提取：
1. 意图类型（指标查询/对比分析/趋势分析/归因分析/风险分析）
2. 公司名称或代码
3. 时间范围（年份、季度）
4. 指标名称
5. 分析类型（同比/环比/绝对值）

以JSON格式返回。
"""
        
        response = await self.llm_service.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=500,
        )
        
        # 解析响应（这里简化处理，实际应该用JSON解析）
        # 这里可以集成更复杂的意图识别模型
        intent_result = {
            "type": "query",  # 默认类型
            "company": self._extract_company(query),
            "indicator": self._extract_indicator(query),
            "time": self._extract_time(query),
        }
        
        return intent_result
    
    async def _retrieve_knowledge(
        self,
        query: str,
        intent: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """检索相关知识"""
        # 使用RAG检索
        docs = await self.retrieval_engine.retrieve(
            query=query,
            top_k=10,
            filters=intent,
        )
        return docs
    
    async def _call_mcp_tools(
        self,
        query: str,
        intent: Dict[str, Any],
        context: ConversationContext,
    ) -> Optional[Dict[str, Any]]:
        """
        根据意图调用MCP工具
        
        Args:
            query: 用户查询
            intent: 意图识别结果
            context: 对话上下文
            
        Returns:
            工具调用结果
        """
        if not self.mcp_client:
            return None
        
        try:
            # 使用LLM判断需要调用哪些工具
            tools = await self.mcp_client.list_tools()
            tools_description = "\n".join([
                f"- {tool['name']}: {tool['description']}"
                for tool in tools
            ])
            
            prompt = f"""
分析以下问题，判断需要调用哪些工具：

问题：{query}
意图：{intent}

可用工具：
{tools_description}

请返回JSON格式，包含：
1. tool_name: 工具名称
2. arguments: 工具参数（从问题中提取）

如果不需要调用工具，返回null。
"""
            
            response = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=500,
            )
            
            # 解析工具调用信息
            try:
                tool_call = json.loads(response)
                if tool_call and tool_call.get("tool_name"):
                    tool_name = tool_call["tool_name"]
                    arguments = tool_call.get("arguments", {})
                    
                    # 调用工具
                    result = await self.mcp_client.call_tool(tool_name, arguments)
                    logger.info(f"MCP工具调用成功: {tool_name}")
                    return {
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result,
                    }
            except json.JSONDecodeError:
                # 如果无法解析JSON，尝试基于意图直接调用
                return await self._call_tool_by_intent(intent)
            
        except Exception as e:
            logger.error(f"MCP工具调用失败: {e}")
            return None
    
    async def _call_tool_by_intent(self, intent: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        根据意图直接调用工具（备用方案）
        
        Args:
            intent: 意图识别结果
            
        Returns:
            工具调用结果
        """
        if not self.mcp_client:
            return None
        
        intent_type = intent.get("type", "")
        company = intent.get("company")
        indicator = intent.get("indicator")
        time_info = intent.get("time", {})
        year = time_info.get("year") if isinstance(time_info, dict) else None
        
        try:
            # 根据意图类型选择工具
            if intent_type == "query" and company and indicator and year:
                return {
                    "tool": "query_report_indicator",
                    "arguments": {
                        "company": company,
                        "indicator": indicator,
                        "year": year,
                    },
                    "result": await self.mcp_client.call_tool(
                        "query_report_indicator",
                        {
                            "company": company,
                            "indicator": indicator,
                            "year": year,
                        }
                    ),
                }
            
            elif intent_type == "compare" and company and indicator:
                # 对比分析
                return {
                    "tool": "compare_indicators",
                    "arguments": {
                        "companies": [company] if company else [],
                        "indicator": indicator,
                        "start_year": year - 2 if year else 2021,
                        "end_year": year if year else 2023,
                    },
                    "result": await self.mcp_client.call_tool(
                        "compare_indicators",
                        {
                            "companies": [company] if company else [],
                            "indicator": indicator,
                            "start_year": year - 2 if year else 2021,
                            "end_year": year if year else 2023,
                        }
                    ),
                }
            
            elif intent_type == "attribution" and company and indicator and year:
                return {
                    "tool": "analyze_attribution",
                    "arguments": {
                        "company": company,
                        "indicator": indicator,
                        "base_year": year - 1,
                        "target_year": year,
                    },
                    "result": await self.mcp_client.call_tool(
                        "analyze_attribution",
                        {
                            "company": company,
                            "indicator": indicator,
                            "base_year": year - 1,
                            "target_year": year,
                        }
                    ),
                }
            
        except Exception as e:
            logger.error(f"基于意图的工具调用失败: {e}")
        
        return None
    
    async def _generate_answer(
        self,
        query: str,
        context: ConversationContext,
        retrieved_docs: List[Dict[str, Any]],
        intent: Dict[str, Any],
        tool_result: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        生成回答
        
        Args:
            query: 用户查询
            context: 对话上下文
            retrieved_docs: 检索到的文档
            intent: 意图识别结果
            tool_result: 工具调用结果（可选）
        """
        # 构建提示词
        context_text = self._format_history(context.history[-5:])
        knowledge_text = "\n\n".join([
            f"来源：{doc.get('source', '')}\n内容：{doc.get('content', '')[:500]}"
            for doc in retrieved_docs[:5]
        ])
        
        # 添加工具调用结果
        tool_text = ""
        if tool_result:
            tool_text = f"""
工具调用结果：
工具：{tool_result.get('tool', '')}
结果：{json.dumps(tool_result.get('result', {}), ensure_ascii=False, indent=2)}
"""
        
        prompt = f"""
你是一个专业的财务分析师助手。基于以下知识回答问题。

知识库内容：
{knowledge_text}

{tool_text}

对话历史：
{context_text}

当前问题：{query}

请基于知识库内容和工具调用结果回答问题，要求：
1. 回答准确、专业
2. 如果知识库中没有相关信息，明确说明
3. 回答简洁明了，控制在200字以内
4. 可以引用数据时，请提供具体数值
5. 如果使用了工具，请引用工具的结果

回答：
"""
        
        answer = await self.llm_service.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1000,
        )
        
        return answer
    
    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """格式化对话历史"""
        formatted = []
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)
    
    def _extract_company(self, text: str) -> Optional[str]:
        """提取公司名称（简化版）"""
        # 这里应该使用NER模型或规则
        companies = ["贵州茅台", "招商银行", "工商银行", "建设银行", "中国银行"]
        for company in companies:
            if company in text:
                return company
        return None
    
    def _extract_indicator(self, text: str) -> Optional[str]:
        """提取指标名称（简化版）"""
        indicators = ["营收", "净利润", "不良率", "ROE", "拨备覆盖率", "净息差"]
        for indicator in indicators:
            if indicator in text:
                return indicator
        return None
    
    def _extract_time(self, text: str) -> Optional[Dict[str, Any]]:
        """提取时间信息（简化版）"""
        import re
        year_match = re.search(r"20\d{2}", text)
        if year_match:
            return {"year": int(year_match.group())}
        return None
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """获取对话历史"""
        if conversation_id in self.conversations:
            return self.conversations[conversation_id].history
        return []
    
    async def clear_conversation_history(self, conversation_id: str):
        """清空对话历史"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

