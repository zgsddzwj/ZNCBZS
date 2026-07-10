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
- 多轮对话记忆（Redis 持久化，24h TTL）
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
- 支持 PDF、Word、Excel 导出

### 5. 个性化配置
- 自定义指标库
- 权限管理（RBAC 三级角色）

## 技术架构

### 三层架构
- **数据层**：多源数据接入、预处理、知识库存储
- **引擎层**：协同引擎、大模型服务、知识检索引擎（RAG）
- **应用层**：财报问答、指标分析、报告生成等微服务

### 核心技术
- **基础大模型**：GPT 系列 + DeepSeek（API 调用，支持金融领域微调）
- **LoRA 微调**：基于金融领域数据的 LoRA 微调（支持本地模型部署）
- **辅助小模型**：
  - BERT Reranker：检索结果重排序（Top10 准确率 92%）
  - 金融领域 NER：基于 SpanBERT 的实体识别和关系抽取
  - XGBoost 归因分析：财务指标波动归因分析
- **多模态模型**：GPT-4V/LLaVA 处理图表数据（准确率 95%+）
- **知识图谱**：Neo4j 存储企业-指标-行业关系
- **向量数据库**：Milvus/FAISS 存储非结构化文档
- **RAG 技术**：检索增强生成（混合检索 + Reranker 重排序）

## 生产级安全与运维

本项目已完成生产级安全加固和运维优化，涵盖以下方面：

### 安全加固
| 功能 | 说明 |
|------|------|
| 数据库用户管理 | SQLAlchemy ORM + bcrypt 密码哈希，无硬编码凭证 |
| JWT 刷新/撤销 | Access Token (30min) + Refresh Token (7d) + Token 黑名单 |
| API 认证 | 所有端点强制认证，RBAC 三级权限控制 |
| 速率限制 | 登录 5 次/分钟，LLM 查询 20 次/分钟（slowapi） |
| 文件上传安全 | Magic Bytes 验证、大小限制、路径遍历防护 |
| Prompt 注入防护 | 用户输入清洗、注入检测、安全提示构建 |
| 加密密钥独立化 | Fernet 加密使用独立 `ENCRYPTION_KEY`，与 JWT 密钥分离 |
| CORS 收紧 | 仅允许实际使用的 HTTP 方法和头部 |
| TrustedHost 中间件 | 生产环境强制 Host 头验证 |
| 敏感信息脱敏 | 日志自动过滤 Token/密码等敏感字段 |
| 错误信息安全 | 不向客户端泄露内部异常详情 |
| 安全响应头 | X-Frame-Options、X-Content-Type-Options、CSP 等 |
| 请求体大小限制 | 默认 10MB，防止超大请求体攻击 |

### 运维与可靠性
| 功能 | 说明 |
|------|------|
| CI/CD 流水线 | GitHub Actions 自动化 Lint、测试、构建、Docker 镜像 |
| 深度健康检查 | `/health/deep` 检查数据库、Redis、调度器状态 |
| 对话历史持久化 | Redis 存储，多实例共享，24h 自动过期 |
| 操作日志持久化 | 数据库 + 日志文件双重存储 |
| 调度器优雅关闭 | 任务取消 + 30s 超时等待，防止数据不一致 |
| 多 Worker 部署 | Gunicorn + UvicornWorker，`max_requests` 防内存泄漏 |
| 前端生产构建 | 多阶段 Docker 构建，Nginx 托管静态文件 |
| 日志轮转 | 按天轮转，保留 30 天，自动压缩 |

## 项目结构

