# 智能财报助手 - 项目架构文档

## 📋 目录
1. [整体架构设计](#整体架构设计)
2. [技术栈选型](#技术栈选型)
3. [分层架构详解](#分层架构详解)
4. [核心模块设计](#核心模块设计)
5. [数据流转流程](#数据流转流程)

---

## 一、整体架构设计

### 1.1 架构模式

采用**分层架构 + 微服务**的设计模式：

```
┌─────────────────────────────────────────────────┐
│              前端交互层 (Frontend)               │
│         React + Vite + Ant Design               │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│              API网关层 (API Gateway)            │
│         FastAPI + JWT认证 + 权限控制             │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│              应用服务层 (Services)               │
│  财报服务 | 分析服务 | 报告生成 | 智能体服务    │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│              引擎层 (Engine)                    │
│  协同引擎 | 大模型服务 | 知识检索引擎 (RAG)     │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│              数据层 (Data)                      │
│  文档处理 | 数据存储 | 数据采集 | 数据清洗      │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│              存储层 (Storage)                   │
│  Neo4j | Milvus | Redis | SQLite/PostgreSQL    │
└─────────────────────────────────────────────────┘
```

### 1.2 三层架构核心

#### 数据层（Data Layer）
- **职责**：数据采集、清洗、存储、检索
- **核心组件**：
  - `DocumentProcessor`：文档解析（PDF/Word/Excel）
  - `DataCollector`：数据采集（财报、宏观、政策）
  - `DataCleaner`：数据清洗和标准化
  - `VectorStore`：向量数据库接口（Milvus/FAISS）
  - `KnowledgeGraph`：知识图谱接口（Neo4j）

#### 引擎层（Engine Layer）
- **职责**：任务调度、模型推理、知识检索
- **核心组件**：
  - `Coordinator`：协同引擎（任务拆解、工具调用、上下文管理）
  - `LLMService`：大模型服务（OpenAI/DeepSeek/微调模型）
  - `RetrievalEngine`：知识检索引擎（RAG技术）

#### 应用层（Application Layer）
- **职责**：业务逻辑实现、API接口
- **核心组件**：
  - `ReportService`：财报查询服务
  - `AnalysisService`：深度分析服务（归因、风险、趋势）
  - `ReportGenerator`：报告生成服务
  - `AgentManager`：智能体管理服务

---

## 二、技术栈选型

### 2.1 后端技术栈

| 技术 | 版本 | 用途 | 选型理由 |
|------|------|------|---------|
| **FastAPI** | 0.104.1 | Web框架 | 高性能、异步支持、自动API文档 |
| **Python** | 3.10+ | 编程语言 | AI生态丰富、开发效率高 |
| **Uvicorn** | 0.24.0 | ASGI服务器 | 高性能异步服务器 |
| **Pydantic** | 2.5.0 | 数据验证 | 类型安全、自动验证 |
| **SQLAlchemy** | 2.0.23 | ORM | 数据库抽象层 |
| **Alembic** | 1.12.1 | 数据库迁移 | 版本控制数据库schema |

### 2.2 大模型技术栈

| 技术 | 用途 | 说明 |
|------|------|------|
| **OpenAI API** | GPT-4-turbo | 通用推理、文本生成 |
| **DeepSeek API** | DeepSeek-Chat | 长文本处理、专业推理 |
| **LoRA微调** | 金融领域微调 | 基于PEFT库的轻量化微调 |
| **Transformers** | 模型加载 | Hugging Face模型库 |

### 2.3 数据存储技术栈

| 技术 | 用途 | 选型理由 |
|------|------|---------|
| **Neo4j** | 知识图谱 | 图数据库，适合关系查询 |
| **Milvus** | 向量数据库 | 高性能向量检索，支持大规模 |
| **FAISS** | 向量检索备选 | 本地向量检索，轻量级 |
| **Redis** | 缓存 | 高频数据缓存、会话管理 |
| **SQLite/PostgreSQL** | 关系数据库 | 元数据存储、用户数据 |

### 2.4 前端技术栈

| 技术 | 用途 |
|------|------|
| **React** | UI框架 |
| **Vite** | 构建工具 |
| **Ant Design** | UI组件库 |
| **ECharts** | 图表可视化 |
| **Axios** | HTTP客户端 |

### 2.5 部署和运维

| 技术 | 用途 |
|------|------|
| **Docker** | 容器化 |
| **Docker Compose** | 服务编排 |
| **Nginx** | 反向代理（可选） |

---

## 三、分层架构详解

### 3.1 API层（`backend/api/routes/`）

**职责**：HTTP接口定义、请求验证、权限控制

**模块划分**：
- `auth.py`：认证授权（注册、登录、JWT）
- `chat.py`：对话查询接口
- `report.py`：财报查询接口
- `analysis.py`：深度分析接口
- `upload.py`：文件上传接口
- `agents.py`：智能体接口
- `voice.py`：语音交互接口
- `data_integration.py`：数据集成接口

**设计特点**：
- RESTful API设计
- Pydantic模型验证
- 统一的错误处理
- JWT Token认证

**示例代码**：
```python
@router.post("/query")
async def chat_query(request: ChatRequest):
    """对话查询接口"""
    coordinator = Coordinator()
    result = await coordinator.process_query(
        query=request.message,
        context=request.context
    )
    return ChatResponse(**result)
```

### 3.2 服务层（`backend/services/`）

**职责**：业务逻辑实现、服务编排

**核心服务**：

#### ReportService（财报服务）
- 财报数据查询
- 指标提取和计算
- 跨期/跨公司对比

#### AnalysisService（分析服务）
- 指标波动归因分析
- 风险预警检测
- 行业对标分析
- 趋势预测

#### ReportGenerator（报告生成服务）
- 报告模板管理
- 内容生成（LLM）
- 图表生成
- 多格式导出（PDF/Word/Excel）

#### AgentManager（智能体管理）
- 预置智能体管理
- 自定义智能体创建
- 智能体执行调度

### 3.3 引擎层（`backend/engine/`）

#### Coordinator（协同引擎）

**核心职责**：
1. **任务拆解**：理解用户意图，拆解为子任务
2. **工具调用**：根据任务类型调用相应工具
3. **上下文管理**：维护对话历史和多轮对话
4. **流程调度**：协调各模块完成复杂任务

**工作流程**：
```
用户查询 
  → 意图理解（提取实体、意图类型）
  → 知识检索（RAG检索相关知识）
  → 工具调用（指标计算、分析等）
  → 生成回答（LLM生成）
  → 更新上下文
```

**关键设计**：
- 异步处理（async/await）
- 上下文持久化（内存存储，可扩展为Redis）
- 错误处理和重试机制

#### LLMService（大模型服务）

**功能**：
- 封装OpenAI/DeepSeek API调用
- LoRA微调模型加载和推理
- 模型切换逻辑（API模型 vs 微调模型）
- 文本嵌入生成（用于向量检索）

**设计特点**：
- 统一的模型接口
- 自动重试机制
- 异步并发支持

#### RetrievalEngine（知识检索引擎）

**RAG实现**：
1. **向量检索**：使用Milvus进行语义检索
2. **关键词检索**：基于Neo4j的知识图谱查询
3. **混合检索**：合并两种检索结果
4. **重排序**：使用BERT Reranker模型重排序

**检索流程**：
```
查询文本
  → 生成查询向量（LLM Embedding）
  → 向量检索（Milvus，Top-K）
  → 关键词检索（Neo4j，Top-K）
  → 合并去重
  → Reranker重排序
  → 返回Top-K结果
```

### 3.4 数据层（`backend/data/`）

#### DocumentProcessor（文档处理器）

**功能**：
- PDF解析（pdfplumber）
- Word解析（python-docx）
- Excel解析（pandas）
- OCR识别（Tesseract）
- 图表解析（GPT-4V/LLaVA）

#### DataCollector（数据采集器）

**功能**：
- 银行财报采集（42家A股上市银行）
- 宏观经济数据采集
- 政策文件采集

#### DataCleaner（数据清洗器）

**功能**：
- 指标名称标准化
- 数值清洗和单位转换
- 文本清洗（移除页眉页脚）
- 数据质量评估

#### DataImportService（数据导入服务）

**功能**：
- 数据导入到向量数据库
- 数据导入到知识图谱
- 批量导入和验证

---

## 四、核心模块设计

### 4.1 协同引擎设计（Coordinator）

**设计模式**：责任链模式 + 策略模式

**核心方法**：

```python
class Coordinator:
    async def process_query(
        self,
        query: str,
        context: Optional[ConversationContext] = None,
    ) -> Dict[str, Any]:
        """
        处理用户查询的完整流程
        
        流程：
        1. 理解意图（_understand_intent）
        2. 检索知识（_retrieve_knowledge）
        3. 生成回答（_generate_answer）
        4. 更新上下文
        """
```

**意图理解**：
- 使用LLM提取意图类型（指标查询/对比分析/趋势分析）
- 提取实体（公司、指标、时间）
- 支持多轮对话上下文

**工具调用能力**：
- 指标计算工具
- 图表生成工具
- 知识检索工具
- 分析工具

### 4.2 知识检索引擎设计（RetrievalEngine）

**RAG实现策略**：

1. **混合检索**：
   - 向量检索权重：0.7
   - 关键词检索权重：0.3
   - 合并去重后重排序

2. **Reranker优化**：
   - 使用BERT Reranker模型
   - Top10准确率提升至92%

3. **过滤器支持**：
   - 按公司过滤
   - 按时间过滤
   - 按指标类型过滤

### 4.3 大模型服务设计（LLMService）

**模型管理**：
- 支持多模型切换（OpenAI/DeepSeek/微调模型）
- 根据任务类型自动选择模型
- 金融领域问题优先使用微调模型

**异步处理**：
- 所有模型调用都是异步的
- 支持并发请求
- 自动重试机制

---

## 五、数据流转流程

### 5.1 用户查询流程

```
用户输入问题
    ↓
API层（路由、验证）
    ↓
Coordinator（协同引擎）
    ↓
意图理解（LLM）
    ↓
知识检索（RAG）
    ↓
工具调用（如需要）
    ↓
生成回答（LLM）
    ↓
返回结果
```

### 5.2 数据导入流程

```
数据采集（Collector）
    ↓
数据清洗（Cleaner）
    ↓
数据验证
    ↓
导入向量数据库（Milvus）
    ↓
导入知识图谱（Neo4j）
    ↓
元数据存储（SQLite）
```

### 5.3 报告生成流程

```
用户选择模板
    ↓
数据查询（ReportService）
    ↓
内容生成（LLM + 模板）
    ↓
图表生成（ECharts配置）
    ↓
格式导出（PDF/Word/Excel）
    ↓
返回文件
```

---

## 六、关键技术决策

### 6.1 为什么选择FastAPI？

1. **性能优势**：基于Starlette和Pydantic，性能接近Node.js
2. **异步支持**：原生支持async/await，适合AI模型调用
3. **自动文档**：Swagger UI自动生成，开发效率高
4. **类型安全**：基于Pydantic的类型验证

### 6.2 为什么选择Neo4j？

1. **关系查询优势**：金融知识图谱需要复杂关系查询
2. **查询性能**：图查询比SQL JOIN更高效
3. **可视化支持**：Neo4j Bloom支持可视化查询

### 6.3 为什么选择Milvus？

1. **高性能**：专为向量检索优化
2. **可扩展性**：支持分布式部署
3. **生态完善**：与AI框架集成良好

### 6.4 为什么选择React？

1. **组件化开发**：代码复用和维护方便
2. **生态丰富**：Ant Design、ECharts等组件库
3. **性能优化**：虚拟DOM、组件懒加载

---

## 七、项目结构

```
zncbzs/
├── backend/                    # 后端服务
│   ├── api/                   # API接口层
│   │   └── routes/            # 路由模块
│   ├── core/                  # 核心配置
│   │   ├── config.py          # 配置管理
│   │   ├── auth.py            # 权限管理
│   │   ├── security.py        # 安全工具
│   │   └── logging.py         # 日志配置
│   ├── engine/                # 引擎层
│   │   ├── coordinator.py     # 协同引擎 ⭐
│   │   ├── llm_service.py     # 大模型服务 ⭐
│   │   └── retrieval.py      # 检索引擎 ⭐
│   ├── data/                  # 数据层
│   │   ├── processor.py       # 文档处理
│   │   ├── storage.py         # 存储接口
│   │   ├── collector.py       # 数据采集
│   │   ├── cleaner.py         # 数据清洗
│   │   └── import_service.py  # 数据导入
│   ├── services/              # 应用服务层
│   │   ├── report_service.py  # 财报服务
│   │   ├── analysis_service.py # 分析服务
│   │   ├── report_generator.py # 报告生成
│   │   ├── agents.py          # 智能体服务 ⭐
│   │   └── scheduler.py       # 定时任务
│   ├── models/                # 模型模块
│   │   ├── finetune/          # LoRA微调
│   │   ├── reranker/          # Reranker模型
│   │   ├── ner/               # NER模型
│   │   ├── attribution/       # 归因分析模型
│   │   └── multimodal/        # 多模态模型
│   └── main.py                # 应用入口
├── frontend/                   # 前端
│   └── src/
│       ├── pages/             # 页面组件
│       ├── components/       # 通用组件
│       └── api/               # API调用
├── config/                     # 配置文件
│   ├── model_config.yaml     # 模型配置
│   └── env_template.txt       # 环境变量模板
└── docker-compose.yml          # Docker编排
```

---

## 八、设计模式和最佳实践

### 8.1 设计模式应用

1. **策略模式**：模型选择策略（OpenAI/DeepSeek/微调模型）
2. **工厂模式**：智能体创建（AgentManager）
3. **责任链模式**：任务处理流程（Coordinator）
4. **适配器模式**：存储接口抽象（VectorStore/KnowledgeGraph）

### 8.2 最佳实践

1. **异步编程**：所有I/O操作使用async/await
2. **错误处理**：统一的异常处理和日志记录
3. **配置管理**：使用Pydantic Settings管理配置
4. **类型安全**：使用类型注解和Pydantic验证
5. **代码组织**：按功能模块划分，职责清晰

---

## 九、扩展性设计

### 9.1 水平扩展

- **API层**：无状态设计，支持多实例部署
- **数据层**：Milvus支持分布式部署
- **缓存层**：Redis集群支持

### 9.2 垂直扩展

- **模型层**：支持新增模型类型
- **工具层**：支持新增分析工具
- **智能体层**：支持自定义智能体

### 9.3 插件化设计

- **数据源插件**：支持新增数据源
- **分析工具插件**：支持新增分析算法
- **导出格式插件**：支持新增导出格式

---

## 十、性能优化策略

### 10.1 缓存策略

- **高频指标缓存**：Redis缓存常用指标查询结果
- **向量检索缓存**：缓存相似查询的检索结果
- **模型响应缓存**：缓存相同问题的回答

### 10.2 并发优化

- **异步处理**：所有模型调用异步化
- **连接池**：数据库连接池管理
- **批量处理**：批量导入数据时使用批量API

### 10.3 查询优化

- **向量索引**：Milvus自动创建向量索引
- **图索引**：Neo4j创建节点和关系索引
- **查询优化**：优化Cypher查询语句

---

## 📚 相关文档

- [大模型微调文档](./INTERVIEW_02_模型微调.md)
- [多Agent协调文档](./INTERVIEW_03_多Agent协调.md)
- [Langchain使用文档](./INTERVIEW_04_Langchain.md)

