# backend/mcp/server.py
"""
MCP Server 核心逻辑
处理工具列表、工具调用等
"""
from typing import Dict, List, Any, Optional
import httpx
from mcp.protocol import (
    McpTool,
    convert_openapi_endpoint_to_mcp_tool,
    create_error_response,
    create_success_response,
    McpError
)


class McpServerHandler:
    """MCP Server 请求处理器"""

    def __init__(
        self,
        server_config: Dict[str, Any],
        combinations: List[Dict[str, Any]]
    ):
        """
        初始化 MCP Server

        Args:
            server_config: MCP Server 配置（包含 id, name, prefix, combination_ids 等）
            combinations: 所有组合的列表
        """
        self.server_config = server_config
        self.combinations = combinations
        self.prefix = server_config.get("prefix", "")

    def get_tools(self) -> List[McpTool]:
        """
        获取所有可用工具列表
        聚合所有组合中的接口并转换为 MCP 工具
        """
        tools = []
        combination_ids = self.server_config.get("combination_ids", [])

        for combination in self.combinations:
            # 只处理当前 MCP Server 包含的组合
            if combination.get("id") not in combination_ids:
                continue

            # 只处理 active 状态的组合
            if combination.get("status") != "active":
                continue

            # 遍历组合中的所有端点
            endpoints = combination.get("endpoints", [])
            for endpoint in endpoints:
                try:
                    tool = convert_openapi_endpoint_to_mcp_tool(
                        endpoint,
                        prefix=self.prefix
                    )
                    tools.append(tool)
                except Exception as e:
                    print(f"Failed to convert endpoint to tool: {e}")
                    continue

        return tools

    async def handle_tools_list(self, request_id: Optional[int | str] = None) -> Dict[str, Any]:
        """
        处理 tools/list 请求

        Returns:
            JSON-RPC 响应
        """
        try:
            tools = self.get_tools()
            tools_dict = [tool.model_dump() for tool in tools]

            return create_success_response(
                result={"tools": tools_dict},
                id=request_id
            )
        except Exception as e:
            return create_error_response(
                code=McpError.INTERNAL_ERROR,
                message=f"Failed to list tools: {str(e)}",
                id=request_id
            )

    async def handle_tools_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        request_id: Optional[int | str] = None
    ) -> Dict[str, Any]:
        """
        处理 tools/call 请求
        实际调用后端 API

        Args:
            tool_name: 工具名称
            arguments: 工具参数
            request_id: 请求 ID

        Returns:
            JSON-RPC 响应
        """
        try:
            # 从参数中提取必要信息
            method = arguments.get("_method", "GET")
            path = arguments.get("_path", "")
            service_url = arguments.get("_serviceUrl", "")

            if not service_url or not path:
                return create_error_response(
                    code=McpError.INVALID_PARAMS,
                    message="Missing required parameters: _serviceUrl or _path",
                    id=request_id
                )

            # 构建完整 URL
            # 需要处理 service_url 可能是完整的 OpenAPI spec URL 的情况
            # 这里简化处理，假设 service_url 是 API base URL
            # 实际应该解析 OpenAPI spec 获取 servers 信息
            base_url = service_url.replace("/openapi.json", "").replace("/swagger.json", "")
            full_url = f"{base_url}{path}"

            # 准备请求参数
            # 过滤掉内部参数（以 _ 开头的）
            request_params = {
                k: v for k, v in arguments.items()
                if not k.startswith("_")
            }

            # 执行 HTTP 请求
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(full_url, params=request_params)
                elif method.upper() == "POST":
                    response = await client.post(full_url, json=request_params)
                elif method.upper() == "PUT":
                    response = await client.put(full_url, json=request_params)
                elif method.upper() == "DELETE":
                    response = await client.delete(full_url, params=request_params)
                elif method.upper() == "PATCH":
                    response = await client.patch(full_url, json=request_params)
                else:
                    return create_error_response(
                        code=McpError.INVALID_PARAMS,
                        message=f"Unsupported HTTP method: {method}",
                        id=request_id
                    )

            # 返回 API 响应
            try:
                result_data = response.json()
            except Exception:
                result_data = {"text": response.text, "status_code": response.status_code}

            return create_success_response(
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": str(result_data)
                        }
                    ]
                },
                id=request_id
            )

        except httpx.TimeoutException:
            return create_error_response(
                code=McpError.INTERNAL_ERROR,
                message="API request timeout",
                id=request_id
            )
        except httpx.RequestError as e:
            return create_error_response(
                code=McpError.INTERNAL_ERROR,
                message=f"API request failed: {str(e)}",
                id=request_id
            )
        except Exception as e:
            return create_error_response(
                code=McpError.INTERNAL_ERROR,
                message=f"Tool execution failed: {str(e)}",
                id=request_id
            )

    async def handle_initialize(self, request_id: Optional[int | str] = None) -> Dict[str, Any]:
        """
        处理 initialize 请求

        Returns:
            JSON-RPC 响应
        """
        return create_success_response(
            result={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": self.server_config.get("name", "Synapse MCP Server"),
                    "version": "0.1.0"
                }
            },
            id=request_id
        )

    async def handle_request(self, method: str, params: Optional[Dict[str, Any]], request_id: Optional[int | str]) -> Dict[str, Any]:
        """
        统一处理 MCP 请求

        Args:
            method: RPC 方法名
            params: 请求参数
            request_id: 请求 ID

        Returns:
            JSON-RPC 响应
        """
        if method == "initialize":
            return await self.handle_initialize(request_id)
        elif method == "tools/list":
            return await self.handle_tools_list(request_id)
        elif method == "tools/call":
            if not params:
                return create_error_response(
                    code=McpError.INVALID_PARAMS,
                    message="Missing params for tools/call",
                    id=request_id
                )
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if not tool_name:
                return create_error_response(
                    code=McpError.INVALID_PARAMS,
                    message="Missing tool name",
                    id=request_id
                )
            return await self.handle_tools_call(tool_name, arguments, request_id)
        else:
            return create_error_response(
                code=McpError.METHOD_NOT_FOUND,
                message=f"Method not found: {method}",
                id=request_id
            )