```
zncbzs/
├── backend/                  # 后端服务
│   ├── api/                  # API 路由层
│   │   ├── deps.py           # 依赖注入（服务单例复用）
│   │   └── routes/           # 路由模块（auth/chat/report/analysis/agents/upload/voice）
│   ├── core/                 # 核心配置和工具
│   │   ├── config.py         # Pydantic Settings 配置
│   │   ├── auth.py           # JWT 认证 + RBAC 权限
│   │   ├── security.py       # 加密、IP 白名单、操作日志
│   │   ├── rate_limit.py     # 速率限制（slowapi）
│   │   ├── prompt_security.py # Prompt 注入防护
│   │   ├── middleware.py     # 异常处理/请求日志/安全头/请求体限制
│   │   └── logging.py        # 日志配置（含敏感信息脱敏）
│   ├── data/                 # 数据层
│   │   ├── database.py       # SQLAlchemy 引擎和会话管理
│   │   ├── processor.py      # 文档处理器
│   │   └── storage.py        # 存储接口（向量 DB、知识图谱）
│   ├── engine/               # 引擎层
│   │   ├── coordinator.py    # 协同引擎（对话 Redis 持久化）
│   │   ├── llm_service.py    # 大模型服务
│   │   └── retrieval.py      # 知识检索引擎
│   ├── services/             # 应用层服务
│   │   ├── report_service.py # 财报服务
│   │   ├── analysis_service.py # 分析服务
│   │   └── scheduler.py      # 定时任务调度器（优雅关闭）
│   ├── models/               # 数据模型
│   │   ├── user.py           # 用户模型
│   │   └── operation_log.py  # 操作日志模型
│   ├── gunicorn_conf.py      # Gunicorn 生产配置
│   └── main.py               # 应用入口
├── frontend/                 # 前端界面
│   ├── src/
│   │   ├── pages/            # 页面组件（含 404 页面）
│   │   ├── components/       # 通用组件（含 ErrorBoundary）
│   │   ├── api/              # API 调用（含 JWT 自动刷新）
│   │   └── stores/           # Zustand 状态管理
│   ├── Dockerfile            # 多阶段生产构建
│   ├── nginx.conf            # Nginx 配置
│   └── vite.config.js        # Vite 配置（本地开发 proxy）
├── tests/                    # 单元测试
│   ├── test_auth.py          # 认证模块测试
│   ├── test_security.py      # 安全模块测试
│   └── test_prompt_security.py # Prompt 安全测试
├── docs/
│   └── API_VERSIONING.md     # API 版本控制策略
├── .github/workflows/
│   └── ci.yml                # CI/CD 流水线
├── .env.example              # 环境变量模板（唯一来源）
├── pyproject.toml            # Python 依赖管理
├── docker-compose.yml        # Docker 编排
└── README.md
```

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Redis
- Neo4j（可选，用于知识图谱）
- Milvus（可选，用于向量检索）

### 方式一：Docker Compose 部署（推荐）

1. 克隆项目
```bash
git clone https://github.com/zgsddzwj/ZNCBZS.git
cd zncbzs
```

2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 填入实际配置（API Key、数据库密码等）
```

3. 启动所有服务
```bash
docker-compose up -d
```

### 方式二：本地开发

1. 克隆项目
```bash
git clone https://github.com/zgsddzwj/ZNCBZS.git
cd zncbzs
```

2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 填入实际配置
```

3. 安装后端依赖
```bash
pip install -e ".[dev]"
```

4. 启动后端服务
```bash
# 开发模式
uvicorn backend.main:app --reload

# 生产模式（多 Worker）
gunicorn -c backend/gunicorn_conf.py backend.main:app
```

5. 启动前端服务（另开终端）
```bash
cd frontend
npm install
npm run dev
```

## 配置说明

### 环境变量

所有配置通过 `.env` 文件管理，模板见 `.env.example`。关键配置项：

