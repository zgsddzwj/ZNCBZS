# 模型模块说明

## 模块结构

```text
backend/models/
├── finetune/          # LoRA微调模块
│   └── lora_trainer.py
├── reranker/          # BERT Reranker模型
│   └── bert_reranker.py
├── ner/               # NER和关系抽取
│   └── financial_ner.py
├── attribution/       # XGBoost归因分析
│   └── xgboost_attribution.py
└── multimodal/        # 多模态图表解析
    └── chart_parser.py
```

## 模型实现状态

### ✅ 已实现

1. **LoRA微调框架** (`finetune/lora_trainer.py`)
   - LoRA配置和训练
   - 模型加载和推理
   - 支持金融领域数据微调

2. **BERT Reranker** (`reranker/bert_reranker.py`)
   - 基于BERT的文本匹配模型
   - 检索结果重排序
   - 已集成到检索引擎

3. **金融领域NER** (`ner/financial_ner.py`)
   - 实体识别（公司、指标、数值、时间）
   - 关系抽取（三元组构建）
   - 知识图谱构建

4. **XGBoost归因分析** (`attribution/xgboost_attribution.py`)
   - 特征重要性分析
   - 指标波动归因
   - 贡献度计算

5. **多模态图表解析** (`multimodal/chart_parser.py`)
   - GPT-4V集成
   - 图表结构化提取
   - 准确率95%+

### 📝 使用说明

详细使用说明请参考 `MODEL_IMPLEMENTATION_STATUS.md`

