# 智能财报助手 - Langchain使用文档

## 📋 目录
1. [Langchain使用情况](#langchain使用情况)
2. [为什么选择自定义实现](#为什么选择自定义实现)
3. [Langchain集成方案](#langchain集成方案)
4. [Langchain替代方案](#langchain替代方案)

---

## 一、Langchain使用情况

### 1.1 当前状态

**依赖情况**：
- ✅ `langchain==0.0.350`：已添加到requirements.txt
- ✅ `langchain-openai==0.0.2`：已添加
- ✅ `langchain-community==0.0.10`：已添加

**代码使用情况**：
- ❌ **当前未在代码中直接使用Langchain**
- ✅ 项目使用自定义实现的Coordinator和Agent系统

### 1.2 为什么预留Langchain依赖？

**原因**：
1. **未来扩展**：预留接口，方便后续集成
2. **工具链支持**：某些工具可能需要Langchain
3. **社区生态**：Langchain生态丰富，便于集成第三方工具

---

## 二、为什么选择自定义实现

### 2.1 技术选型对比

| 方案 | 优势 | 劣势 | 选择理由 |
|------|------|------|---------|
| **Langchain** | 生态丰富、工具多、社区活跃 | 抽象层次高、性能开销、学习成本 | 适合快速原型 |
| **自定义实现** | 性能好、可控性强、定制化 | 开发工作量大、需要维护 | ✅ **选择** |

### 2.2 选择自定义实现的原因

#### 1. 性能考虑
- **Langchain**：抽象层次高，性能开销较大
- **自定义实现**：直接调用API，性能更优，响应更快

#### 2. 定制化需求
- **金融领域特殊性**：需要深度定制金融场景逻辑
- **业务逻辑复杂**：协同引擎需要精细控制流程
- **Langchain**：通用框架，定制化成本高

#### 3. 架构设计
- **项目架构**：已采用分层架构，Langchain会增加复杂度
- **代码维护**：自定义实现更符合项目架构

#### 4. 异步支持
- **FastAPI异步**：项目大量使用async/await
- **Langchain**：异步支持不够完善
- **自定义实现**：原生异步支持

### 2.3 对比分析

**Langchain方案**：
```python
from langchain.agents import initialize_agent
from langchain.tools import Tool

# Langchain Agent
agent = initialize_agent(
    tools=[...],
    llm=llm,
    agent_type="zero-shot-react-description"
)
result = agent.run(query)
```

**自定义实现方案**：
```python
# 自定义Coordinator
coordinator = Coordinator()
result = await coordinator.process_query(query)
```

**优势**：
- ✅ 性能更好（直接调用，无中间层）
- ✅ 代码更清晰（符合项目架构）
- ✅ 易于调试和维护
- ✅ 异步支持完善

---

## 三、Langchain集成方案

### 3.1 如何集成Langchain（未来方案）

如果需要在项目中集成Langchain，可以采用以下方案：

#### 方案一：部分集成（推荐）

**集成范围**：
- 使用Langchain的工具链（Tools）
- 使用Langchain的文档加载器（Document Loaders）
- 保留自定义的Coordinator和Agent

**集成示例**：
```python
from langchain.tools import Tool
from langchain.agents import initialize_agent
from langchain.llms import OpenAI

# 定义工具
tools = [
    Tool(
        name="财报查询",
        func=lambda q: report_service.query(q),
        description="查询财报数据"
    ),
    Tool(
        name="指标计算",
        func=lambda q: analysis_service.calculate(q),
        description="计算财务指标"
    ),
]

# 创建Langchain Agent（作为工具）
langchain_agent = initialize_agent(
    tools=tools,
    llm=OpenAI(),
    agent_type="zero-shot-react-description"
)

# 在Coordinator中使用
class Coordinator:
    async def process_query(self, query: str):
        # 复杂任务使用Langchain Agent
        if self._is_complex_task(query):
            return await langchain_agent.arun(query)
        else:
            # 简单任务使用自定义流程
            return await self._custom_process(query)
```

#### 方案二：混合使用

**架构**：
```
自定义Coordinator（主流程）
    ↓
Langchain Tools（工具调用）
    ↓
自定义Agent（业务逻辑）
```

**优势**：
- 保留自定义架构的优势
- 利用Langchain的工具生态
- 渐进式迁移

### 3.2 Langchain组件使用

#### 1. 文档加载器（Document Loaders）

**用途**：加载财报PDF、政策文件等

**示例**：
```python
from langchain.document_loaders import PyPDFLoader, DirectoryLoader

# 加载PDF文档
loader = PyPDFLoader("report.pdf")
documents = loader.load()

# 批量加载
loader = DirectoryLoader("./reports", glob="*.pdf")
documents = loader.load()
```

#### 2. 文本分割器（Text Splitters）

**用途**：将长文档分割为chunks用于向量检索

**示例**：
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = splitter.split_documents(documents)
```

#### 3. 向量存储（Vector Stores）

**用途**：集成Langchain的向量存储接口

**示例**：
```python
from langchain.vectorstores import Milvus
from langchain.embeddings import OpenAIEmbeddings

vectorstore = Milvus.from_documents(
    documents=chunks,
    embedding=OpenAIEmbeddings(),
    connection_args={"host": "localhost", "port": "19530"}
)
```

#### 4. 检索器（Retrievers）

**用途**：RAG检索

**示例**：
```python
from langchain.chains import RetrievalQA

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever()
)

result = qa_chain.run("查询某银行不良率")
```

#### 5. 链（Chains）

**用途**：复杂任务链式调用

**示例**：
```python
from langchain.chains import LLMChain, SimpleSequentialChain

# 创建链
chain1 = LLMChain(llm=llm, prompt=prompt1)
chain2 = LLMChain(llm=llm, prompt=prompt2)

# 顺序链
overall_chain = SimpleSequentialChain(
    chains=[chain1, chain2],
    verbose=True
)

result = overall_chain.run(query)
```

#### 6. 工具（Tools）

**用途**：封装外部工具供Agent调用

**示例**：
```python
from langchain.tools import Tool

# 定义工具
report_tool = Tool(
    name="财报查询工具",
    func=lambda q: report_service.query(q),
    description="查询银行财报数据，输入：银行名称、年份、指标"
)

# 在Agent中使用
agent = initialize_agent(
    tools=[report_tool, ...],
    llm=llm
)
```

#### 7. 记忆（Memory）

**用途**：对话历史管理

**示例**：
```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

agent = initialize_agent(
    tools=tools,
    llm=llm,
    memory=memory
)
```

---

## 四、Langchain替代方案

### 4.1 当前实现 vs Langchain

| 功能 | 当前实现 | Langchain | 说明 |
|------|---------|----------|------|
| **任务调度** | Coordinator | AgentExecutor | 自定义实现，更灵活 |
| **Agent管理** | AgentManager | Agent | 自定义实现，更符合业务 |
| **RAG检索** | RetrievalEngine | RetrievalQA | 自定义实现，性能更好 |
| **文档处理** | DocumentProcessor | Document Loaders | 自定义实现，支持更多格式 |
| **向量存储** | VectorStore | Vector Stores | 直接使用Milvus，更高效 |
| **工具调用** | 自定义工具 | Tools | 自定义实现，集成更好 |

### 4.2 功能对比

#### 任务调度

**Langchain方式**：
```python
from langchain.agents import AgentExecutor, initialize_agent

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type="zero-shot-react-description"
)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
result = executor.run(query)
```

**自定义实现方式**：
```python
coordinator = Coordinator()
result = await coordinator.process_query(query)
```

**优势**：
- 异步支持更好
- 流程控制更精细
- 性能开销更小

#### RAG检索

**Langchain方式**：
```python
from langchain.chains import RetrievalQA
from langchain.vectorstores import Milvus

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever()
)
```

**自定义实现方式**：
```python
retrieval_engine = RetrievalEngine()
docs = await retrieval_engine.retrieve(
    query=query,
    top_k=10,
    use_hybrid=True
)
```

**优势**：
- 支持混合检索（向量+关键词）
- 支持Reranker重排序
- 异步性能更好

#### Agent管理

**Langchain方式**：
```python
from langchain.agents import Agent

class MyAgent(Agent):
    # 需要实现多个方法
    pass
```

**自定义实现方式**：
```python
class Agent:
    async def execute(self, query, context):
        # 只需实现一个方法
        pass
```

**优势**：
- 接口更简单
- 符合业务需求
- 易于扩展

---

## 五、何时使用Langchain

### 5.1 适合使用Langchain的场景

1. **快速原型开发**
   - 需要快速验证想法
   - Langchain工具丰富，开发速度快

2. **集成第三方工具**
   - 需要集成Langchain生态的工具
   - 如：Wikipedia、Google Search等

3. **标准化流程**
   - 任务流程标准化
   - 不需要深度定制

4. **文档处理**
   - 使用Langchain的文档加载器
   - 支持多种格式

### 5.2 不适合使用Langchain的场景

1. **性能要求高**
   - 需要毫秒级响应
   - 自定义实现性能更好

2. **深度定制需求**
   - 业务逻辑复杂
   - 需要精细控制

3. **异步优先**
   - 大量异步操作
   - Langchain异步支持不够完善

4. **已有成熟架构**
   - 项目架构已确定
   - 集成成本高

---

## 六、Langchain集成建议

### 6.1 渐进式集成策略

**阶段一**：使用Langchain工具（低风险）
- 使用文档加载器加载PDF
- 使用文本分割器处理文档
- 不影响核心架构

**阶段二**：部分功能迁移（中等风险）
- 使用Langchain的检索链
- 保留自定义Coordinator
- A/B测试对比效果

**阶段三**：全面集成（高风险）
- 完全迁移到Langchain
- 需要大量测试和验证

### 6.2 混合使用方案（推荐）

**架构设计**：
```
用户请求
    ↓
Coordinator（自定义，主流程）
    ↓
    ├─→ 简单任务：自定义处理
    ├─→ 复杂任务：Langchain Agent
    └─→ 工具调用：Langchain Tools
```

**优势**：
- 保留自定义架构优势
- 利用Langchain生态
- 渐进式迁移
- 风险可控

---

## 七、代码示例

### 7.1 使用Langchain工具

```python
from langchain.tools import Tool
from backend.services.report_service import ReportService

# 创建财报查询工具
report_service = ReportService()

report_tool = Tool(
    name="财报查询",
    func=lambda q: report_service.query(q),
    description="查询银行财报数据"
)

# 在Agent中使用
from langchain.agents import initialize_agent

agent = initialize_agent(
    tools=[report_tool],
    llm=llm,
    agent_type="zero-shot-react-description"
)
```

### 7.2 使用Langchain文档加载

```python
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 加载PDF
loader = PyPDFLoader("report.pdf")
documents = loader.load()

# 分割文档
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = splitter.split_documents(documents)

# 导入到向量数据库
from backend.data.import_service import DataImportService
import_service = DataImportService()
await import_service.import_text_to_vector(chunks)
```

### 7.3 使用Langchain检索链

```python
from langchain.chains import RetrievalQA
from langchain.vectorstores import Milvus

# 创建检索链
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(),
    return_source_documents=True
)

