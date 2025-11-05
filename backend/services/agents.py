"""
智能体服务 - 预置智能体和自定义智能体
"""
from typing import Dict, Any, List, Optional
from loguru import logger
from backend.engine.llm_service import LLMService
from backend.data.storage import KnowledgeGraph, VectorStore


class Agent:
    """智能体基类"""
    
    def __init__(self, name: str, description: str, knowledge_base: Optional[str] = None):
        self.name = name
        self.description = description
        self.knowledge_base = knowledge_base
        self.llm_service = LLMService()
        self.knowledge_graph = KnowledgeGraph()
        self.vector_store = VectorStore()
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行智能体任务"""
        raise NotImplementedError


class BostonMatrixAgent(Agent):
    """波士顿矩阵助手"""
    
    def __init__(self):
        super().__init__(
            name="波士顿矩阵助手",
            description="自动生成波士顿矩阵图，划分业务类型并给出建议"
        )
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成波士顿矩阵分析
        
        输入格式：
        {
            "products": [
                {"name": "产品A", "market_growth": 15, "relative_share": 0.8},
                {"name": "产品B", "market_growth": 5, "relative_share": 1.2},
            ]
        }
        """
        try:
            products = context.get("products", []) if context else []
            
            # 分类业务
            classified = []
            for product in products:
                growth = product.get("market_growth", 0)
                share = product.get("relative_share", 0)
                
                if growth >= 10 and share >= 1.0:
                    category = "明星业务"
                    suggestion = "加大投资，保持竞争优势"
                elif growth < 10 and share >= 1.0:
                    category = "现金牛业务"
                    suggestion = "维持现状，获取现金流"
                elif growth >= 10 and share < 1.0:
                    category = "问题业务"
                    suggestion = "评估投资价值，考虑放弃或加大投入"
                else:
                    category = "瘦狗业务"
                    suggestion = "考虑退出或转型"
                
                classified.append({
                    **product,
                    "category": category,
                    "suggestion": suggestion,
                })
            
            # 生成分析报告
            prompt = f"""
基于以下波士顿矩阵分析结果，生成详细的分析报告：

{classified}

要求：
1. 总结各业务类型的特点
2. 给出整体业务组合建议
3. 识别需要关注的业务
"""
            
            analysis = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1000,
            )
            
            return {
                "matrix_data": classified,
                "analysis": analysis,
                "chart_config": self._generate_chart_config(classified),
            }
            
        except Exception as e:
            logger.error(f"波士顿矩阵分析失败: {e}")
            raise
    
    def _generate_chart_config(self, classified: List[Dict]) -> Dict:
        """生成图表配置"""
        return {
            "type": "scatter",
            "data": [
                {
                    "name": item["name"],
                    "value": [item["market_growth"], item["relative_share"]],
                    "category": item["category"],
                }
                for item in classified
            ],
        }


class SWOTAgent(Agent):
    """SWOT分析助手"""
    
    def __init__(self):
        super().__init__(
            name="SWOT分析助手",
            description="自动生成SWOT分析表及战略建议"
        )
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成SWOT分析"""
        try:
            entity_info = context.get("entity_info", "") if context else query
            
            prompt = f"""
对以下企业/业务线进行SWOT分析：

{entity_info}

请从知识库中提取相关信息，生成：
1. Strengths（优势）
2. Weaknesses（劣势）
3. Opportunities（机会）
4. Threats（威胁）
5. 战略建议

返回JSON格式。
"""
            
            # 检索相关知识
            from backend.engine.retrieval import RetrievalEngine
            retrieval = RetrievalEngine()
            docs = await retrieval.retrieve(query=entity_info, top_k=10)
            
            knowledge_text = "\n".join([d.get("content", "")[:500] for d in docs[:5]])
            prompt += f"\n\n相关知识：\n{knowledge_text}"
            
            analysis = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2000,
            )
            
            return {
                "swot_analysis": analysis,
                "sources": [{"source": d.get("source", "")} for d in docs[:3]],
            }
            
        except Exception as e:
            logger.error(f"SWOT分析失败: {e}")
            raise


class CreditQAAgent(Agent):
    """信贷问答助手"""
    
    def __init__(self):
        super().__init__(
            name="信贷问答助手",
            description="解答信贷业务相关问题"
        )
        # 关联信贷知识库
        self.knowledge_base = "credit_policy"
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """回答信贷相关问题"""
        try:
            # 检索信贷政策知识
            from backend.engine.retrieval import RetrievalEngine
            retrieval = RetrievalEngine()
            docs = await retrieval.retrieve(
                query=query,
                top_k=10,
                filters={"knowledge_base": self.knowledge_base},
            )
            
            knowledge_text = "\n".join([d.get("content", "")[:500] for d in docs[:5]])
            
            prompt = f"""
