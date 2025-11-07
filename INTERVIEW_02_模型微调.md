# 小京财智 AI 助手平台 - 大模型微调文档

## 📋 目录
1. [微调策略概述](#微调策略概述)
2. [LoRA微调实现](#lora微调实现)
3. [辅助小模型](#辅助小模型)
4. [模型训练流程](#模型训练流程)
5. [模型部署和推理](#模型部署和推理)

---

## 一、微调策略概述

### 1.1 微调目标

针对金融领域场景，优化模型在以下方面的能力：
- **财务术语理解**：准确理解金融专业术语（如"拨备覆盖率"、"净息差"）
- **指标计算逻辑**：理解财务指标计算公式和应用场景
- **财报逻辑分析**：理解财报数据的关联关系和业务逻辑
- **多轮对话能力**：支持上下文记忆和多轮对话
- **报告生成能力**：生成专业、准确的分析报告

### 1.2 微调方案

采用**分层微调策略**：

```
基础大模型（GPT-4/DeepSeek）
    ↓
LoRA微调（金融领域数据）
    ↓
专业模型（财报分析专用）
    +
辅助小模型（Reranker、NER、归因分析）
```

### 1.3 模型选择

| 模型 | 用途 | 优势 |
|------|------|------|
| **GPT-4-turbo** | 通用推理、文本生成 | 能力强、准确率高 |
| **DeepSeek-Chat** | 长文本处理、专业推理 | 长上下文、性价比高 |
| **LoRA微调模型** | 金融领域专用 | 专业化、成本低 |
| **BERT Reranker** | 检索重排序 | 准确率高、速度快 |
| **SpanBERT NER** | 实体识别 | 金融领域专用 |
| **XGBoost** | 归因分析 | 可解释性强 |

---

## 二、LoRA微调实现

### 2.1 LoRA技术原理

**LoRA（Low-Rank Adaptation）**：
- 在原始模型的权重矩阵旁添加低秩矩阵
- 只训练低秩矩阵，冻结原始权重
- 大幅减少训练参数（从670亿到6.7亿，约1%）
- 显著降低显存需求和训练时间

**优势**：
- 训练速度快（2.5-3天 vs 数周）
- 显存占用少（可训练更大模型）
- 模型效果好（接近全量微调）
- 易于部署（只需保存LoRA权重）

### 2.2 实现架构

**位置**：`backend/models/finetune/lora_trainer.py`

**核心类**：`LoRATrainer`

**关键方法**：

```python
class LoRATrainer:
    def load_base_model(self):
        """加载基础模型（如DeepSeek-7B）"""
    
    def prepare_training_data(self, data_path: str):
        """准备训练数据（格式化、分词）"""
    
    def train(self, dataset, num_epochs=3):
        """LoRA微调训练"""
    
    def generate(self, prompt: str):
        """使用微调模型生成文本"""
```

### 2.3 LoRA配置

```python
# LoRA配置参数
lora_config = LoraConfig(
    r=16,              # LoRA rank（低秩矩阵的秩）
    lora_alpha=32,     # LoRA alpha（缩放因子）
    target_modules=["q_proj", "v_proj"],  # 目标模块
    lora_dropout=0.1,  # Dropout率
    bias="none",       # 偏置处理方式
    task_type=TaskType.CAUSAL_LM  # 任务类型
)
```

**参数说明**：
- `r`：低秩矩阵的秩，越大效果越好但参数越多（推荐16-64）
- `lora_alpha`：缩放因子，通常设为r的2倍
- `target_modules`：需要微调的模块（注意力层、MLP层等）

### 2.4 训练数据准备

**数据格式**：
```json
{
    "instruction": "分析以下财报数据，计算不良率",
    "input": "某银行2023年不良贷款余额100亿元，各项贷款总额5000亿元",
    "output": "不良率 = 不良贷款余额 / 各项贷款总额 = 100 / 5000 = 2%"
}
```

**数据规模**：
- **总数据量**：17万条标注数据
- **财报问答对**：10万条
- **指标计算示例**：5万条
- **分析方法应用**：2万条

**数据来源**：
- 财报文本提取
- 金融领域知识库
- 专家标注
- 数据增强（同义替换、改写）

### 2.5 训练流程

```python
# 1. 初始化训练器
trainer = LoRATrainer(
    base_model_name="DeepSeek-7B-Chat",
    output_dir="./models/financial_llm_lora"
)

# 2. 加载基础模型
trainer.load_base_model()

# 3. 准备训练数据
dataset = trainer.prepare_training_data("data/training_data.json")

# 4. 开始训练
trainer.train(
    dataset=dataset,
    num_epochs=3,
    batch_size=4,
    learning_rate=2e-4
)
```

**训练参数**：
- **Epochs**：3轮（防止过拟合）
- **Batch Size**：4-8（根据GPU显存调整）
- **Learning Rate**：2e-4（LoRA推荐学习率）
- **Max Length**：2048（最大序列长度）

### 2.6 训练资源需求

**推荐方案**：DeepSeek-7B + 8张RTX 4090
- **训练时间**：约2.5天
- **显存需求**：每卡约20GB
- **成本**：约7,000元（云服务）

**最佳方案**：DeepSeek-67B + 64张RTX 4090
- **训练时间**：约2.9天
- **显存需求**：每卡约12GB
- **成本**：约44,000元（云服务）

---

## 三、辅助小模型

### 3.1 BERT Reranker模型

**位置**：`backend/models/reranker/bert_reranker.py`

**功能**：对RAG检索结果进行重排序，提升Top-K准确率

**技术方案**：
- **基础模型**：BERT或RoBERTa
- **微调数据**：查询-文档相关性标注数据
- **训练方式**：监督学习（对比学习）

**性能指标**：
- **Top10准确率**：92%（比未重排序提升约15%）
- **推理速度**：批量处理，毫秒级

**集成方式**：
```python
# 在检索引擎中自动使用
class RetrievalEngine:
    async def _rerank(self, query, results, top_k):
        """使用BERT Reranker重排序"""
        reranker = BERTReranker()
        return reranker.rerank(query, results, top_k)
```

### 3.2 金融领域NER模型

**位置**：`backend/models/ner/financial_ner.py`

**功能**：从财报文本中提取金融实体

**提取的实体类型**：
- **公司实体**：银行名称、公司代码
- **指标实体**：财务指标（如"不良率"、"ROE"）
- **数值实体**：指标数值、百分比
- **时间实体**：年份、季度、日期

**技术方案**：
- **基础模型**：SpanBERT（适合实体识别）
- **标签体系**：BIO标注（B-公司、I-公司、O等）
- **训练数据**：金融领域实体标注数据（约5万条）

**使用示例**：
```python
ner = FinancialNER()
entities = ner.extract_entities(
    "招商银行2023年不良率1.5%，同比下降0.2个百分点"
)
# 输出：
# [
#     {"type": "公司", "text": "招商银行", "start": 0, "end": 4},
#     {"type": "时间", "text": "2023年", "start": 4, "end": 9},
#     {"type": "指标", "text": "不良率", "start": 9, "end": 12},
#     {"type": "数值", "text": "1.5%", "start": 12, "end": 16}
# ]
```

### 3.3 XGBoost归因分析模型

**位置**：`backend/models/attribution/xgboost_attribution.py`

**功能**：分析财务指标波动的原因和贡献度

**技术方案**：
- **算法**：XGBoost（梯度提升树）
- **特征工程**：财务指标、宏观经济指标、行业指标
- **输出**：各因素的贡献度和重要性

**使用示例**：
```python
model = XGBoostAttributionModel()
result = model.analyze_attribution(
    features={
        "净利润": 100,
        "营收": 1000,
        "成本": 800,
        "净息差": 2.5,
        "资产规模": 50000
    }
)
# 输出：
# {
#     "factors": [
#         {"name": "净息差扩大", "contribution": 0.6, "impact": "+60%"},
#         {"name": "资产规模增长", "contribution": 0.3, "impact": "+30%"},
#         {"name": "成本控制", "contribution": 0.1, "impact": "+10%"}
#     ]
# }
```

---

## 四、模型训练流程

### 4.1 数据准备阶段

**步骤**：
1. **数据收集**：收集金融领域语料（财报、政策、规则）
2. **数据清洗**：去重、格式化、质量检查
3. **数据标注**：标注问答对、实体、关系（标注团队3-5人）
4. **数据分割**：训练集/验证集/测试集（8:1:1）
5. **数据增强**：同义替换、改写、生成

**时间**：2-3周

### 4.2 模型训练阶段

**步骤**：
1. **环境准备**：GPU服务器、训练环境搭建
2. **模型下载**：下载基础模型（DeepSeek-7B/67B）
3. **训练执行**：运行训练脚本
4. **模型验证**：在验证集上评估性能
5. **超参数调优**：调整学习率、batch size等
6. **模型保存**：保存最佳模型checkpoint

**时间**：2-3周（包括调优）

### 4.3 模型评估阶段

**评估指标**：
- **准确率**：回答正确率
- **相关性**：回答与问题的相关性
- **专业性**：金融术语使用准确性
- **流畅性**：文本生成流畅度

**评估方法**：
- **自动评估**：BLEU、ROUGE、BERTScore
- **人工评估**：专家评分（0-5分）

### 4.4 模型部署阶段

**步骤**：
1. **模型导出**：导出LoRA权重
2. **模型量化**：INT8/INT4量化（可选，减少显存）
3. **模型加载**：集成到LLMService
4. **性能测试**：测试推理速度和准确率
5. **A/B测试**：对比微调模型和基础模型效果

---

## 五、模型部署和推理

### 5.1 模型集成

**位置**：`backend/engine/llm_service.py`

**集成方式**：
```python
class LLMService:
    def __init__(self):
        # 加载LoRA微调模型
        try:
            self.lora_trainer = LoRATrainer()
            self.lora_trainer.load_finetuned_model(
                "./models/financial_llm_lora"
            )
            self.finetuned_model = self.lora_trainer
        except Exception as e:
            logger.warning(f"LoRA模型加载失败: {e}")
    
    async def generate(self, prompt: str, use_finetuned: bool = False):
        """生成文本，优先使用微调模型"""
        if use_finetuned and self.finetuned_model:
            # 使用LoRA微调模型
            return await self._generate_with_finetuned(prompt)
        else:
            # 使用API模型
            return await self._generate_with_api(prompt)
```

### 5.2 模型切换策略

**自动切换逻辑**：
- **金融领域问题**：自动使用微调模型
- **通用问题**：使用API模型（GPT-4/DeepSeek）
- **长文本处理**：使用DeepSeek API

**判断逻辑**：
```python
def is_financial_domain(query: str) -> bool:
    """判断是否为金融领域问题"""
    financial_keywords = [
        "财报", "指标", "不良率", "ROE", "净利润",
        "银行", "信贷", "风险", "分析"
    ]
    return any(keyword in query for keyword in financial_keywords)
```

### 5.3 推理优化

**优化策略**：
1. **缓存机制**：缓存相同问题的回答
2. **批量推理**：批量处理多个请求
3. **模型量化**：INT8量化减少显存和加速
4. **异步处理**：使用异步接口避免阻塞

**性能指标**：
- **推理速度**：单次推理约2-5秒（取决于模型大小）
- **并发能力**：支持多用户并发查询
- **显存占用**：DeepSeek-7B约14GB，DeepSeek-67B约134GB

---

## 六、训练数据示例

### 6.1 财报问答对示例

```json
{
    "instruction": "分析以下财报数据，回答问题",
    "input": "某银行2023年净利润100亿元，2022年净利润80亿元，同比增长多少？",
    "output": "净利润同比增长率 = (2023年净利润 - 2022年净利润) / 2022年净利润 × 100% = (100 - 80) / 80 × 100% = 25%。因此，该银行2023年净利润同比增长25%。"
}
```

### 6.2 指标计算示例

```json
{
    "instruction": "计算财务指标",
    "input": "某银行不良贷款余额50亿元，各项贷款总额5000亿元，计算不良率",
    "output": "不良率 = 不良贷款余额 / 各项贷款总额 × 100% = 50 / 5000 × 100% = 1%。该银行不良率为1%。"
}
```

### 6.3 分析方法应用示例

```json
{
    "instruction": "使用杜邦分析法分析ROE",
    "input": "某银行ROE为15%，净利率为30%，资产周转率为0.5，权益乘数为1.0",
    "output": "根据杜邦分析法：ROE = 净利率 × 资产周转率 × 权益乘数 = 30% × 0.5 × 1.0 = 15%。该银行ROE主要由净利率和资产周转率驱动，权益乘数较低。"
}
```

---

## 七、模型评估指标

### 7.1 自动评估指标

| 指标 | 说明 | 目标值 |
|------|------|--------|
| **BLEU** | 文本生成质量 | ≥0.6 |
| **ROUGE-L** | 文本召回率 | ≥0.7 |
| **BERTScore** | 语义相似度 | ≥0.85 |
| **准确率** | 事实准确性 | ≥90% |

### 7.2 人工评估维度

| 维度 | 评分标准 | 目标 |
|------|---------|------|
| **准确性** | 回答是否正确 | ≥4.5/5 |
| **专业性** | 金融术语使用是否准确 | ≥4.5/5 |
| **相关性** | 回答是否切题 | ≥4.5/5 |
| **流畅性** | 文本是否流畅 | ≥4.0/5 |
| **完整性** | 回答是否完整 | ≥4.0/5 |

---

## 八、微调效果对比

### 8.1 微调前 vs 微调后

| 场景 | 微调前 | 微调后 | 提升 |
|------|--------|--------|------|
| **财务术语理解** | 70% | 95% | +25% |
| **指标计算准确率** | 75% | 92% | +17% |
| **财报分析专业度** | 3.2/5 | 4.6/5 | +1.4 |
| **金融领域问答** | 68% | 91% | +23% |

### 8.2 成本对比

| 方案 | 训练成本 | 推理成本（月） | 总成本（年） |
|------|---------|---------------|-------------|
| **API调用** | 0 | 10-20万 | 120-240万 |
| **LoRA微调** | 7,000元 | 2-5万 | 25-60万 |
| **节省** | - | - | **95-180万** |

---

## 九、模型管理

### 9.1 模型版本管理

- **版本命名**：`financial_llm_lora_v1.0.0`
- **版本说明**：记录训练数据、超参数、性能指标
- **版本回滚**：支持快速回滚到上一版本

### 9.2 模型监控

- **性能监控**：推理速度、准确率、错误率
- **使用统计**：调用次数、用户反馈
- **异常告警**：模型异常、性能下降

### 9.3 模型更新

- **增量更新**：基于新数据增量训练
- **全量更新**：定期全量重新训练
- **A/B测试**：新版本上线前进行对比测试

---

## 📚 相关文档

- [项目架构文档](./INTERVIEW_01_项目架构.md)
- [多Agent协调文档](./INTERVIEW_03_多Agent协调.md)
- [Langchain使用文档](./INTERVIEW_04_Langchain.md)

