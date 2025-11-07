"""
MCP Server - 封装项目工具和数据源为MCP协议
"""
import asyncio
import json
from typing import Any, Dict, List, Optional
from loguru import logger

from backend.services.report_service import ReportService
from backend.services.analysis_service import AnalysisService
from backend.services.report_generator import ReportGenerator
from backend.services.agents import AgentManager
from backend.services.voice_service import VoiceService
from backend.services.data_integration_service import DataIntegrationService
from backend.engine.retrieval import RetrievalEngine


class MCPServer:
    """
    MCP Server - 提供工具和资源
    
    工具列表：
    1. query_report_indicator - 查询财报指标
    2. compare_indicators - 对比指标
    3. analyze_attribution - 归因分析
    4. predict_trend - 趋势预测
    5. generate_report - 生成报告
    6. execute_agent - 执行智能体
    7. recognize_speech - 语音识别
    8. text_to_speech - 文本转语音
    9. integrate_data - 数据集成
    
    资源列表：
    1. knowledge_base - 知识库检索
    2. financial_data - 财务数据查询
    """
    
    def __init__(self):
        self.report_service = ReportService()
        self.analysis_service = AnalysisService()
        self.report_generator = ReportGenerator()
        self.agent_manager = AgentManager()
        self.voice_service = VoiceService()
        self.data_integration_service = DataIntegrationService()
        self.retrieval_engine = RetrievalEngine()
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        return [
            {
                "name": "query_report_indicator",
                "description": "查询财报指标数据",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "company": {
                            "type": "string",
                            "description": "公司名称"
                        },
                        "indicator": {
                            "type": "string",
                            "description": "指标名称（如：净利润、不良率、ROE等）"
                        },
                        "year": {
                            "type": "integer",
                            "description": "年份"
                        },
                        "quarter": {
                            "type": "string",
                            "description": "季度（可选，如：Q1、Q2、Q3、Q4）"
                        }
                    },
                    "required": ["company", "indicator", "year"]
                }
            },
            {
                "name": "compare_indicators",
                "description": "对比多个公司或时间段的指标",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "companies": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "公司名称列表"
                        },
                        "indicator": {
                            "type": "string",
                            "description": "指标名称"
                        },
                        "start_year": {
                            "type": "integer",
                            "description": "起始年份"
                        },
                        "end_year": {
                            "type": "integer",
                            "description": "结束年份"
                        }
                    },
                    "required": ["companies", "indicator", "start_year", "end_year"]
                }
            },
            {
                "name": "analyze_attribution",
                "description": "分析指标波动的归因",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "company": {
                            "type": "string",
                            "description": "公司名称"
                        },
                        "indicator": {
                            "type": "string",
                            "description": "指标名称"
                        },
                        "base_year": {
                            "type": "integer",
                            "description": "基准年份"
                        },
                        "target_year": {
                            "type": "integer",
                            "description": "目标年份"
                        }
                    },
                    "required": ["company", "indicator", "base_year", "target_year"]
                }
            },
            {
                "name": "predict_trend",
                "description": "预测财务指标趋势",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "company": {
                            "type": "string",
                            "description": "公司名称"
                        },
                        "indicator": {
                            "type": "string",
                            "description": "指标名称"
                        },
                        "years": {
                            "type": "integer",
                            "description": "预测年数（1-2年）"
                        }
                    },
                    "required": ["company", "indicator", "years"]
                }
            },
            {
                "name": "generate_report",
                "description": "生成财务分析报告",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "company": {
                            "type": "string",
                            "description": "公司名称"
                        },
                        "template_id": {
                            "type": "string",
                            "description": "报告模板ID"
                        },
                        "year": {
                            "type": "integer",
                            "description": "报告年份"
                        },
                        "include_charts": {
                            "type": "boolean",
                            "description": "是否包含图表",
                            "default": True
                        }
                    },
                    "required": ["company", "template_id", "year"]
                }
            },
            {
                "name": "execute_agent",
                "description": "执行智能体任务",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "智能体ID（boston_matrix、swot、credit_qa、retail_transformation、document_writing）"
                        },
                        "query": {
                            "type": "string",
                            "description": "查询内容"
                        },
                        "context": {
                            "type": "object",
                            "description": "上下文信息（可选）"
                        }
                    },
                    "required": ["agent_id", "query"]
                }
            },
            {
                "name": "recognize_speech",
                "description": "语音识别（将音频转换为文本）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "audio_data": {
                            "type": "string",
                            "description": "Base64编码的音频数据"
                        },
                        "language": {
                            "type": "string",
                            "description": "语言代码（zh-CN、zh-HK、en-US）",
                            "default": "zh-CN"
                        }
                    },
                    "required": ["audio_data"]
                }
            },
            {
                "name": "text_to_speech",
                "description": "文本转语音",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "要转换的文本"
                        },
                        "language": {
                            "type": "string",
                            "description": "语言代码",
                            "default": "zh-CN"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "integrate_data",
                "description": "集成数据（采集、清洗、导入）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "data_type": {
                            "type": "string",
                            "enum": ["bank_reports", "macro_data", "policy_files"],
                            "description": "数据类型"
                        },
                        "bank_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "银行名称列表（仅用于bank_reports）"
                        },
                        "years": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "年份列表"
                        },
                        "sources": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "数据源列表（仅用于policy_files）"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "开始日期（YYYY-MM-DD）"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "结束日期（YYYY-MM-DD）"
                        }
                    },
                    "required": ["data_type"]
                }
            },
            {
                "name": "deep_interpretation",
                "description": "深度财报解读（提取关键信息）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "company": {
                            "type": "string",
                            "description": "公司名称"
                        },
                        "year": {
                            "type": "integer",
                            "description": "年份"
                        }
                    },
                    "required": ["company", "year"]
                }
            }
        ]
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """列出所有可用资源"""
        return [
            {
                "uri": "knowledge://search",
                "name": "知识库检索",
                "description": "从知识库中检索相关信息",
                "mimeType": "application/json"
            },
            {
                "uri": "financial://data",
                "name": "财务数据",
                "description": "查询财务数据",
                "mimeType": "application/json"
            }
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用工具
        
        Args:
            name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        try:
            if name == "query_report_indicator":
                result = await self.report_service.get_indicator(
                    company=arguments["company"],
                    indicator=arguments["indicator"],
                    year=arguments["year"],
                    quarter=arguments.get("quarter"),
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            
            elif name == "compare_indicators":
                result = await self.report_service.compare_indicators(
                    companies=arguments["companies"],
                    indicator=arguments["indicator"],
                    start_year=arguments["start_year"],
                    end_year=arguments["end_year"],
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            
            elif name == "analyze_attribution":
                result = await self.analysis_service.analyze_attribution(
                    company=arguments["company"],
                    indicator=arguments["indicator"],
                    base_year=arguments["base_year"],
                    target_year=arguments["target_year"],
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            
            elif name == "predict_trend":
                result = await self.analysis_service.predict_trend(
                    company=arguments["company"],
                    indicator=arguments["indicator"],
                    years=arguments["years"],
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            
            elif name == "generate_report":
                result = await self.report_generator.generate_report(
                    company=arguments["company"],
                    template_id=arguments["template_id"],
                    year=arguments["year"],
                    include_charts=arguments.get("include_charts", True),
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            
            elif name == "execute_agent":
                agent = self.agent_manager.get_agent(arguments["agent_id"])
                if not agent:
                    raise ValueError(f"智能体 {arguments['agent_id']} 不存在")
                
                result = await agent.execute(
                    query=arguments["query"],
                    context=arguments.get("context"),
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            
            elif name == "recognize_speech":
                import base64
                audio_data = base64.b64decode(arguments["audio_data"])
                text = await self.voice_service.recognize_speech(
                    audio_data=audio_data,
                    language=arguments.get("language", "zh-CN"),
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                }
            
            elif name == "text_to_speech":
                audio_data = await self.voice_service.text_to_speech(
                    text=arguments["text"],
                    language=arguments.get("language", "zh-CN"),
                )
                import base64
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": audio_base64
                        }
                    ]
                }
            
            elif name == "integrate_data":
                data_type = arguments["data_type"]
                if data_type == "bank_reports":
                    result = await self.data_integration_service.integrate_bank_reports(
                        bank_names=arguments.get("bank_names"),
                        years=arguments.get("years"),
                    )
                elif data_type == "macro_data":
                    result = await self.data_integration_service.integrate_macro_data(
                        indicators=arguments.get("indicators"),
                        start_date=arguments.get("start_date"),
                        end_date=arguments.get("end_date"),
                    )
                elif data_type == "policy_files":
                    result = await self.data_integration_service.integrate_policy_files(
                        sources=arguments.get("sources"),
                        start_date=arguments.get("start_date"),
                        end_date=arguments.get("end_date"),
                    )
                else:
                    raise ValueError(f"不支持的数据类型: {data_type}")
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            
            elif name == "deep_interpretation":
                result = await self.analysis_service.deep_interpretation(
                    company=arguments["company"],
                    year=arguments["year"],
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            
            else:
                raise ValueError(f"未知工具: {name}")
                
        except Exception as e:
            logger.error(f"工具调用失败 {name}: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"错误: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        读取资源
        
        Args:
            uri: 资源URI
            
        Returns:
            资源内容
        """
        try:
            if uri.startswith("knowledge://"):
                # 知识库检索
                query = uri.replace("knowledge://search?query=", "")
                docs = await self.retrieval_engine.retrieve(query=query, top_k=10)
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(docs, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            
            elif uri.startswith("financial://"):
                # 财务数据查询
                # 解析URI参数
                params = {}
                if "?" in uri:
                    query_str = uri.split("?")[1]
                    for param in query_str.split("&"):
                        key, value = param.split("=")
                        params[key] = value
                
                # 查询数据
                if "company" in params and "indicator" in params:
                    result = await self.report_service.get_indicator(
                        company=params["company"],
                        indicator=params["indicator"],
                        year=int(params.get("year", "2023")),
                    )
                    return {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": "application/json",
                                "text": json.dumps(result, ensure_ascii=False, indent=2)
                            }
                        ]
                    }
            
            else:
                raise ValueError(f"未知资源URI: {uri}")
                
        except Exception as e:
            logger.error(f"资源读取失败 {uri}: {e}")
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/plain",
                        "text": f"错误: {str(e)}"
                    }
                ]
            }