你是专业的信贷业务助手。请基于以下信贷政策和监管要求回答问题：

知识库内容：
{knowledge_text}

问题：{query}

要求：
1. 回答准确，符合银行信贷政策
2. 引用具体的政策文件或规定
3. 如果涉及计算，提供计算步骤
4. 回答要专业、简洁
"""
            
            answer = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=1000,
            )
            
            return {
                "answer": answer,
                "sources": [{"source": d.get("source", "")} for d in docs[:3]],
            }
            
        except Exception as e:
            logger.error(f"信贷问答失败: {e}")
            raise


class RetailTransformationAgent(Agent):
    """零售转型助手"""
    
    def __init__(self):
        super().__init__(
            name="零售转型助手",
            description="提供银行零售业务转型相关分析"
        )
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """零售转型分析"""
        try:
            from backend.engine.retrieval import RetrievalEngine
            retrieval = RetrievalEngine()
            docs = await retrieval.retrieve(
                query=query,
                top_k=15,
                filters={"category": "retail_transformation"},
            )
            
            knowledge_text = "\n".join([d.get("content", "")[:500] for d in docs[:10]])
            
            prompt = f"""
基于以下零售转型知识和案例，回答用户问题：

知识库：
{knowledge_text}

问题：{query}

要求：
1. 提供具体的转型策略建议
2. 引用同业成功案例
3. 分析数字化获客渠道
4. 提供产品创新建议
"""
            
            answer = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2000,
            )
            
            return {
                "answer": answer,
                "cases": [{"title": d.get("title", ""), "source": d.get("source", "")} for d in docs[:5]],
            }
            
        except Exception as e:
            logger.error(f"零售转型分析失败: {e}")
            raise


class DocumentWritingAgent(Agent):
    """公文写作助手"""
    
    def __init__(self):
        super().__init__(
            name="公文写作助手",
            description="支持银行内部公文撰写"
        )
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成公文"""
        try:
            doc_type = context.get("doc_type", "通知") if context else "通知"
            content_info = context.get("content_info", {}) if context else {}
            
            # 加载公文模板
            templates = {
                "通知": """
关于{title}的通知

各部门：

{content}

特此通知。

{organization}
{date}
""",
                "请示": """
关于{title}的请示

{recipient}：

{content}

请批示。

{organization}
{date}
""",
                "报告": """
{title}报告

{recipient}：

{content}

{organization}
{date}
""",
            }
            
            template = templates.get(doc_type, templates["通知"])
            
            # 使用LLM优化内容
            prompt = f"""
基于以下信息，生成符合银行公文格式规范的{doc_type}：

信息：
{content_info}

要求：
1. 符合银行公文格式（字体、行距、落款）
2. 语言正式、严谨
3. 逻辑清晰
4. 完整填写模板中的占位符
"""
            
            draft = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=2000,
            )
            
            return {
                "doc_type": doc_type,
                "draft": draft,
                "template_used": template,
            }
            
        except Exception as e:
            logger.error(f"公文生成失败: {e}")
            raise


class AgentManager:
    """智能体管理器"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {
            "boston_matrix": BostonMatrixAgent(),
            "swot": SWOTAgent(),
            "credit_qa": CreditQAAgent(),
            "retail_transformation": RetailTransformationAgent(),
            "document_writing": DocumentWritingAgent(),
        }
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取智能体"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有智能体"""
        return [
            {
                "id": agent_id,
                "name": agent.name,
                "description": agent.description,
            }
            for agent_id, agent in self.agents.items()
        ]
    
    async def create_custom_agent(
        self,
        name: str,
        description: str,
        knowledge_base: Optional[str] = None,
        capabilities: List[str] = None,
    ) -> str:
        """创建自定义智能体"""
        # 生成智能体ID
        agent_id = f"custom_{len(self.agents)}"
        
        # 创建自定义智能体
        class CustomAgent(Agent):
            def __init__(self, name, description, knowledge_base, capabilities):
                super().__init__(name, description, knowledge_base)
                self.capabilities = capabilities or []
        
        self.agents[agent_id] = CustomAgent(name, description, knowledge_base, capabilities)
        
        return agent_id

