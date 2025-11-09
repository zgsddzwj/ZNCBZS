# 智能财报助手 - 多Agent协调文档

## 📋 目录
1. [Agent架构设计](#agent架构设计)
2. [Agent类型和功能](#agent类型和功能)
3. [Agent协调机制](#agent协调机制)
4. [Agent执行流程](#agent执行流程)
5. [自定义Agent](#自定义agent)

---

## 一、Agent架构设计

### 1.1 Agent设计理念

**定义**：智能体（Agent）是封装了特定业务逻辑和知识库的独立模块，能够完成特定领域的任务。

**设计原则**：
- **单一职责**：每个Agent专注于一个业务场景
- **知识增强**：每个Agent关联特定的知识库
- **可扩展性**：支持自定义Agent创建
- **可组合性**：多个Agent可以协作完成复杂任务

### 1.2 Agent架构

```
┌─────────────────────────────────────────┐
│         AgentManager (管理器)          │
│  - Agent注册和发现                      │
│  - Agent调度和协调                      │
│  - 自定义Agent创建                      │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│         Agent基类 (抽象层)              │
│  - 统一接口 (execute)                   │
│  - 知识库访问                           │
│  - LLM服务调用                          │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│      具体Agent实现 (预置智能体)          │
│  - BostonMatrixAgent                    │
│  - SWOTAgent                            │
│  - CreditQAAgent                         │
│  - RetailTransformationAgent             │
│  - DocumentWritingAgent                 │
└─────────────────────────────────────────┘
```

### 1.3 核心组件

**位置**：`backend/services/agents.py`

**核心类**：
- `Agent`：智能体基类
- `AgentManager`：智能体管理器
- 各种具体Agent实现类

---

## 二、Agent类型和功能

### 2.1 预置智能体列表

| Agent ID | 名称 | 功能描述 | 应用场景 |
|----------|------|---------|---------|
| `boston_matrix` | 波士顿矩阵助手 | 生成波士顿矩阵图，划分业务类型 | 业务组合分析 |
| `swot` | SWOT分析助手 | 生成SWOT分析表及战略建议 | 战略规划 |
| `credit_qa` | 信贷问答助手 | 解答信贷业务相关问题 | 信贷业务咨询 |
| `retail_transformation` | 零售转型助手 | 提供零售业务转型分析 | 零售业务转型 |
| `document_writing` | 公文写作助手 | 生成银行内部公文 | 公文撰写 |

### 2.2 波士顿矩阵助手（BostonMatrixAgent）

**功能**：
- 自动生成波士顿矩阵图
- 划分业务类型（明星、现金牛、问题、瘦狗）
- 给出业务调整建议

**输入格式**：
```json
{
    "products": [
        {
            "name": "产品A",
            "market_growth": 15,      // 市场增长率（%）
            "relative_share": 0.8     // 相对市场份额
        }
    ]
}
```

**输出格式**：
```json
{
    "matrix_data": [
        {
            "name": "产品A",
            "market_growth": 15,
            "relative_share": 0.8,
            "category": "明星业务",
            "suggestion": "加大投资，保持竞争优势"
        }
    ],
    "analysis": "分析报告...",
    "chart_config": {...}
}
```

**分类规则**：
- **明星业务**：增长率≥10% 且 市场份额≥1.0
- **现金牛业务**：增长率<10% 且 市场份额≥1.0
- **问题业务**：增长率≥10% 且 市场份额<1.0
- **瘦狗业务**：增长率<10% 且 市场份额<1.0

### 2.3 SWOT分析助手（SWOTAgent）

**功能**：
- 从知识库中提取企业/业务线信息
- 自动生成SWOT分析（优势、劣势、机会、威胁）
- 提供战略建议

**工作流程**：
```
输入企业/业务信息
    ↓
检索相关知识（知识图谱 + 向量数据库）
    ↓
LLM提取SWOT要素
    ↓
生成结构化分析报告
```

**输出格式**：
```json
{
    "swot_analysis": {
        "strengths": ["优势1", "优势2"],
        "weaknesses": ["劣势1", "劣势2"],
        "opportunities": ["机会1", "机会2"],
        "threats": ["威胁1", "威胁2"],
        "strategies": ["战略建议1", "战略建议2"]
    },
    "sources": [...]
}
```

### 2.4 信贷问答助手（CreditQAAgent）

**功能**：
- 解答信贷业务相关问题
- 基于信贷政策和监管要求
- 提供准确、合规的回答

**知识库**：
- 信贷政策文件
- 监管要求
- 业务规则
- 计算标准

**示例问题**：
- "企业申请流动资金贷款的条件是什么？"
- "抵押物评估标准是什么？"
- "贷后风险监控指标有哪些？"

### 2.5 零售转型助手（RetailTransformationAgent）

**功能**：
- 提供零售业务转型策略
- 分析同业转型案例
- 数字化获客渠道对比
- 产品创新建议

**知识库**：
- 零售转型案例
- 数字化工具和渠道
- 产品创新案例
- 行业最佳实践

### 2.6 公文写作助手（DocumentWritingAgent）

**功能**：
- 生成银行内部公文
- 支持通知、请示、报告等类型
- 符合公文格式规范

**支持的公文类型**：
- 通知
- 请示
- 报告

**模板机制**：
- 预置标准化模板
- LLM优化内容
- 自动填充占位符

---

## 三、Agent协调机制

### 3.1 AgentManager（管理器）

**位置**：`backend/services/agents.py`

**核心功能**：
1. **Agent注册和发现**
   - 管理所有预置Agent
   - 支持Agent查询和获取

2. **Agent调度**
   - 根据用户意图选择合适的Agent
   - 支持多Agent协作

3. **自定义Agent创建**
   - 支持用户创建自定义Agent
   - 配置Agent的知识库和能力

**关键方法**：
```python
class AgentManager:
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取指定的Agent"""
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有可用的Agent"""
    
    async def create_custom_agent(
        self,
        name: str,
        description: str,
        knowledge_base: Optional[str] = None,
        capabilities: List[str] = None,
    ) -> str:
        """创建自定义Agent"""
```

### 3.2 Agent基类设计

**核心接口**：
```python
class Agent:
    """智能体基类"""
    
    def __init__(
        self,
        name: str,
        description: str,
        knowledge_base: Optional[str] = None
    ):
        self.name = name
        self.description = description
        self.knowledge_base = knowledge_base
        self.llm_service = LLMService()
        self.knowledge_graph = KnowledgeGraph()
        self.vector_store = VectorStore()
    
    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行Agent任务（子类必须实现）"""
        raise NotImplementedError
```

**设计特点**：
- **统一接口**：所有Agent实现相同的`execute`方法
- **知识库访问**：每个Agent可以访问自己的知识库
- **LLM服务**：共享LLM服务，但可以配置不同的提示词

### 3.3 Agent选择策略

**自动选择逻辑**：
```python
def select_agent(query: str, context: Dict) -> str:
    """根据查询内容自动选择Agent"""
    
    # 1. 关键词匹配
    if "波士顿矩阵" in query or "BCG" in query:
        return "boston_matrix"
    
    if "SWOT" in query or "优势劣势" in query:
        return "swot"
    
    if "信贷" in query or "贷款" in query:
        return "credit_qa"
    
    # 2. 使用LLM判断
    intent = llm_service.analyze_intent(query)
    if intent == "业务分析":
        return "boston_matrix"
    elif intent == "战略分析":
        return "swot"
    # ...
```

### 3.4 多Agent协作

**场景**：复杂任务需要多个Agent协作

**示例**：生成完整的业务分析报告
```
1. SWOTAgent → 分析企业优劣势
2. BostonMatrixAgent → 分析业务组合
3. RetailTransformationAgent → 提供转型建议
4. ReportGenerator → 整合生成报告
```

**协调机制**：
```python
async def multi_agent_execution(
    query: str,
    agent_sequence: List[str]
) -> Dict[str, Any]:
    """多Agent协作执行"""
    
    results = {}
    context = {}
    
    for agent_id in agent_sequence:
        agent = agent_manager.get_agent(agent_id)
        result = await agent.execute(query, context)
        results[agent_id] = result
        context.update(result)  # 更新上下文
    
    return results
```

---

## 四、Agent执行流程

### 4.1 单Agent执行流程

```
用户请求
    ↓
AgentManager选择Agent
    ↓
Agent.execute()
    ↓
知识检索（如需要）
    ↓
LLM生成/计算处理
    ↓
结果格式化
    ↓
返回结果
```

### 4.2 详细执行流程（以SWOTAgent为例）

```python
async def execute(self, query: str, context: Dict) -> Dict:
    # 1. 提取实体信息
    entity_info = context.get("entity_info", query)
    
    # 2. 检索相关知识
    retrieval = RetrievalEngine()
    docs = await retrieval.retrieve(
        query=entity_info,
        top_k=10,
        filters={"category": "swot"}
    )
    
    # 3. 构建提示词
    knowledge_text = "\n".join([d["content"] for d in docs])
    prompt = f"""
    对以下企业进行SWOT分析：
    {entity_info}
    
    相关知识：
    {knowledge_text}
    
    请生成SWOT分析...
    """
    
    # 4. LLM生成分析
    analysis = await self.llm_service.generate(prompt)
    
    # 5. 返回结果
    return {
        "swot_analysis": analysis,
        "sources": docs
    }
```

### 4.3 Agent状态管理

**状态类型**：
- **空闲**：Agent未在执行任务
- **执行中**：Agent正在处理任务
- **已完成**：任务执行完成
- **错误**：执行过程中出现错误

**状态管理**：
```python
class Agent:
    def __init__(self):
        self.status = "idle"
        self.current_task = None
    
    async def execute(self, query: str):
        self.status = "executing"
        self.current_task = query
        try:
            result = await self._execute_internal(query)
            self.status = "completed"
            return result
        except Exception as e:
            self.status = "error"
            raise
```

---

## 五、自定义Agent

### 5.1 创建自定义Agent

**API接口**：`POST /api/v1/agents/create`

**请求格式**：
```json
{
    "name": "供应链金融分析助手",
    "description": "分析供应链金融客户风险",
    "knowledge_base": "supply_chain_finance",
    "capabilities": ["问答交互", "报告生成", "数据查询"]
}
```

**实现逻辑**：
```python
async def create_custom_agent(request):
    """创建自定义Agent"""
    
    # 1. 创建Agent类
    class CustomAgent(Agent):
        def __init__(self, name, description, knowledge_base, capabilities):
            super().__init__(name, description, knowledge_base)
            self.capabilities = capabilities
        
        async def execute(self, query, context):
            # 自定义执行逻辑
            # 可以调用知识库、LLM等
            pass
    
    # 2. 注册到AgentManager
    agent_id = agent_manager.create_custom_agent(
        name=request.name,
        description=request.description,
        knowledge_base=request.knowledge_base,
        capabilities=request.capabilities
    )
    
    return {"agent_id": agent_id}
```

### 5.2 自定义Agent配置

**配置项**：
- **名称和描述**：Agent的功能说明
- **知识库关联**：关联的知识库ID
- **能力配置**：支持的功能（问答、报告生成等）
- **提示词模板**：自定义提示词
- **输出格式**：定义输出数据结构

### 5.3 自定义Agent示例

**供应链金融分析助手**：
```python
class SupplyChainFinanceAgent(Agent):
    """供应链金融分析助手"""
    
    def __init__(self):
        super().__init__(
            name="供应链金融分析助手",
            description="分析供应链金融客户风险评估",
            knowledge_base="supply_chain_finance"
        )
    
    async def execute(self, query: str, context: Dict):
        # 1. 提取客户信息
        customer_info = context.get("customer_info", {})
        
        # 2. 检索供应链金融知识
        docs = await self.retrieve_knowledge(query)
        
        # 3. 风险评估
        risk_score = await self.assess_risk(customer_info)
        
        # 4. 生成分析报告
        report = await self.generate_report(customer_info, risk_score)
        
        return {
            "risk_score": risk_score,
            "analysis": report,
            "recommendations": [...]
        }
```

---

## 六、Agent与协同引擎的集成

### 6.1 Coordinator调用Agent

**集成方式**：
```python
class Coordinator:
    async def process_query(self, query: str):
        # 1. 理解意图
        intent = await self._understand_intent(query)
        
        # 2. 判断是否需要Agent
        if intent.get("type") == "agent_task":
            agent_id = intent.get("agent_id")
            agent = agent_manager.get_agent(agent_id)
            return await agent.execute(query, intent)
        
        # 3. 普通查询流程
        # ...
```

### 6.2 Agent作为工具

**设计**：Agent可以作为工具被协同引擎调用

**示例**：
```python
# 用户查询："分析某银行的业务组合"
# Coordinator流程：
# 1. 理解意图 → 需要业务分析
# 2. 调用BostonMatrixAgent
# 3. 整合结果
# 4. 返回分析报告
```

---

## 七、Agent性能优化

### 7.1 并发执行

**多Agent并发**：
```python
async def parallel_agent_execution(
    query: str,
    agent_ids: List[str]
) -> Dict[str, Any]:
    """并行执行多个Agent"""
    
    tasks = [
        agent_manager.get_agent(agent_id).execute(query)
        for agent_id in agent_ids
    ]
    
    results = await asyncio.gather(*tasks)
    return dict(zip(agent_ids, results))
```

### 7.2 结果缓存

**缓存策略**：
- 相同查询缓存Agent结果
- 缓存时间：1小时
- 缓存键：`agent:{agent_id}:{query_hash}`

### 7.3 错误处理和重试

**重试机制**：
```python
async def execute_with_retry(
    agent: Agent,
    query: str,
    max_retries: int = 3
):
    """带重试的Agent执行"""
    
    for attempt in range(max_retries):
        try:
            return await agent.execute(query)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

---

## 八、Agent使用示例

### 8.1 API调用示例

**使用波士顿矩阵助手**：
```bash
curl -X POST http://localhost:8000/api/v1/agents/execute \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "boston_matrix",
    "query": "分析以下业务组合",
    "context": {
      "products": [
        {"name": "零售贷款", "market_growth": 15, "relative_share": 0.8},
        {"name": "公司贷款", "market_growth": 5, "relative_share": 1.2}
      ]
    }
  }'
```

**使用SWOT分析助手**：
```bash
curl -X POST http://localhost:8000/api/v1/agents/execute \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "swot",
    "query": "分析招商银行的SWOT",
    "context": {
      "entity_info": "招商银行，零售业务为主"
    }
  }'
```

### 8.2 Python代码调用

```python
from backend.services.agents import AgentManager

manager = AgentManager()

# 获取Agent
agent = manager.get_agent("boston_matrix")

# 执行Agent
result = await agent.execute(
    query="分析业务组合",
    context={
        "products": [...]
    }
)

# 创建自定义Agent
agent_id = await manager.create_custom_agent(
    name="我的助手",
    description="自定义分析助手",
    knowledge_base="my_kb"
)
```

---

## 九、Agent设计模式

### 9.1 模板方法模式

**基类定义骨架**：
```python
class Agent:
    async def execute(self, query, context):
        # 1. 前置处理（模板方法）
        processed_query = self.preprocess(query)
        
        # 2. 执行任务（子类实现）
        result = await self.do_execute(processed_query, context)
        
        # 3. 后置处理（模板方法）
        return self.postprocess(result)
    
    def preprocess(self, query):
        """前置处理（可选重写）"""
        return query
    
    async def do_execute(self, query, context):
        """执行任务（子类必须实现）"""
        raise NotImplementedError
    
    def postprocess(self, result):
        """后置处理（可选重写）"""
        return result
```

### 9.2 策略模式

**不同Agent使用不同策略**：
- SWOTAgent：使用知识检索 + LLM生成策略
- BostonMatrixAgent：使用规则计算 + LLM优化策略
- CreditQAAgent：使用知识库检索 + 模板匹配策略

### 9.3 工厂模式

**AgentManager作为工厂**：
```python
class AgentManager:
    def create_agent(self, agent_type: str, config: Dict):
        """工厂方法创建Agent"""
        if agent_type == "boston_matrix":
            return BostonMatrixAgent()
        elif agent_type == "swot":
            return SWOTAgent()
        # ...
```

---

## 📚 相关文档

- [项目架构文档](./INTERVIEW_01_项目架构.md)
- [模型微调文档](./INTERVIEW_02_模型微调.md)
- [Langchain使用文档](./INTERVIEW_04_Langchain.md)

