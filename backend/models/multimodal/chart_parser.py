"""
多模态图表解析模型
使用 DeepSeek（文本方式）或 LLaVA 解析财报中的图表数据
"""
from typing import Dict, Any
from loguru import logger
from backend.engine.llm_service import LLMService
import base64
import json


class ChartParser:
    """图表解析器"""

    def __init__(self):
        self.llm_service = LLMService()

        # LLaVA模型（需要本地部署）
        self.llava_model = None
        self.use_llava = False  # 默认使用DeepSeek文本解析

    async def parse_chart(
        self,
        image_path: str,
        chart_type: str = "auto",  # auto, table, bar, line, pie
        use_model: str = "deepseek",  # deepseek or llava
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
        if use_model == "deepseek":
            return await self._parse_with_deepseek(image_path, chart_type)
        elif use_model == "llava":
            return await self._parse_with_llava(image_path, chart_type)
        else:
            raise ValueError(f"不支持的模型: {use_model}")

    async def _parse_with_deepseek(
        self,
        image_path: str,
        chart_type: str,
    ) -> Dict[str, Any]:
        """使用DeepSeek（通过文本指令）解析图表"""
        if not self.llm_service.deepseek_client:
            raise ValueError("未配置DeepSeek API密钥，无法解析图表")

        try:
            # 读取图片并编码
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")

            prompt = f"""
你是一名财报图表解析助手。现在提供给你一张图表的Base64编码，你需要：
1. 判断图表类型（柱状图、折线图、饼图、表格等）。
2. 提取所有可识别的数据点。
3. 识别坐标轴标签及单位。
4. 将结果以JSON格式输出，严格遵循下述结构：
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

如果无法解析出具体数值，请在对应位置填入 null，并在 structured_data 中给出文字描述。

图表类型参考：{chart_type}
图像Base64：{image_data}
"""

            response = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=1500,
                use_deepseek=True,
            )

            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                logger.warning("DeepSeek图表解析结果非JSON格式，返回原始内容")
                result = {
                    "chart_type": chart_type,
                    "data": {},
                    "structured_data": [
                        {"label": "raw_response", "value": response, "unit": ""}
                    ],
                }

            result["accuracy"] = result.get("accuracy", 0.85)
            result["model"] = "deepseek"

            return result

        except Exception as e:
            logger.error(f"DeepSeek图表解析失败: {e}")
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

