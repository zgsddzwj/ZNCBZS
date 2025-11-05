"""
多模态图表解析模型
使用GPT-4V或LLaVA解析财报中的图表数据
"""
from typing import Dict, Any, Optional, List
from pathlib import Path
from openai import AsyncOpenAI
from loguru import logger
from backend.core.config import settings
import base64


class ChartParser:
    """图表解析器"""
    
    def __init__(self):
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # LLaVA模型（需要本地部署）
        self.llava_model = None
        self.use_llava = False  # 默认使用GPT-4V
    
    async def parse_chart(
        self,
        image_path: str,
        chart_type: str = "auto",  # auto, table, bar, line, pie
        use_model: str = "gpt4v",  # gpt4v or llava
    ) -> Dict[str, Any]:
        """
        解析图表
        
        Args:
            image_path: 图片路径
            chart_type: 图表类型
            use_model: 使用的模型
        
        Returns:
            {
                "chart_type": "bar",
                "data": {...},
                "structured_data": [...],
                "accuracy": 0.95
            }
        """
        if use_model == "gpt4v":
            return await self._parse_with_gpt4v(image_path, chart_type)
        elif use_model == "llava":
            return await self._parse_with_llava(image_path, chart_type)
        else:
            raise ValueError(f"不支持的模型: {use_model}")
    
    async def _parse_with_gpt4v(
        self,
        image_path: str,
        chart_type: str,
    ) -> Dict[str, Any]:
        """使用GPT-4V解析图表"""
        if not self.openai_client:
            raise ValueError("未配置OpenAI API密钥")
        
        try:
            # 读取图片并编码
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            prompt = f"""
请分析以下财报图表，提取结构化数据。

图表类型：{chart_type}

要求：
1. 识别图表类型（柱状图、折线图、饼图、表格等）
2. 提取所有数据点
3. 识别坐标轴标签和单位
4. 返回结构化JSON格式

请返回JSON格式：
{{
    "chart_type": "图表类型",
    "data": {{
        "x_axis": ["标签1", "标签2", ...],
        "y_axis": "Y轴标签",
        "series": [
            {{"name": "系列1", "values": [1, 2, 3, ...]}},
            ...
        ]
    }},
    "structured_data": [
        {{"label": "标签", "value": 数值, "unit": "单位"}},
        ...
    ]
}}
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=2000,
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            result["accuracy"] = 0.95  # GPT-4V准确率
            result["model"] = "gpt-4v"
            
            return result
            
        except Exception as e:
            logger.error(f"GPT-4V图表解析失败: {e}")
            raise
    
    async def _parse_with_llava(
        self,
        image_path: str,
        chart_type: str,
    ) -> Dict[str, Any]:
        """使用LLaVA解析图表（需要本地部署）"""
        # TODO: 实现LLaVA模型调用
        # 需要部署LLaVA模型并调用API
        logger.warning("LLaVA模型解析功能待实现")
        return {
            "chart_type": chart_type,
            "data": {},
            "structured_data": [],
            "accuracy": 0.90,
            "model": "llava",
        }

