#!/usr/bin/env python3
"""
MCP Server Stdio Launcher
用于 Cursor、Claude Desktop 等工具的 stdio 传输方式
"""
import sys
import json
import asyncio
from typing import Optional

# 添加项目路径以便导入
sys.path.insert(0, '/Users/zhaojl/Development/Projects/Synapse/backend')

from mcp.protocol import JsonRpcRequest
from mcp.server import McpServerHandler


async def main(prefix: str):
    """
    主函数：从 stdin 读取 JSON-RPC 请求，输出到 stdout

    Args:
        prefix: MCP Server 前缀
    """
    # 导入数据（这里简化处理，实际应该连接数据库或 API）
    from main import mcp_servers_db, combinations_db

    # 查找对应的 MCP Server
    mcp_server = None
    for server in mcp_servers_db.values():
        if server.prefix == prefix:
            mcp_server = server
            break

    if not mcp_server:
        error_msg = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32001,
                "message": f"MCP Server with prefix '{prefix}' not found"
            },
            "id": None
        }
        print(json.dumps(error_msg), flush=True)
        sys.exit(1)

    # 创建 handler
    server_dict = mcp_server.model_dump()
    combinations_list = [comb.model_dump() for comb in combinations_db.values()]

    handler = McpServerHandler(
        server_config=server_dict,
        combinations=combinations_list
    )

    # 输出服务器就绪信息到 stderr（不影响 JSON-RPC 通信）
    print(f"MCP Server '{prefix}' ready on stdio", file=sys.stderr, flush=True)

    # 主循环：读取请求并处理
    while True:
        try:
            # 从 stdin 读取一行
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            # 解析 JSON-RPC 请求
            try:
                request_data = json.loads(line)
                rpc_request = JsonRpcRequest(**request_data)
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    },
                    "id": None
                }
                print(json.dumps(error_response), flush=True)
                continue

            # 处理请求
            response = await handler.handle_request(
                method=rpc_request.method,
                params=rpc_request.params,
                request_id=rpc_request.id
            )

            # 输出响应
            print(json.dumps(response), flush=True)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr, flush=True)
            break


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: mcp_stdio_server.py <prefix>", file=sys.stderr)
        print("Example: mcp_stdio_server.py synapse", file=sys.stderr)
        sys.exit(1)

    prefix = sys.argv[1]
    asyncio.run(main(prefix))
