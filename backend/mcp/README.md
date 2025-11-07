# MCP (Model Context Protocol) 架构说明

## 概述

本项目已改造为基于 **MCP (Model Context Protocol)** 的架构，实现了标准化的工具调用和数据源访问接口。

## 架构组件

### 1. MCP Server (`backend/mcp/server.py`)

MCP Server 封装了项目的所有工具和数据源，提供标准化的接口。

#### 可用工具列表

| 工具名称 | 描述 | 用途 |
|---------|------|------|
| `query_report_indicator` | 查询财报指标 | 查询指定公司的财务指标数据 |
| `compare_indicators` | 对比指标 | 对比多个公司或时间段的指标 |
| `analyze_attribution` | 归因分析 | 分析指标波动的归因 |
| `predict_trend` | 趋势预测 | 预测财务指标趋势 |
| `generate_report` | 生成报告 | 生成财务分析报告 |
| `execute_agent` | 执行智能体 | 执行预置或自定义智能体 |
| `recognize_speech` | 语音识别 | 将音频转换为文本 |
| `text_to_speech` | 文本转语音 | 将文本转换为音频 |
| `integrate_data` | 数据集成 | 采集、清洗、导入数据 |
| `deep_interpretation` | 深度财报解读 | 提取财报关键信息 |

#### 可用资源列表

| 资源URI | 描述 | 用途 |
|---------|------|------|
| `knowledge://search` | 知识库检索 | 从知识库中检索相关信息 |
| `financial://data` | 财务数据 | 查询财务数据 |

### 2. MCP Client (`backend/mcp/client.py`)

MCP Client 作为 Coordinator 和 MCP Server 之间的桥梁，提供便捷的工具调用接口。

#### 主要方法

- `list_tools()`: 列出所有可用工具
- `list_resources()`: 列出所有可用资源
- `call_tool(name, arguments)`: 调用指定工具
- `read_resource(uri)`: 读取指定资源
- `search_knowledge(query, top_k)`: 搜索知识库（便捷方法）

### 3. Coordinator 集成 (`backend/engine/coordinator.py`)

Coordinator 已集成 MCP Client，通过 MCP 协议调用工具和数据源。

#### 工作流程

```
用户查询
  ↓
意图理解（LLM）
  ↓
判断是否需要调用工具
  ↓
调用MCP工具（如果需要）
  ↓
检索知识库（MCP资源）
  ↓
生成回答（LLM + 工具结果 + 知识库）
  ↓
返回结果
```

## 使用示例

### 1. 直接使用 MCP Client

```python
from backend.mcp.client import MCPClient

# 创建MCP Client
client = MCPClient()

# 列出所有工具
tools = await client.list_tools()

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

### 2. 通过 Coordinator 使用（推荐）

```python
from backend.engine.coordinator import Coordinator

# 创建Coordinator（默认启用MCP）
coordinator = Coordinator(use_mcp=True)

# 处理查询（自动调用MCP工具）
result = await coordinator.process_query(
    "招商银行2023年净利润是多少？"
)
```

### 3. 禁用 MCP（兼容模式）

```python
# 创建Coordinator（禁用MCP，使用原有方式）
coordinator = Coordinator(use_mcp=False)
```

## 工具定义格式

每个工具都遵循 MCP 标准格式：

```json
{
  "name": "tool_name",
  "description": "工具描述",
  "inputSchema": {
    "type": "object",
    "properties": {
      "param1": {
        "type": "string",
        "description": "参数描述"
      }
    },
    "required": ["param1"]
  }
}
```

## 资源定义格式

每个资源都遵循 MCP 标准格式：

```json
{
  "uri": "resource://type",
  "name": "资源名称",
  "description": "资源描述",
  "mimeType": "application/json"
}
```

## 优势

1. **标准化接口**: 所有工具和数据源使用统一的 MCP 协议
2. **易于扩展**: 新增工具只需在 MCP Server 中注册
3. **工具热插拔**: 支持动态加载和卸载工具
4. **第三方集成**: 可以轻松集成第三方 MCP 工具
5. **类型安全**: 使用 JSON Schema 定义工具参数，确保类型安全

## 扩展指南

### 添加新工具

1. 在 `MCPServer.list_tools()` 中添加工具定义
2. 在 `MCPServer.call_tool()` 中添加工具实现
3. 工具会自动在 Coordinator 中可用

### 添加新资源

1. 在 `MCPServer.list_resources()` 中添加资源定义
2. 在 `MCPServer.read_resource()` 中添加资源读取逻辑
3. 资源可以通过 MCP Client 访问

## 配置

MCP 架构默认启用，可以通过以下方式配置：

```python
# 启用MCP（默认）
coordinator = Coordinator(use_mcp=True)

# 禁用MCP（兼容模式）
coordinator = Coordinator(use_mcp=False)
```

## 相关文档

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [项目架构文档](../docs/INTERVIEW_01_项目架构.md)

