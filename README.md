# 智能财报助手

基于大模型 + 知识增强的财务分析工具，支持通过自然语言对话实现财报解析、指标查询、风险分析、报告生成等功能，适配金融机构（银行、券商、基金）的财报分析场景，为金融分析师、信贷客户经理、风控人员及管理层提供专业化、高效化的智能支持。

## 产品概述

- **产品名称**：智能财报助手
- **产品定位**：基于大模型 + 知识增强的财务分析工具，支持通过自然语言对话实现财报解析、指标查询、风险分析、报告生成等功能，适配金融机构（银行、券商、基金）的财报分析场景。
- **目标用户**：银行内部市场研究人员、业务分析师、信贷客户经理、风控审核人员、中高层管理者；外部合作金融机构（如券商、基金公司）的财务分析团队
- **核心价值**：将单份银行财报分析时间从传统 2 小时缩短至 10 秒内，报告撰写效率提升 60% 以上，通过智能体应用覆盖 80% 以上的金融业务分析与办公场景

## 核心功能

### 1. 对话式交互
- 自然语言输入（文本/语音）
- 多轮对话记忆
- 意图纠错和补全

### 2. 财报解析与指标查询
- 多格式财报接入（PDF、Word、Excel）
- 核心指标查询（利润表、资产负债表、现金流量表）
- 跨期/跨公司对比

### 3. 深度分析
- 指标波动归因
- 风险预警
- 行业对标

### 4. 报告生成
- 一键生成分析报告
- 支持PDF、Word、Excel导出

### 5. 个性化配置
- 自定义指标库
- 权限管理

## 技术架构

### 三层架构
- **数据层**：多源数据接入、预处理、知识库存储
- **引擎层**：协同引擎、大模型服务、知识检索引擎（RAG）
- **应用层**：财报问答、指标分析、报告生成等微服务

### 核心技术
- **基础大模型**：GPT系列 + DeepSeek（API调用，支持金融领域微调）
- **LoRA微调**：基于金融领域数据的LoRA微调（支持本地模型部署）
- **辅助小模型**：
  - BERT Reranker：检索结果重排序（Top10准确率92%）
  - 金融领域NER：基于SpanBERT的实体识别和关系抽取
  - XGBoost归因分析：财务指标波动归因分析
- **多模态模型**：GPT-4V/LLaVA处理图表数据（准确率95%+）
- **知识图谱**：Neo4j存储企业-指标-行业关系
- **向量数据库**：Milvus/FAISS存储非结构化文档
- **RAG技术**：检索增强生成（混合检索 + Reranker重排序）

## 项目结构

```
zncbzs/
├── backend/              # 后端服务
│   ├── api/             # API接口层
│   ├── engine/          # 引擎层
│   ├── data/            # 数据层
│   ├── services/        # 应用层服务
│   └── models/          # 数据模型
├── frontend/            # 前端界面
├── config/              # 配置文件
├── requirements.txt     # Python依赖
└── docker-compose.yml   # Docker配置
```

## 快速开始

### 环境要求
- Python 3.10+
- Docker & Docker Compose
- Redis
- Neo4j（可选，用于知识图谱）
- Milvus（可选，用于向量检索）

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd zncbzs
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp config/.env.example config/.env
# 编辑 config/.env 填入你的配置
```

4. 启动服务
```bash
# 启动后端服务
cd backend
uvicorn main:app --reload

# 启动前端服务（另开终端）
cd frontend
npm install
npm run dev
```

5. 使用Docker Compose（推荐）
```bash
docker-compose up -d
```

## 配置说明

#### 环境变量配置
1. 复制环境变量模板：
```bash
cp config/env_template.txt .env
```

2. 编辑 `.env` 文件，填入你的配置：
- `OPENAI_API_KEY`: OpenAI API密钥（必需）
- `DEEPSEEK_API_KEY`: DeepSeek API密钥（可选）
- `NEO4J_URI`: Neo4j数据库地址（默认：bolt://localhost:7687）
- `MILVUS_HOST`: Milvus向量数据库地址（默认：localhost）
- `REDIS_URL`: Redis缓存地址（默认：redis://localhost:6379/0）

#### 模型配置
在 `config/model_config.yaml` 中配置模型参数和微调策略。

#### 数据库初始化
首次使用需要初始化数据库：
```bash
# 启动Docker服务（包含Neo4j、Milvus、Redis）
docker-compose up -d

