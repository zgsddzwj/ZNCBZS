# MCP架构改造说明

## 改造概述

项目已成功改造为基于 **MCP (Model Context Protocol)** 的架构，实现了标准化的工具调用和数据源访问接口。

## 改造内容

### 1. 新增模块

#### `backend/mcp/` 目录
- `__init__.py`: MCP模块导出
- `server.py`: MCP Server实现，封装所有工具和数据源
- `client.py`: MCP Client实现，提供工具调用接口
- `README.md`: MCP架构使用文档

### 2. 修改的模块

#### `backend/engine/coordinator.py`
- 集成MCP Client
- 添加`_call_mcp_tools()`方法：根据意图调用MCP工具
- 添加`_call_tool_by_intent()`方法：基于意图直接调用工具（备用方案）
- 修改`_generate_answer()`方法：支持工具调用结果
- 支持MCP架构开关（`use_mcp`参数）

#### `requirements.txt`
- 添加`mcp==0.9.0`依赖

#### `README.md`
- 添加MCP架构说明章节

## 架构对比

### 改造前（直接调用）

```
Coordinator
  ├── 直接调用 ReportService
  ├── 直接调用 AnalysisService
  ├── 直接调用 ReportGenerator
  └── 直接调用 AgentManager
```

### 改造后（MCP架构）

```
Coordinator
  └── MCP Client
        └── MCP Server
              ├── 工具：query_report_indicator
              ├── 工具：compare_indicators
              ├── 工具：analyze_attribution
              ├── 工具：predict_trend
              ├── 工具：generate_report
              ├── 工具：execute_agent
              ├── 工具：recognize_speech
              ├── 工具：text_to_speech
              ├── 工具：integrate_data
              ├── 工具：deep_interpretation
              ├── 资源：knowledge://search
              └── 资源：financial://data
```

## 可用工具列表

| 工具名称 | 对应服务 | 功能 |
|---------|---------|------|
| `query_report_indicator` | ReportService | 查询财报指标 |
| `compare_indicators` | ReportService | 对比指标 |
| `analyze_attribution` | AnalysisService | 归因分析 |
| `predict_trend` | AnalysisService | 趋势预测 |
| `generate_report` | ReportGenerator | 生成报告 |
| `execute_agent` | AgentManager | 执行智能体 |
| `recognize_speech` | VoiceService | 语音识别 |
| `text_to_speech` | VoiceService | 文本转语音 |
| `integrate_data` | DataIntegrationService | 数据集成 |
| `deep_interpretation` | AnalysisService | 深度财报解读 |

## 可用资源列表

| 资源URI | 功能 |
|---------|------|
| `knowledge://search?query=...` | 知识库检索 |
| `financial://data?company=...&indicator=...&year=...` | 财务数据查询 |

## 使用方式

### 1. 默认启用MCP（推荐）

```python
from backend.engine.coordinator import Coordinator

# 默认启用MCP
coordinator = Coordinator(use_mcp=True)

# 处理查询（自动调用MCP工具）
result = await coordinator.process_query("招商银行2023年净利润是多少？")
```

### 2. 禁用MCP（兼容模式）

```python
# 禁用MCP，使用原有直接调用方式
coordinator = Coordinator(use_mcp=False)
```

### 3. 直接使用MCP Client

```python
from backend.mcp.client import MCPClient

client = MCPClient()

# 调用工具
result = await client.call_tool(
    "query_report_indicator",
    {
        "company": "招商银行",
        "indicator": "净利润",
        "year": 2023
    }
)

# 搜索知识库
docs = await client.search_knowledge("银行不良率", top_k=10)
```

## 优势

1. **标准化接口**: 所有工具使用统一的MCP协议，便于维护和扩展
2. **工具热插拔**: 支持动态添加和移除工具
3. **第三方集成**: 可以轻松集成第三方MCP工具
4. **类型安全**: 使用JSON Schema定义工具参数
5. **向后兼容**: 支持禁用MCP，保持原有功能

## 扩展指南

### 添加新工具

1. 在`MCPServer.list_tools()`中添加工具定义（JSON Schema）
2. 在`MCPServer.call_tool()`中添加工具实现
3. 工具会自动在Coordinator中可用

### 添加新资源

1. 在`MCPServer.list_resources()`中添加资源定义
2. 在`MCPServer.read_resource()`中添加资源读取逻辑
3. 资源可以通过MCP Client访问

## 测试建议

1. **单元测试**: 测试每个MCP工具的功能
2. **集成测试**: 测试Coordinator通过MCP调用工具
3. **兼容性测试**: 测试禁用MCP时的向后兼容性

## 相关文档

- [MCP架构使用文档](../backend/mcp/README.md)
- [项目架构文档](./INTERVIEW_01_项目架构.md)

