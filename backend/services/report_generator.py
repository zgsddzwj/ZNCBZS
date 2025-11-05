"""
报告生成服务 - 生成分析报告并导出
"""
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from loguru import logger
from backend.engine.llm_service import LLMService


class ReportGenerator:
    """报告生成服务"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.templates_dir = Path("./templates")
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_report(
        self,
        template_name: str,
        data: Dict[str, Any],
        format: str = "pdf",
    ) -> Dict[str, Any]:
        """
        生成分析报告
        
        Args:
            template_name: 模板名称（如"信贷审批摘要"）
            data: 报告数据
            format: 导出格式（pdf, word, excel）
        """
        try:
            # 加载模板
            template = self._load_template(template_name)
            
            # 使用LLM生成报告内容
            report_content = await self._generate_content(template, data)
            
            # 生成图表
            charts = await self._generate_charts(data)
            
            # 导出文件
            file_path = await self._export_report(
                content=report_content,
                charts=charts,
                format=format,
            )
            
            return {
                "report_id": f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "template": template_name,
                "content": report_content,
                "charts": charts,
                "file_path": file_path,
                "format": format,
            }
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            raise
    
    def _load_template(self, template_name: str) -> str:
        """加载报告模板"""
        template_path = self.templates_dir / f"{template_name}.jinja2"
        
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        else:
            # 返回默认模板
            return self._get_default_template(template_name)
    
    def _get_default_template(self, template_name: str) -> str:
        """获取默认模板"""
        templates = {
            "信贷审批摘要": """
# {company} {year}年财报摘要

## 核心指标
{indicators}

## 风险评估
{risk_assessment}

## 建议
{recommendation}
""",
            "季度业绩分析": """
# {company} {period}季度业绩分析报告

## 业绩概况
{overview}

## 关键指标分析
{indicator_analysis}

## 趋势分析
{trend_analysis}

## 结论
{conclusion}
""",
        }
        
        return templates.get(template_name, templates["季度业绩分析"])
    
    async def _generate_content(
        self,
        template: str,
        data: Dict[str, Any],
    ) -> str:
        """使用LLM生成报告内容"""
        prompt = f"""
基于以下数据和模板，生成专业的财务分析报告。

模板：
{template}

数据：
{data}

要求：
1. 严格按照模板格式
2. 内容专业、准确
3. 数据引用要精确
4. 结论要明确
"""
        
        content = await self.llm_service.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=3000,
        )
        
        return content
    
    async def _generate_charts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成图表数据"""
        # 这里应该使用图表库（如matplotlib、plotly）生成图表
        # 简化版返回图表配置
        charts = []
        
        if "time_series" in data:
            charts.append({
                "type": "line",
                "title": "趋势图",
                "data": data["time_series"],
            })
        
        if "comparison" in data:
            charts.append({
                "type": "bar",
                "title": "对比图",
                "data": data["comparison"],
            })
        
        return charts
    
    async def _export_report(
        self,
        content: str,
        charts: List[Dict[str, Any]],
        format: str,
    ) -> str:
        """导出报告文件"""
        output_dir = Path("./data/reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = output_dir / f"report_{timestamp}.{format}"
        
        if format == "pdf":
            # 使用报告库生成PDF（如reportlab）
            # 简化版，实际应该生成PDF
            file_path.write_text(content, encoding="utf-8")
        elif format == "word":
            # 使用python-docx生成Word
            from docx import Document
            doc = Document()
            doc.add_paragraph(content)
            doc.save(str(file_path))
        elif format == "excel":
            # 使用openpyxl生成Excel
            import pandas as pd
            df = pd.DataFrame({"内容": [content]})
            df.to_excel(file_path, index=False)
        
        return str(file_path)