# 或手动启动各个服务
# Neo4j: 访问 http://localhost:7474 进行初始化
# Milvus: 会自动创建集合
```

### 使用示例

#### 1. 对话查询
```bash
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "message": "贵州茅台2023年营收同比增长多少？"
  }'
```

#### 2. 上传财报
```bash
curl -X POST http://localhost:8000/api/v1/upload/report \
  -F "file=@report.pdf" \
  -F "company=贵州茅台" \
  -F "year=2023" \
  -F "report_type=annual"
```

#### 3. 指标查询
```bash
curl -X POST http://localhost:8000/api/v1/reports/indicators \
  -H "Content-Type: application/json" \
  -d '{
    "company": "招商银行",
    "indicator": "不良率",
    "start_year": 2021,
    "end_year": 2023
  }'
```

## API文档

启动服务后，访问 `http://localhost:8000/docs` 查看Swagger API文档。

## 项目结构

```
zncbzs/
├── backend/                  # 后端服务
│   ├── api/                 # API路由层
│   │   └── routes/          # 具体路由模块
│   ├── core/                # 核心配置和工具
│   ├── data/                # 数据层
│   │   ├── processor.py     # 文档处理器
│   │   └── storage.py       # 存储接口（向量DB、知识图谱）
│   ├── engine/              # 引擎层
│   │   ├── coordinator.py   # 协同引擎
│   │   ├── llm_service.py   # 大模型服务
│   │   └── retrieval.py     # 知识检索引擎
│   ├── services/            # 应用层服务
│   │   ├── report_service.py      # 财报服务
│   │   ├── analysis_service.py    # 分析服务
│   │   └── report_generator.py    # 报告生成服务
│   ├── models/              # 数据模型
│   └── main.py              # 应用入口
├── frontend/                # 前端界面
│   ├── src/
│   │   ├── pages/           # 页面组件
│   │   ├── components/      # 通用组件
│   │   └── api/             # API调用
│   └── package.json
├── config/                  # 配置文件
│   ├── model_config.yaml    # 模型配置
│   └── env_template.txt     # 环境变量模板
├── requirements.txt         # Python依赖
├── docker-compose.yml       # Docker编排
└── README.md
```

## 功能实现状态

### ✅ 已实现核心功能

1. **RBAC权限管理系统**
   - 管理员、高级用户、普通用户三级权限
   - JWT Token认证
   - 操作日志记录

2. **智能体应用模块**
   - 5个预置智能体（波士顿矩阵、SWOT分析、信贷问答、零售转型、公文写作）
   - 自定义智能体搭建功能

3. **语音交互功能**
   - 语音识别（支持普通话、粤语）
   - 文本转语音
   - 完整语音查询流程

4. **指标异常预警**
   - 行业均值偏离检测（±15%）
   - 历史均值偏离检测（±20%）
   - 预警原因分析

5. **深度财报分析**
   - 深度财报解读（提取关键信息）
   - 趋势预测（1-2年预测，带置信度）

6. **安全功能**
   - AES-256加密存储
   - IP白名单管理
   - 操作日志保存（≥1年）

### 🔄 待完善功能

- 报告模板定制和业务场景化报告
- 图表交互功能（hover、点击筛选、导出）
- 个性化推荐系统
- 系统参数配置界面
- 42家A股上市银行数据导入
- 性能优化（响应时间、并发处理）

详细功能清单请参考 [FEATURES.md](./FEATURES.md)

## 许可证

MIT License

## 联系方式

如有问题，请提交Issue或联系开发团队。

