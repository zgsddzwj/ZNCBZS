# 数据集成使用指南

## 概述

数据集成功能用于自动采集、清洗和导入以下数据：
1. **42家A股上市银行财报数据**（近10年）
2. **宏观经济数据**（GDP、利率、通胀率等）
3. **行业政策文件**（央行、银保监会、证监会等）

## 架构设计

```
数据采集 → 数据清洗 → 数据导入
   ↓          ↓          ↓
Collector  Cleaner  ImportService
   ↓          ↓          ↓
  银行财报    标准化     向量数据库
  宏观数据    格式化     知识图谱
  政策文件    验证      关系数据库
```

## 核心模块

### 1. 数据采集器 (`backend/data/collector.py`)

#### BankReportCollector - 银行财报采集器
- 支持42家A股上市银行
- 支持年报、半年报、季报
- 并发采集（最多5个并发）
- 数据源：巨潮资讯网、Wind、同花顺等

#### MacroDataCollector - 宏观经济数据采集器
- 支持GDP、利率、通胀率、M2等指标
- 数据源：国家统计局、央行官网

#### PolicyFileCollector - 政策文件采集器
- 支持央行、银保监会、证监会等来源
- 自动下载PDF文件

### 2. 数据清洗器 (`backend/data/cleaner.py`)

- **指标标准化**：统一指标名称（如"营业收入"→"营收"）
- **数值清洗**：处理单位转换、格式统一
- **文本清洗**：移除页眉页脚、特殊字符
- **数据质量评估**：评估完整性、准确性

### 3. 数据导入服务 (`backend/data/import_service.py`)

- **向量数据库**：导入文本到Milvus（用于RAG检索）
- **知识图谱**：导入指标、关系到Neo4j
- **关系数据库**：存储元数据和统计信息

### 4. 定时任务调度器 (`backend/services/scheduler.py`)

- **每日更新**：每天凌晨2点自动更新最新数据
- **每周更新**：每周一凌晨3点完整更新
- **手动触发**：支持手动触发更新

## 使用方法

### 1. API调用

#### 集成银行财报数据

```bash
curl -X POST http://localhost:8000/api/v1/data-integration/bank-reports \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "bank_names": ["工商银行", "建设银行"],
    "years": [2022, 2023],
    "report_types": ["annual", "semi_annual"],
    "auto_import": true
  }'
```

#### 集成宏观经济数据

```bash
curl -X POST http://localhost:8000/api/v1/data-integration/macro-data \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "indicators": ["GDP", "利率", "通胀率"],
    "start_date": "2020-01-01",
    "end_date": "2024-12-31",
    "auto_import": true
  }'
```

#### 集成政策文件

```bash
curl -X POST http://localhost:8000/api/v1/data-integration/policy-files \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["央行", "银保监会"],
    "start_date": "2023-01-01",
    "end_date": "2024-12-31",
    "auto_import": true
  }'
```

#### 完整数据集成

```bash
curl -X POST http://localhost:8000/api/v1/data-integration/full \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "include_banks": true,
    "include_macro": true,
    "include_policies": true
  }'
```

#### 查询集成状态

```bash
curl -X GET http://localhost:8000/api/v1/data-integration/status \
  -H "Authorization: Bearer <token>"
```

### 2. Python代码调用

```python
from backend.services.data_integration_service import DataIntegrationService

service = DataIntegrationService()

# 集成银行财报
result = await service.integrate_bank_reports(
    bank_names=["工商银行", "建设银行"],
    years=[2022, 2023],
    auto_import=True,
)

# 集成宏观经济数据
result = await service.integrate_macro_data(
    indicators=["GDP", "利率"],
    start_date="2020-01-01",
    end_date="2024-12-31",
)

# 完整集成
result = await service.full_integration(
    include_banks=True,
    include_macro=True,
    include_policies=True,
)
```

## 数据源配置

### 1. 银行财报数据源

**巨潮资讯网（推荐）**
- 官方披露平台，数据权威
- 需要解析HTML或调用API
- URL示例：`http://www.cninfo.com.cn/new/information/topSearch/query`

**Wind/同花顺API**
- 需要付费账户
- 数据质量高，更新及时

**银行官网**
- 部分银行提供API
- 需要逐个银行配置

### 2. 宏观经济数据源

**国家统计局**
- API：`http://data.stats.gov.cn/easyquery.htm`
- 需要注册获取API密钥

**央行官网**
- 货币政策数据
- 需要解析HTML

### 3. 政策文件数据源

**央行官网**
- `http://www.pbc.gov.cn/zhengcehuobisi/125207/125213/`

**银保监会**
- `http://www.cbirc.gov.cn/`

**证监会**
- `http://www.csrc.gov.cn/pub/newsite/`

## 自动更新机制

系统启动后会自动启动定时任务：

1. **每日更新**（凌晨2点）
   - 检查最新财报（季度末）
   - 更新宏观经济数据（最近30天）
   - 更新政策文件（最近7天）

2. **每周更新**（周一凌晨3点）
   - 完整更新所有数据源

## 数据存储位置

- **原始数据**：`./data/raw/`
  - `bank_reports/` - 银行财报PDF
  - `macro_data/` - 宏观经济数据
  - `policy_files/` - 政策文件PDF

- **处理后数据**：
  - 向量数据库（Milvus）- 文本向量
  - 知识图谱（Neo4j）- 指标和关系
  - 关系数据库（SQLite/PostgreSQL）- 元数据

## 注意事项

1. **数据源API配置**
   - 需要根据实际数据源实现具体的采集逻辑
   - 某些数据源需要API密钥或付费账户
   - 需要处理反爬虫机制

2. **数据量**
   - 42家银行 × 10年 × 3种报告类型 ≈ 1260份财报
   - 每份财报平均50-200页，需要大量存储空间
   - 建议分批导入，避免内存溢出

3. **性能优化**
   - 使用异步并发采集
   - 使用连接池管理HTTP请求
   - 批量导入向量数据

4. **错误处理**
   - 网络错误自动重试
   - 数据格式错误跳过并记录
   - 失败数据记录日志便于排查

## 开发计划

### Phase 1: 基础框架（已完成）
- ✅ 数据采集器框架
- ✅ 数据清洗器框架
- ✅ 数据导入服务框架
- ✅ API路由

### Phase 2: 数据源实现（待完成）
- ⏳ 实现巨潮资讯网财报采集
- ⏳ 实现国家统计局API调用
- ⏳ 实现政策文件网站解析

### Phase 3: 优化和测试（待完成）
- ⏳ 性能优化（并发、缓存）
- ⏳ 错误处理和重试机制
- ⏳ 数据质量验证

## 常见问题

**Q: 如何添加新的数据源？**

A: 在对应的Collector类中添加新的采集方法，实现数据源特定的解析逻辑。

**Q: 如何修改数据清洗规则？**

A: 在`DataCleaner`类中修改对应的清洗方法，如`_clean_indicators`、`_clean_text`等。

**Q: 如何查看导入进度？**

A: 调用`/api/v1/data-integration/status`接口查看集成状态和统计信息。

**Q: 导入失败怎么办？**

A: 查看日志文件`./logs/`，检查错误信息。可以手动触发重新导入。

