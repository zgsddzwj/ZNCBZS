"""
金融领域NER模型
基于SpanBERT的命名实体识别和关系抽取
从非结构化财报中提取"企业-指标-数值-时间"等三元组
"""
from typing import List, Dict, Any, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
from loguru import logger


class FinancialNER:
    """金融领域NER模型"""
    
    def __init__(
        self,
        model_path: str = "./models/ner",
        device: str = "cuda",
    ):
        self.model_path = model_path
        self.device = device
        self.tokenizer = None
        self.model = None
        
        # 实体类型定义
        self.entity_types = [
            "B-COMPANY", "I-COMPANY",  # 公司名称
            "B-INDICATOR", "I-INDICATOR",  # 财务指标
            "B-VALUE", "I-VALUE",  # 数值
            "B-TIME", "I-TIME",  # 时间
            "O",  # 其他
        ]
        
        self._load_model()
    
    def _load_model(self):
        """加载NER模型"""
        try:
            # 使用中文NER模型（如BERT-NER或微调的金融领域模型）
            model_name = "dbmdz/bert-base-chinese"  # 默认使用基础模型
            
            from pathlib import Path
            if Path(self.model_path).exists():
                model_name = self.model_path
                logger.info(f"加载微调NER模型: {model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            # 注意：需要根据实际模型结构调整
            # 这里假设使用TokenClassification模型
            self.model = AutoModelForTokenClassification.from_pretrained(
                model_name,
                num_labels=len(self.entity_types),
            )
            self.model.to(self.device)
            self.model.eval()
            
        except Exception as e:
            logger.error(f"加载NER模型失败: {e}")
            self.model = None
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取实体
        
        Returns:
            [
                {"text": "招商银行", "type": "COMPANY", "start": 0, "end": 4},
                {"text": "不良率", "type": "INDICATOR", "start": 10, "end": 13},
                {"text": "1.5%", "type": "VALUE", "start": 14, "end": 18},
                {"text": "2023年", "type": "TIME", "start": 19, "end": 24},
            ]
        """
        if not self.model:
            return []
        
        try:
            # 分词和编码
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            ).to(self.device)
            
            # 推理
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.argmax(outputs.logits, dim=-1)
            
            # 解码和提取实体
            tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0].cpu())
            labels = predictions[0].cpu().numpy()
            
            entities = self._extract_entities_from_labels(tokens, labels, text)
            
            return entities
            
        except Exception as e:
            logger.error(f"实体提取失败: {e}")
            return []
    
    def extract_relations(
        self,
        text: str,
        entities: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        提取实体间的关系
        
        提取三元组：企业-指标-数值-时间
        """
        # 简化版：基于规则和位置关系
        # 实际应该使用关系抽取模型（如SpanBERT）
        
        relations = []
        
        # 查找(公司, 指标, 数值, 时间)模式
        companies = [e for e in entities if e["type"] == "COMPANY"]
        indicators = [e for e in entities if e["type"] == "INDICATOR"]
        values = [e for e in entities if e["type"] == "VALUE"]
        times = [e for e in entities if e["type"] == "TIME"]
        
        # 构建关系（简化版）
        for company in companies:
            for indicator in indicators:
                # 找到最近的数值和时间
                closest_value = min(
                    values,
                    key=lambda v: abs(v["start"] - indicator["end"]),
                    default=None,
                )
                closest_time = min(
                    times,
                    key=lambda t: abs(t["start"] - indicator["end"]),
                    default=None,
                )
                
                if closest_value:
                    relations.append({
                        "subject": company["text"],
                        "predicate": indicator["text"],
                        "object": closest_value["text"],
                        "time": closest_time["text"] if closest_time else None,
                    })
        
        return relations
    
    def _extract_entities_from_labels(
        self,
        tokens: List[str],
        labels: np.ndarray,
        original_text: str,
    ) -> List[Dict[str, Any]]:
        """从标签序列中提取实体"""
        entities = []
        current_entity = None
        
        for i, (token, label_id) in enumerate(zip(tokens, labels)):
            label = self.entity_types[label_id]
            
            if label.startswith("B-"):
                # 新实体开始
                if current_entity:
                    entities.append(current_entity)
                current_entity = {
                    "type": label[2:],
                    "start": i,
                    "end": i + 1,
                    "tokens": [token],
                }
            elif label.startswith("I-") and current_entity:
                # 实体继续
                current_entity["end"] = i + 1
                current_entity["tokens"].append(token)
            else:
                # 实体结束
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
        
        # 处理最后一个实体
        if current_entity:
            entities.append(current_entity)
        
        # 转换为文本位置
        for entity in entities:
            entity["text"] = "".join(entity["tokens"]).replace("##", "")
            # 简化版：实际需要更精确的位置映射
        
        return entities

