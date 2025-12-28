# backend/api/mcp_protocol.py
"""
MCP 协议端点（HTTP + SSE 传输）
"""
import asyncio
import json
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from mcp.protocol import JsonRpcRequest, McpError, create_error_response
from mcp.server import McpServerHandler
from mcp.session import session_manager
from models.combination import Combination
from models.mcp_server import McpServer
from repositories.combination_repository import CombinationRepository
from repositories.mcp_server_repository import McpServerRepository

router = APIRouter(prefix="/mcp", tags=["mcp-protocol"])


@router.api_route("/{prefix}", methods=["GET", "POST"])
async def mcp_endpoint(prefix: str, request: Request, db: AsyncSession = Depends(get_db)):
    """
    标准 MCP 协议端点（HTTP + SSE 传输）

    符合 MCP 官方标准，同时支持 GET 和 POST 请求：
    - GET: 打开 SSE 流接收服务器推送消息
    - POST: 发送 JSON-RPC 请求并获取响应

    支持的 HTTP 头：
    - Mcp-Session-Id: 会话标识（POST 请求必需）
    - MCP-Protocol-Version: 协议版本（必需）
    - Accept: text/event-stream（GET 请求）

    Claude Desktop 配置示例：
    {
      "mcpServers": {
        "synapse": {
          "url": "http://localhost:8000/mcp/synapse"
        }
      }
    }
    """
    # 查找对应的 MCP Server
    server_repo = McpServerRepository(db)
    mcp_server = await server_repo.get_by_prefix(prefix)

    if not mcp_server:
        raise HTTPException(status_code=404, detail=f"MCP Server with prefix '{prefix}' not found")

    # 检查服务状态
    if mcp_server.status != "active":
        raise HTTPException(status_code=403, detail=f"MCP Server '{prefix}' is inactive")

    # 获取协议版本（如果提供）
    protocol_version = request.headers.get("MCP-Protocol-Version", "2024-11-05")

    # GET 请求：返回 SSE 流
    if request.method == "GET":
        # 获取或创建会话
        session_id = request.headers.get("Mcp-Session-Id")

        if session_id:
            # 验证现有会话
            session = await session_manager.get_session(session_id)
            if not session or session.prefix != prefix:
                raise HTTPException(status_code=404, detail="Invalid session ID")
        else:
            # 创建新会话
            session = await session_manager.create_session(prefix)

        async def event_generator():
            """SSE 事件生成器"""
            try:
                # 发送连接确认
                yield {
                    "event": "endpoint",
                    "data": json.dumps({
                        "jsonrpc": "2.0",
                        "method": "endpoint",
                        "params": {
                            "endpoint": f"/mcp/{prefix}"
                        }
                    })
                }

                # 持续监听队列中的消息
                while True:
                    try:
                        # 等待消息，设置超时以便定期发送 keepalive
                        message = await asyncio.wait_for(
                            session.queue.get(),
                            timeout=30.0  # 30秒超时
                        )

                        # 发送消息（可以是通知、请求或响应）
                        yield {
                            "event": "message",
                            "data": json.dumps(message)
                        }

                        # 更新会话活动时间
                        session.update_activity()

                    except asyncio.TimeoutError:
                        # 发送 keepalive 心跳
                        yield {
                            "event": "ping",
                            "data": json.dumps({"type": "ping"})
                        }
                        session.update_activity()

            except asyncio.CancelledError:
                # 客户端断开连接
                print(f"SSE connection closed for session {session.session_id}")
            finally:
                # 清理会话
                await session_manager.remove_session(session.session_id)

        # 返回 SSE 响应，带会话 ID 头
        response = EventSourceResponse(event_generator())
        response.headers["Mcp-Session-Id"] = session.session_id
        response.headers["MCP-Protocol-Version"] = protocol_version
        return response

    # POST 请求：处理 JSON-RPC 请求
    else:
        # 解析 JSON-RPC 请求
        try:
            body = await request.json()
            rpc_request = JsonRpcRequest(**body)
        except Exception as e:
            error_response = create_error_response(
                code=McpError.PARSE_ERROR,
                message=f"Invalid JSON-RPC request: {str(e)}",
                id=None
            )
            response = JSONResponse(content=error_response)
            response.headers["MCP-Protocol-Version"] = protocol_version
            return response

        # 获取所有组合（用于 McpServerHandler）
        comb_repo = CombinationRepository(db)
        all_combinations = await comb_repo.get_all()
        combinations_list = [Combination.from_orm(c).model_dump() for c in all_combinations]

        # 特殊处理 initialize 请求
        if rpc_request.method == "initialize":
            # 创建新会话
            session = await session_manager.create_session(prefix)

            # 创建 MCP Server Handler
            server_dict = McpServer.from_orm(mcp_server).model_dump()

            handler = McpServerHandler(
                server_config=server_dict,
                combinations=combinations_list
            )

            # 处理初始化请求
            result = await handler.handle_request(
                method=rpc_request.method,
                params=rpc_request.params,
                request_id=rpc_request.id
            )

            # 返回响应，带会话 ID 头
            response = JSONResponse(content=result)
            response.headers["Mcp-Session-Id"] = session.session_id
            response.headers["MCP-Protocol-Version"] = protocol_version
            return response

        # 其他请求需要验证会话
        session_id = request.headers.get("Mcp-Session-Id")
        if not session_id:
            error_response = create_error_response(
                code=McpError.INVALID_REQUEST,
                message="Missing Mcp-Session-Id header",
                id=rpc_request.id
            )
            response = JSONResponse(content=error_response, status_code=400)
            response.headers["MCP-Protocol-Version"] = protocol_version
            return response

        # 验证会话
        session = await session_manager.get_session(session_id)
        if not session or session.prefix != prefix:
            error_response = create_error_response(
                code=McpError.INVALID_REQUEST,
                message="Invalid session ID",
                id=rpc_request.id
            )
            response = JSONResponse(content=error_response, status_code=404)
            response.headers["MCP-Protocol-Version"] = protocol_version
            return response

        # 更新会话活动时间
        session.update_activity()

        # 创建 MCP Server Handler
        server_dict = McpServer.from_orm(mcp_server).model_dump()

        handler = McpServerHandler(
            server_config=server_dict,
            combinations=combinations_list
        )

        # 处理请求
        result = await handler.handle_request(
            method=rpc_request.method,
            params=rpc_request.params,
            request_id=rpc_request.id
        )

        # 返回响应
        response = JSONResponse(content=result)
        response.headers["Mcp-Session-Id"] = session_id
        response.headers["MCP-Protocol-Version"] = protocol_version
        return response


@router.get("/{prefix}/config")
async def get_mcp_config(prefix: str, db: AsyncSession = Depends(get_db)):
    """
    获取 MCP Server 的配置信息

    返回可以直接复制到 AI 工具配置文件中的标准配置
    """
    # 查找对应的 MCP Server
    repo = McpServerRepository(db)
    mcp_server = await repo.get_by_prefix(prefix)

    if not mcp_server:
        raise HTTPException(status_code=404, detail=f"MCP Server with prefix '{prefix}' not found")

    # 生成标准 HTTP + SSE 配置（单一端点）
    config = {
        mcp_server.prefix: {
            "type": "sse",
            "url": f"http://localhost:8000/mcp/{mcp_server.prefix}"
        }
    }

    example = {
        "mcpServers": config
    }

    return {
        "config": config,
        "example": example,
        "endpoint": f"http://localhost:8000/mcp/{mcp_server.prefix}",
        "instructions": {
            "claude_desktop": "~/Library/Application Support/Claude/claude_desktop_config.json (macOS)",
            "cursor": "Settings → MCP Servers"
        }
    }
