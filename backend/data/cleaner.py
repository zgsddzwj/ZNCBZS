"""
数据清洗和标准化器
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
from loguru import logger
import pandas as pd
from backend.core.config import settings


class DataCleaner:
    """数据清洗器"""
    
    def __init__(self):
        # 财务指标标准名称映射
        self.indicator_mapping = settings.INDICATOR_MAPPING
    
    def clean_bank_report_data(
        self,
        raw_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        清洗银行财报数据
        
        Args:
            raw_data: 原始财报数据
        
        Returns:
            清洗后的数据
        """
        cleaned_data = {
            "bank": self._normalize_bank_name(raw_data.get("bank", "")),
            "year": raw_data.get("year"),
            "report_type": raw_data.get("report_type", "annual"),
            "indicators": {},
            "tables": [],
            "text": "",
        }
        
        # 清洗指标数据
        if "indicators" in raw_data:
            cleaned_data["indicators"] = self._clean_indicators(
                raw_data["indicators"]
            )
        
        # 清洗表格数据
        if "tables" in raw_data:
            cleaned_data["tables"] = self._clean_tables(raw_data["tables"])
        
        # 清洗文本数据
        if "text" in raw_data:
            cleaned_data["text"] = self._clean_text(raw_data["text"])
        
        # 添加元数据
        cleaned_data["metadata"] = {
            "source": raw_data.get("source", ""),
            "publish_date": raw_data.get("publish_date", ""),
            "cleaned_at": datetime.now().isoformat(),
            "data_quality": self._assess_data_quality(cleaned_data),
        }
        
        return cleaned_data
    
    def _normalize_bank_name(self, bank_name: str) -> str:
        """标准化银行名称"""
        # 移除常见后缀
        bank_name = bank_name.replace("股份有限公司", "")
        bank_name = bank_name.replace("有限公司", "")
        bank_name = bank_name.replace("银行", "")
        
        # 标准化名称映射
        name_mapping = {
            "工行": "工商银行",
            "建行": "建设银行",
            "农行": "农业银行",
            "中行": "中国银行",
            "交行": "交通银行",
            "招行": "招商银行",
        }
        
        return name_mapping.get(bank_name, bank_name)
    
    def _clean_indicators(
        self,
        indicators: Dict[str, Any],
    ) -> Dict[str, Any]:
        """清洗指标数据"""
        cleaned = {}
        
        for key, value in indicators.items():
            # 标准化指标名称
            normalized_key = self.indicator_mapping.get(key, key)
            
            # 清洗数值
            cleaned_value = self._clean_numeric_value(value)
            
            if cleaned_value is not None:
                cleaned[normalized_key] = cleaned_value
        
        return cleaned
    
    def _clean_numeric_value(self, value: Any) -> Optional[float]:
        """清洗数值"""
        if value is None:
            return None
        
        # 如果是字符串，提取数字
        if isinstance(value, str):
            # 移除常见格式符号
            value = value.replace(",", "").replace("，", "")
            value = value.replace("%", "").replace("％", "")
            value = value.replace("亿元", "").replace("万元", "").replace("元", "")
            
            # 提取数字
            match = re.search(r"-?\d+\.?\d*", value)
            if match:
                try:
                    num = float(match.group())
                    # 单位转换（万元转亿元）
                    if "万元" in value or "万" in value:
                        num = num / 10000
                    return num
                except:
                    pass
        
        # 如果是数字，直接返回
        if isinstance(value, (int, float)):
            return float(value)
        
        return None
    
    def _clean_tables(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清洗表格数据"""
        cleaned_tables = []
        
        for table in tables:
            try:
                # 转换为DataFrame进行清洗
                if isinstance(table, dict) and "data" in table:
                    df = pd.DataFrame(table["data"])
                    
                    # 清洗列名
                    df.columns = [self._clean_column_name(col) for col in df.columns]
                    
                    # 移除空行
                    df = df.dropna(how="all")
                    
                    # 清洗数值列
                    numeric_cols = df.select_dtypes(include=["object"]).columns
                    for col in numeric_cols:
                        df[col] = df[col].apply(
                            lambda x: self._clean_numeric_value(x) if isinstance(x, str) else x
                        )
                    
                    cleaned_tables.append({
                        "name": table.get("name", ""),
                        "data": df.to_dict("records"),
                        "columns": list(df.columns),
                    })
                else:
                    cleaned_tables.append(table)
                    
            except Exception as e:
                logger.warning(f"清洗表格失败: {e}")
                cleaned_tables.append(table)
        
        return cleaned_tables
    
    def _clean_column_name(self, col_name: str) -> str:
        """清洗列名"""
        # 移除空格和特殊字符
        col_name = re.sub(r"\s+", "", col_name)
        col_name = col_name.strip()
        
        # 标准化映射
        return self.indicator_mapping.get(col_name, col_name)
    
    def _clean_text(self, text: str) -> str:
        """清洗文本数据"""
        if not text:
            return ""
        
        # 移除多余空白
        text = re.sub(r"\s+", " ", text)
        
        # 移除特殊字符
        text = re.sub(r"[^\u4e00-\u9fa5\w\s\.\,\;\:\!\?\(\)\[\]（）【】]", "", text)
        
        # 移除页眉页脚（常见模式）
        text = re.sub(r"第\s*\d+\s*页", "", text)
        text = re.sub(r"共\s*\d+\s*页", "", text)
        
        return text.strip()
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """评估数据质量"""
        quality_score = 100
        
        # 检查指标完整性
        if not data.get("indicators"):
            quality_score -= 30
        
        # 检查表格数据
        if not data.get("tables"):
            quality_score -= 20
        
        # 检查文本数据
        if not data.get("text") or len(data["text"]) < 100:
            quality_score -= 10
        
        return {
            "score": quality_score,
            "indicators_count": len(data.get("indicators", {})),
            "tables_count": len(data.get("tables", [])),
            "text_length": len(data.get("text", "")),
        }
    
    def clean_macro_data(
        self,
        raw_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """清洗宏观经济数据"""
        cleaned_data = {
            "indicator": raw_data.get("indicator", ""),
            "data_points": [],
            "unit": "",
            "frequency": "月度",  # 月度/季度/年度
        }
        
        # 清洗数据点
        if "data" in raw_data:
            for point in raw_data["data"]:
                cleaned_point = {
                    "date": self._parse_date(point.get("date", "")),
                    "value": self._clean_numeric_value(point.get("value", "")),
                }
                if cleaned_point["date"] and cleaned_point["value"] is not None:
                    cleaned_data["data_points"].append(cleaned_point)
        
        return cleaned_data
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        # 尝试多种日期格式
        date_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
            "%Y-%m",
            "%Y/%m",
            "%Y年%m月",
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except:
                continue
        
        return None