| 变量 | 说明 | 必填 |
|------|------|------|
| `SECRET_KEY` | 应用密钥 | ✅ |
| `JWT_SECRET_KEY` | JWT 签名密钥 | ✅ |
| `ENCRYPTION_KEY` | 独立加密密钥（Fernet 格式，留空则从 SECRET_KEY 派生） | |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | ✅ |
| `DATABASE_URL` | 数据库连接地址 | ✅ |
| `REDIS_URL` | Redis 连接地址 | ✅ |
| `NEO4J_PASSWORD` | Neo4j 密码 | ✅ |
| `INITIAL_ADMIN_PASSWORD` | 初始管理员密码（首次启动自动创建） | ✅ |
| `DEBUG` | 调试模式（生产环境必须为 False） | |
| `CORS_ORIGINS` | 允许的跨域来源 | |
| `ALLOWED_HOSTS` | TrustedHost 允许的域名（生产环境需设置） | |

### 生成加密密钥

```python
# 生成独立的 ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## API 文档

- 开发环境：启动后端后访问 `http://localhost:8000/docs` 查看 Swagger 文档
- 生产环境：API 文档自动关闭，确保接口不暴露
- API 版本控制策略详见 [docs/API_VERSIONING.md](./docs/API_VERSIONING.md)

### 主要 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/login` | POST | 用户登录（返回 access + refresh token） |
| `/api/v1/auth/refresh` | POST | 刷新 access token |
| `/api/v1/auth/logout` | POST | 登出 |
| `/api/v1/auth/me` | GET | 获取当前用户信息 |
| `/api/v1/chat/query` | POST | 对话查询 |
| `/api/v1/chat/history/{id}` | GET / DELETE | 对话历史管理 |
| `/api/v1/reports/query` | POST | 财报数据查询 |
| `/api/v1/reports/indicators` | POST | 指标查询 |
| `/api/v1/reports/compare` | POST | 公司对比 |
| `/api/v1/analysis/*` | POST | 归因/风险/趋势分析 |
| `/api/v1/agents/*` | GET / POST | 智能体管理 |
| `/api/v1/upload/report` | POST | 上传财报文件 |
| `/health` | GET | 基础健康检查 |
| `/health/deep` | GET | 深度健康检查（DB/Redis/调度器） |

### 使用示例

#### 1. 登录获取 Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your-password"
```

#### 2. 对话查询
```bash
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-access-token>" \
  -d '{"message": "工商银行2023年营收同比增长多少？"}'
```

#### 3. 上传财报
```bash
curl -X POST http://localhost:8000/api/v1/upload/report \
  -H "Authorization: Bearer <your-access-token>" \
  -F "file=@report.pdf" \
  -F "company=招商银行" \
  -F "year=2023" \
  -F "report_type=annual"
```

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_auth.py -v
```

## CI/CD

项目使用 GitHub Actions 自动化流水线（`.github/workflows/ci.yml`）：

- **Lint**：Ruff 代码检查
- **Test**：多 Python 版本（3.10/3.11/3.12）单元测试
- **Frontend Build**：前端生产构建验证
- **Docker Build**：前后端 Docker 镜像构建验证

## 功能实现状态

### ✅ 已实现核心功能

1. **RBAC 权限管理系统**
   - 管理员、高级用户、普通用户三级权限
   - JWT 认证（Access + Refresh Token）
   - 操作日志数据库持久化

2. **智能体应用模块**
   - 5 个预置智能体（波士顿矩阵、SWOT 分析、信贷问答、零售转型、公文写作）
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
   - 趋势预测（1-2 年预测，带置信度）

6. **生产级安全**
   - AES-256 加密存储（独立加密密钥）
   - IP 白名单管理
   - 操作日志持久化（数据库 + 文件，≥1 年）
   - Prompt 注入防护
   - 速率限制 + 请求体大小限制
   - 安全响应头 + TrustedHost

### 🔄 待完善功能

- 报告模板定制和业务场景化报告
- 图表交互功能（hover、点击筛选、导出）
- 个性化推荐系统
- 系统参数配置界面
- 42 家 A 股上市银行数据导入
- 性能优化（响应时间、并发处理）

## 许可证

MIT License

## 联系方式

如有问题，请提交 Issue 或联系开发团队。