# 在Coordinator中使用
class Coordinator:
    async def process_query(self, query: str):
        # 简单查询使用自定义实现
        if self._is_simple_query(query):
            return await self._custom_retrieve(query)
        
        # 复杂查询使用Langchain
        else:
            result = qa_chain({"query": query})
            return result
```

---

## 八、总结

### 8.1 当前状态

- ✅ **依赖已添加**：Langchain已添加到requirements.txt
- ❌ **代码未使用**：当前使用自定义实现
- ✅ **预留接口**：架构支持未来集成

### 8.2 选择理由

1. **性能优先**：自定义实现性能更好
2. **定制化需求**：金融领域需要深度定制
3. **架构一致**：符合项目分层架构
4. **异步支持**：原生异步支持更好

### 8.3 未来规划

1. **渐进式集成**：逐步引入Langchain工具
2. **混合使用**：保留自定义架构，利用Langchain生态
3. **A/B测试**：对比Langchain和自定义实现效果

### 8.4 面试回答要点

**问题**：为什么没有使用Langchain？

**回答要点**：
1. **性能考虑**：自定义实现性能更好，响应更快
2. **定制化需求**：金融领域需要深度定制，Langchain通用框架难以满足
3. **架构设计**：项目采用分层架构，自定义实现更符合架构
4. **异步支持**：项目大量使用async/await，自定义实现异步支持更好
5. **预留接口**：已在依赖中添加Langchain，支持未来集成
6. **混合使用**：可以在特定场景使用Langchain工具，如文档加载器

---

## 📚 相关文档

- [项目架构文档](./INTERVIEW_01_项目架构.md)
- [模型微调文档](./INTERVIEW_02_模型微调.md)
- [多Agent协调文档](./INTERVIEW_03_多Agent协调.md)

