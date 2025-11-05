"""
BERT Reranker模型
基于BERT微调的文本匹配模型，对初检索结果进行语义相关性重排
"""
from typing import List, Dict, Any, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from loguru import logger
import numpy as np


class BERTReranker:
    """BERT Reranker模型"""
    
    def __init__(
        self,
        model_path: str = "./models/reranker",
        device: str = "cuda",
    ):
        self.model_path = model_path
        self.device = device
        self.tokenizer = None
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载模型"""
        try:
            # 使用中文BERT模型（如BERT-base-chinese）
            # 或使用微调后的金融领域Reranker模型
            model_name = "bert-base-chinese"  # 默认使用基础模型
            
            # 如果存在微调模型，优先加载
            from pathlib import Path
            if Path(self.model_path).exists():
                model_name = self.model_path
                logger.info(f"加载微调Reranker模型: {model_name}")
            else:
                logger.info(f"使用基础BERT模型: {model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            
        except Exception as e:
            logger.error(f"加载Reranker模型失败: {e}")
            self.model = None
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        对检索结果进行重排序
        
        Args:
            query: 查询文本
            documents: 检索结果列表，每个元素包含content, score等
            top_k: 返回top K结果
        
        Returns:
            重排序后的结果列表
        """
        if not self.model or not documents:
            return documents[:top_k]
        
        try:
            # 构建query-document对
            pairs = []
            for doc in documents:
                content = doc.get("content", "")[:500]  # 截断内容
                pairs.append((query, content))
            
            # 批量计算相关性分数
            scores = self._compute_scores(pairs)
            
            # 更新分数并排序
            for i, doc in enumerate(documents):
                doc["rerank_score"] = float(scores[i])
                # 合并原始分数和重排序分数
                doc["final_score"] = doc.get("score", 0) * 0.3 + scores[i] * 0.7
            
            # 按最终分数排序
            reranked = sorted(
                documents,
                key=lambda x: x.get("final_score", 0),
                reverse=True,
            )
            
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            return documents[:top_k]
    
    def _compute_scores(
        self,
        pairs: List[Tuple[str, str]],
        batch_size: int = 32,
    ) -> np.ndarray:
        """批量计算相关性分数"""
        scores = []
        
        for i in range(0, len(pairs), batch_size):
            batch = pairs[i:i + batch_size]
            
            # 编码
            encoded = self.tokenizer(
                [q for q, _ in batch],
                [d for _, d in batch],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(self.device)
            
            # 推理
            with torch.no_grad():
                outputs = self.model(**encoded)
                logits = outputs.logits
                # 获取相关性分数（假设是二分类，取正类概率）
                batch_scores = torch.softmax(logits, dim=-1)[:, 1].cpu().numpy()
            
            scores.extend(batch_scores)
        
        return np.array(scores)

