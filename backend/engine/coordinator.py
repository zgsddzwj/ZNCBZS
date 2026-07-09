"""
协同引擎 - 任务调度和流程控制
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json
from loguru import logger

from backend.engine.llm_service import LLMService
from backend.engine.retrieval import RetrievalEngine
from backend.core.prompt_security import build_safe_prompt, sanitize_user_input
from backend.core.config import settings

# 尝试导入 Redis，不可用时回退到内存
_redis_client = None
try:
    import redis
    _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    _redis_client.ping()
    logger.info("对话历史 Redis 连接成功")
except Exception as e:
    logger.warning(f"Redis 不可用，对话历史将存储在内存中: {e}")
    _redis_client = None

# 对话历史 TTL（24小时自动过期）
_CONVERSATION_TTL = 86400
_REDIS_KEY_PREFIX = "conversation:"


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
    
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        retrieval_engine: Optional[RetrievalEngine] = None,
    ):
        self.llm_service = llm_service or LLMService()
        self.retrieval_engine = retrieval_engine or RetrievalEngine()
        self.conversations: Dict[str, ConversationContext] = {}
        self._redis = _redis_client

    def _save_conversation(self, context: ConversationContext):
        """保存对话到 Redis（或回退到内存）"""
        if self._redis:
            key = f"{_REDIS_KEY_PREFIX}{context.conversation_id}"
            self._redis.setex(
                key,
                _CONVERSATION_TTL,
                json.dumps(context.history, ensure_ascii=False),
            )
        else:
            self.conversations[context.conversation_id] = context

    def _load_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """从 Redis（或内存）加载对话"""
        if self._redis:
            key = f"{_REDIS_KEY_PREFIX}{conversation_id}"
            data = self._redis.get(key)
            if data:
                return ConversationContext(
                    conversation_id=conversation_id,
                    history=json.loads(data),
                )
            return None
        else:
            return self.conversations.get(conversation_id)

    def _delete_conversation(self, conversation_id: str):
        """删除对话"""
        if self._redis:
            key = f"{_REDIS_KEY_PREFIX}{conversation_id}"
            self._redis.delete(key)
        else:
            self.conversations.pop(conversation_id, None)
    
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
            elif context.conversation_id:
                loaded = self._load_conversation(context.conversation_id)
                context = loaded or context
            
            # 保存上下文
            self._save_conversation(context)
            
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
            
            # 保存更新后的上下文
            self._save_conversation(context)
            
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
        system_instruction = """分析以下问题的意图和关键信息，请提取：
1. 意图类型（指标查询/对比分析/趋势分析/归因分析/风险分析）
2. 公司名称或代码
3. 时间范围（年份、季度）
4. 指标名称
5. 分析类型（同比/环比/绝对值）

以JSON格式返回。"""

        context_data = f"对话历史：\n{self._format_history(context.history[-3:])}"

        prompt = build_safe_prompt(
            system_instruction=system_instruction,
            user_input=query,
            context_data=context_data,
        )
        
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

        system_instruction = """你是一个专业的财务分析师助手。基于以下知识回答问题。
要求：
1. 回答准确、专业
2. 如果知识库中没有相关信息，明确说明
3. 回答简洁明了，控制在200字以内
4. 可以引用数据时，请提供具体数值"""

        context_data = f"知识库内容：\n{knowledge_text}\n\n对话历史：\n{context_text}"

        prompt = build_safe_prompt(
            system_instruction=system_instruction,
            user_input=query,
            context_data=context_data,
        )
        
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
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
            else:
                role = getattr(msg, "role", "user")
                content = getattr(msg, "content", "")
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)
    
    # 完整的A股上市银行列表（按匹配优先级排序，长的名称在前）
    _BANK_LIST: List[str] = [
        "工商银行", "建设银行", "农业银行", "中国银行", "交通银行",
        "招商银行", "浦发银行", "兴业银行", "民生银行", "光大银行",
        "华夏银行", "平安银行", "中信银行", "北京银行", "上海银行",
        "江苏银行", "宁波银行", "南京银行", "杭州银行", "成都银行",
        "长沙银行", "西安银行", "贵阳银行", "郑州银行", "青岛银行",
        "苏州银行", "厦门银行", "重庆银行", "齐鲁银行", "兰州银行",
        "瑞丰银行", "常熟银行", "张家港行", "江阴银行", "无锡银行",
        "苏农银行", "紫金银行", "青农商行", "渝农商行", "沪农商行",
        "邮储银行", "浙商银行",
    ]
    
    # 常见非银行上市公司
    _COMPANY_LIST: List[str] = [
        "贵州茅台", "五粮液", "中国移动", "中国平安", "比亚迪",
        "宁德时代", "腾讯控股", "阿里巴巴", "美团", "京东",
    ]
    
    # 完整的财务指标关键词映射
    _INDICATOR_MAP: Dict[str, List[str]] = {
        "营收": ["营业收入", "营业总收入", "主营业务收入", "营收合计"],
        "净利润": ["净利润", "归母净利润", "归属于母公司所有者的净利润"],
        "不良率": ["不良贷款率", "不良率", "NPL比率"],
        "ROE": ["净资产收益率", "ROE", "股东权益报酬率"],
        "拨备覆盖率": ["拨备覆盖率", "拨备"],
        "净息差": ["净息差", "NIM", "净利息收益率"],
        "总资产": ["总资产", "资产总计"],
        "总负债": ["总负债", "负债合计"],
        "资本充足率": ["资本充足率", "CAR"],
        "资产负债率": ["资产负债率", "杠杆率"],
        "流动比率": ["流动比率", "流动性比率"],
        "毛利率": ["毛利率", "毛利润率"],
    }
    
    def _extract_company(self, text: str) -> Optional[str]:
        """提取公司名称（基于完整银行列表 + 常见上市公司）"""
        # 按优先级遍历，长的名称先匹配避免短名误匹配
        for company in self._BANK_LIST + self._COMPANY_LIST:
            if company in text:
                return company
        return None
    
    def _extract_indicator(self, text: str) -> Optional[str]:
        """提取指标名称（支持多种别名映射）"""
        for standard_name, aliases in self._INDICATOR_MAP.items():
            for alias in aliases:
                if alias in text:
                    return standard_name
        return None
    
    def _extract_time(self, text: str) -> Optional[Dict[str, Any]]:
        """提取时间信息（支持年份、季度、半年度）"""
        import re
        result = {}
        
        # 提取年份
        year_match = re.search(r"20\d{2}", text)
        if year_match:
            result["year"] = int(year_match.group())
        
        # 提取季度
        quarter_match = re.search(r"第?[一二三四]季度|Q[1-4]", text)
        if quarter_match:
            quarter_map = {"一": 1, "二": 2, "三": 3, "四": 4,
                          "1": 1, "2": 2, "3": 3, "4": 4}
            q_text = quarter_match.group()
            for k, v in quarter_map.items():
                if k in q_text:
                    result["quarter"] = v
                    break
        
        # 判断是否为半年度/年度报告
        if "半年" in text or "中期" in text:
            result["period"] = "semi_annual"
        elif "年度" in text or "年报" in text:
            result["period"] = "annual"
        
        return result if result else None
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """获取对话历史"""
        context = self._load_conversation(conversation_id)
        if context:
            return context.history
        return []
    
    async def clear_conversation_history(self, conversation_id: str):
        """清空对话历史"""
        self._delete_conversation(conversation_id)

