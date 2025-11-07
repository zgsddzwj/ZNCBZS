"""
MCP (Model Context Protocol) 模块
提供MCP Server和Client实现
"""
from backend.mcp.server import MCPServer
from backend.mcp.client import MCPClient

__all__ = ["MCPServer", "MCPClient"]

