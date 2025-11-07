"""
MCP Client - 与MCP Server通信的客户端
"""
import json
from typing import Dict, Any, List, Optional
from loguru import logger

from backend.mcp.server import MCPServer


class MCPClient:
    """
    MCP Client - 封装与MCP Server的通信
    
    作为Coordinator和MCP Server之间的桥梁
    """
    
    def __init__(self, server: Optional[MCPServer] = None):
        """
        初始化MCP Client
        
        Args:
            server: MCP Server实例（如果为None，则创建新的）
        """
        self.server = server or MCPServer()
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._resources_cache: Optional[List[Dict[str, Any]]] = None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        if self._tools_cache is None:
            self._tools_cache = self.server.list_tools()
        return self._tools_cache
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """列出所有可用资源"""
        if self._resources_cache is None:
            self._resources_cache = self.server.list_resources()
        return self._resources_cache
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        调用工具
        
        Args:
            name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        try:
            result = await self.server.call_tool(name, arguments)
            
            # 解析结果
            if result.get("isError"):
                logger.error(f"工具 {name} 执行失败: {result.get('content', [{}])[0].get('text', '')}")
                raise Exception(result.get("content", [{}])[0].get("text", "工具执行失败"))
            
            # 提取文本内容
            content = result.get("content", [])
            if content and len(content) > 0:
                text = content[0].get("text", "")
                try:
                    # 尝试解析为JSON
                    return json.loads(text)
                except json.JSONDecodeError:
                    # 如果不是JSON，返回文本
                    return {"result": text}
            
            return result
            
        except Exception as e:
            logger.error(f"MCP工具调用失败 {name}: {e}")
            raise
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        读取资源
        
        Args:
            uri: 资源URI
            
        Returns:
            资源内容
        """
        try:
            result = await self.server.read_resource(uri)
            
            # 解析资源内容
            contents = result.get("contents", [])
            if contents and len(contents) > 0:
                text = contents[0].get("text", "")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"content": text}
            
            return result
            
        except Exception as e:
            logger.error(f"MCP资源读取失败 {uri}: {e}")
            raise
    
    def get_tool_description(self, name: str) -> Optional[Dict[str, Any]]:
        """获取工具描述"""
        tools = self._tools_cache or self.server.list_tools()
        for tool in tools:
            if tool["name"] == name:
                return tool
        return None
    
    async def search_knowledge(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        搜索知识库（便捷方法）
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        uri = f"knowledge://search?query={query}"
        result = await self.read_resource(uri)
        if isinstance(result, list):
            return result[:top_k]
        elif isinstance(result, dict) and "content" in result:
            # 如果返回的是单个内容，尝试解析
            try:
                parsed = json.loads(result["content"])
                if isinstance(parsed, list):
                    return parsed[:top_k]
            except:
                pass
        return []

