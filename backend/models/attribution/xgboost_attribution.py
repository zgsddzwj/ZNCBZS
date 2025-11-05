"""
XGBoost归因分析模型
对财务指标波动进行影响因子量化分析
"""
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import xgboost as xgb
from loguru import logger
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib


class XGBoostAttributionModel:
    """XGBoost归因分析模型"""
    
    def __init__(
        self,
        model_path: str = "./models/attribution/xgboost_model.pkl",
    ):
        self.model_path = model_path
        self.model = None
        self.feature_names = [
            "net_interest_margin",  # 净息差
            "operating_cost_ratio",  # 营业成本率
            "loan_growth_rate",  # 贷款增长率
            "deposit_growth_rate",  # 存款增长率
            "npl_ratio",  # 不良率
            "provision_coverage",  # 拨备覆盖率
            "roe",  # 净资产收益率
            "asset_quality_score",  # 资产质量评分
            # ... 更多特征
        ]
    
    def train(
        self,
        training_data: pd.DataFrame,
        target_column: str = "revenue_growth",
    ):
        """
        训练归因分析模型
        
        Args:
            training_data: 训练数据，包含特征和目标变量
            target_column: 目标变量列名（如营收增长率）
        """
        logger.info("开始训练XGBoost归因分析模型...")
        
        # 准备特征和目标
        X = training_data[self.feature_names]
        y = training_data[target_column]
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # 训练XGBoost模型
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            objective='reg:squarederror',
            random_state=42,
        )
        
        self.model.fit(
            X_train,
            y_train,
            eval_set=[(X_test, y_test)],
            early_stopping_rounds=10,
            verbose=False,
        )
        
        # 评估模型
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        logger.info(f"模型训练完成 - MSE: {mse:.4f}, R²: {r2:.4f}")
        
        # 保存模型
        self.save_model()
    
    def analyze_attribution(
        self,
        features: Dict[str, float],
        target_value: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        分析指标波动的归因
        
        Args:
            features: 特征值字典
            target_value: 目标值（如果已知）
        
        Returns:
            {
                "predicted_value": 预测值,
                "feature_importance": {
                    "净息差": 0.35,  # 贡献度35%
                    "营业成本率": 0.25,
                    ...
                },
                "top_factors": [
                    {"factor": "净息差", "contribution": 0.35, "impact": "正"},
                    ...
                ]
            }
        """
        if not self.model:
            raise ValueError("模型未训练或未加载")
        
        # 准备特征向量
        feature_vector = np.array([
            features.get(name, 0.0) for name in self.feature_names
        ]).reshape(1, -1)
        
        # 预测
        predicted = self.model.predict(feature_vector)[0]
        
        # 计算特征重要性（使用SHAP值更准确）
        importances = self.model.feature_importances_
        
        # 计算贡献度
        feature_importance = {
            name: float(importance)
            for name, importance in zip(self.feature_names, importances)
        }
        
        # 归一化贡献度
        total = sum(feature_importance.values())
        if total > 0:
            feature_importance = {
                k: v / total for k, v in feature_importance.items()
            }
        
        # 排序获取top factors
        sorted_factors = sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        top_factors = [
            {
                "factor": name,
                "contribution": contrib,
                "impact": "正" if features.get(name, 0) > 0 else "负",
            }
            for name, contrib in sorted_factors[:5]
        ]
        
        return {
            "predicted_value": float(predicted),
            "feature_importance": feature_importance,
            "top_factors": top_factors,
        }
    
    def save_model(self):
        """保存模型"""
        if self.model:
            joblib.dump(self.model, self.model_path)
            logger.info(f"模型已保存至: {self.model_path}")
    
    def load_model(self):
        """加载模型"""
        try:
            self.model = joblib.load(self.model_path)
            logger.info(f"模型已加载: {self.model_path}")
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            self.model = None

