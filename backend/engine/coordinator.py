"""
协同引擎 - 任务调度和流程控制
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from loguru import logger

from backend.engine.llm_service import LLMService
from backend.engine.retrieval import RetrievalEngine


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
    """协同引擎 - 负责任务拆解、工具调用、上下文管理"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.retrieval_engine = RetrievalEngine()
        self.conversations: Dict[str, ConversationContext] = {}
    
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
            
            # 2. 检索相关知识
            retrieved_docs = await self._retrieve_knowledge(
                query=query,
                intent=intent_result,
            )
            
            # 3. 生成回答
            answer = await self._generate_answer(
                query=query,
                context=context,
                retrieved_docs=retrieved_docs,
                intent=intent_result,
            )
            
            # 添加助手回复
            context.add_message("assistant", answer)
            
            return {
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
    
    async def _generate_answer(
        self,
        query: str,
        context: ConversationContext,
        retrieved_docs: List[Dict[str, Any]],
        intent: Dict[str, Any],
    ) -> str:
        """生成回答"""
        # 构建提示词
        context_text = self._format_history(context.history[-5:])
        knowledge_text = "\n\n".join([
            f"来源：{doc.get('source', '')}\n内容：{doc.get('content', '')[:500]}"
            for doc in retrieved_docs[:5]
        ])
        
        prompt = f"""
你是一个专业的财务分析师助手。基于以下知识回答问题。

知识库内容：
{knowledge_text}

对话历史：
{context_text}

当前问题：{query}

请基于知识库内容回答问题，要求：
1. 回答准确、专业
2. 如果知识库中没有相关信息，明确说明
3. 回答简洁明了，控制在200字以内
4. 可以引用数据时，请提供具体数值

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

