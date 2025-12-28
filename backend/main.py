# backend/main.py
import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path as PathLib
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Path, Request
from sse_starlette.sse import EventSourceResponse
from starlette.middleware.cors import CORSMiddleware

from mcp.openapi_to_mcp import convert_openapi_to_mcp
from mcp.protocol import JsonRpcRequest, McpError, create_error_response
from mcp.server import McpServerHandler
from mcp.session import session_manager
from models.combination import Combination, CombinationCreate, CombinationUpdate
from models.mcp_server import McpServer, McpServerCreate, McpServerUpdate
from services.openapi_fetcher import fetch_openapi_spec, extract_api_endpoints


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 启动和关闭时的操作"""
    # 启动时加载持久化数据
    load_combinations()
    load_mcp_servers()
    init_sample_data()
    yield
    # 关闭时可以添加清理操作（如果需要）


app = FastAPI(
    title="Synapse MCP Gateway",
    description="Converts OpenAPI specifications to AI Agent callable tools (MCP format).",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据持久化路径
DATA_DIR = PathLib(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
COMBINATIONS_FILE = DATA_DIR / "combinations.json"
MCP_SERVERS_FILE = DATA_DIR / "mcp_servers.json"

# Mock OpenAPI spec for development/testing if no URL is provided
MOCK_OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Mock API", "version": "1.0.0"},
    "paths": {
        "/items": {
            "get": {
                "operationId": "getItems",
                "summary": "Get a list of items",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer"},
                        "description": "Limit the number of items returned"
                    }
                ],
                "responses": {
                    "200": {"description": "A list of items"}
                }
            },
            "post": {
                "operationId": "createItem",
                "summary": "Create a new item",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "price": {"type": "number"}
                                },
                                "required": ["name"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Item created"}
                }
            }
        }
    }
}

# 内存存储（临时方案，后续可替换为数据库）
combinations_db: dict[int, Combination] = {}
combination_id_counter = 1

mcp_servers_db: dict[int, McpServer] = {}
mcp_server_id_counter = 1


# 数据持久化函数
def save_combinations():
    """保存组合数据到 JSON 文件"""
    data = {
        "counter": combination_id_counter,
        "combinations": {
            str(id): comb.model_dump(mode='json')
            for id, comb in combinations_db.items()
        }
    }
    with open(COMBINATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def load_combinations():
    """从 JSON 文件加载组合数据"""
    global combinations_db, combination_id_counter

    if not COMBINATIONS_FILE.exists():
        return

    try:
        with open(COMBINATIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        combination_id_counter = data.get("counter", 1)
        combinations_db = {
            int(id): Combination(**comb_data)
            for id, comb_data in data.get("combinations", {}).items()
        }
        print(f"Loaded {len(combinations_db)} combinations from {COMBINATIONS_FILE}")
    except Exception as e:
        print(f"Failed to load combinations: {e}")


def save_mcp_servers():
    """保存 MCP 服务数据到 JSON 文件"""
    data = {
        "counter": mcp_server_id_counter,
        "servers": {
            str(id): server.model_dump(mode='json')
            for id, server in mcp_servers_db.items()
        }
    }
    with open(MCP_SERVERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def load_mcp_servers():
    """从 JSON 文件加载 MCP 服务数据"""
    global mcp_servers_db, mcp_server_id_counter

    if not MCP_SERVERS_FILE.exists():
        return

    try:
        with open(MCP_SERVERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        mcp_server_id_counter = data.get("counter", 1)
        mcp_servers_db = {
            int(id): McpServer(**server_data)
            for id, server_data in data.get("servers", {}).items()
        }
        print(f"Loaded {len(mcp_servers_db)} MCP servers from {MCP_SERVERS_FILE}")
    except Exception as e:
        print(f"Failed to load MCP servers: {e}")


# 添加示例数据（可选，用于测试）
def init_sample_data():
    """初始化示例数据（仅在数据文件不存在时）"""
    global combination_id_counter, mcp_server_id_counter

    # 只有在没有已保存数据时才初始化示例数据
    if COMBINATIONS_FILE.exists() or MCP_SERVERS_FILE.exists():
        return

    # 示例组合
    sample_combination = Combination(
        id=1,
        name="宠物店基础服务",
        description="包含宠物查询和用户管理的基础接口",
        status="active",
        endpoints=[
            {
                "serviceName": "Petstore API",
                "serviceUrl": "https://petstore3.swagger.io/api/v3/openapi.json",
                "path": "/pet/{petId}",
                "method": "GET",
                "summary": "Find pet by ID"
            },
            {
                "serviceName": "Petstore API",
                "serviceUrl": "https://petstore3.swagger.io/api/v3/openapi.json",
                "path": "/user/{username}",
                "method": "GET",
                "summary": "Get user by user name"
            }
        ],
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )
    combinations_db[1] = sample_combination
    combination_id_counter = 2
    save_combinations()
    print("Initialized sample data")


# ============= Helper Functions =============

async def notify_tools_changed(prefix: str):
    """
    通知工具列表已变更

    Args:
        prefix: MCP Server 前缀
    """
    notification = {
        "jsonrpc": "2.0",
        "method": "notifications/tools/list_changed"
    }

    await session_manager.broadcast_to_prefix(prefix, notification)
    print(f"Notified tools changed for prefix: {prefix}")


@app.get("/api/v1/endpoints")
async def get_api_endpoints(url: str = Query(..., description="URL to the OpenAPI 3.0 specification.")):
    """
    Fetches an OpenAPI 3.0 specification and returns a simplified list of its endpoints.
    """
    try:
        openapi_spec = await fetch_openapi_spec(url)
        endpoints = extract_api_endpoints(openapi_spec)
        return endpoints
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/v1/tools")
async def get_mcp_tools(openapi_url: Optional[str] = Query(
    None,
    description="URL to the OpenAPI 3.0 specification. If not provided, a mock spec will be used."
)):
    """
    Exposes converted MCP Tools from an OpenAPI 3.0 specification.
    """
    try:
        if openapi_url:
            openapi_spec = await fetch_openapi_spec(openapi_url)
        else:
            # Use the mock spec if no URL is provided
            openapi_spec = MOCK_OPENAPI_SPEC
            print("Using mock OpenAPI spec.")

        mcp_tools = convert_openapi_to_mcp(openapi_spec)
        return mcp_tools
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"OpenAPI spec file not found: {e}")
    except Exception as e:
        # Catch other potential errors during fetch or conversion
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process OpenAPI spec: {e}")


# ============= Combination Management API =============

@app.get("/api/v1/combinations", response_model=list[Combination])
async def get_combinations():
    """
    获取所有组合列表
    """
    return list(combinations_db.values())


@app.get("/api/v1/combinations/{combination_id}", response_model=Combination)
async def get_combination(combination_id: int = Path(..., description="组合 ID")):
    """
    根据 ID 获取单个组合
    """
    if combination_id not in combinations_db:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")
    return combinations_db[combination_id]


@app.post("/api/v1/combinations", response_model=Combination, status_code=201)
async def create_combination(combination: CombinationCreate):
    """
    创建新组合
    """
    global combination_id_counter

    new_combination = Combination(
        id=combination_id_counter,
        name=combination.name,
        description=combination.description,
        endpoints=combination.endpoints,
        status="active",
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    combinations_db[combination_id_counter] = new_combination
    combination_id_counter += 1
    save_combinations()  # 保存数据

    return new_combination


@app.put("/api/v1/combinations/{combination_id}", response_model=Combination)
async def update_combination(
        combination_id: int = Path(..., description="组合 ID"),
        combination_update: CombinationUpdate = None
):
    """
    更新组合信息
    """
    if combination_id not in combinations_db:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    existing_combination = combinations_db[combination_id]

    # 更新字段
    if combination_update.name is not None:
        existing_combination.name = combination_update.name
    if combination_update.description is not None:
        existing_combination.description = combination_update.description
    if combination_update.endpoints is not None:
        existing_combination.endpoints = combination_update.endpoints

    existing_combination.updatedAt = datetime.now()
    save_combinations()  # 保存数据

    return existing_combination


@app.patch("/api/v1/combinations/{combination_id}/status", response_model=Combination)
async def toggle_combination_status(
        combination_id: int = Path(..., description="组合 ID"),
        status: str = Query(..., description="新状态：active 或 inactive")
):
    """
    切换组合状态（启用/停用）
    """
    if combination_id not in combinations_db:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    if status not in ["active", "inactive"]:
        raise HTTPException(status_code=400, detail="状态值必须为 'active' 或 'inactive'")

    existing_combination = combinations_db[combination_id]
    existing_combination.status = status
    existing_combination.updatedAt = datetime.now()
    save_combinations()  # 保存数据

    return existing_combination


@app.delete("/api/v1/combinations/{combination_id}", status_code=204)
async def delete_combination(combination_id: int = Path(..., description="组合 ID")):
    """
    删除组合
    """
    if combination_id not in combinations_db:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    del combinations_db[combination_id]
    save_combinations()  # 保存数据
    return None


# ============= MCP Server Management API =============

@app.get("/api/v1/mcp-servers", response_model=list[McpServer])
async def get_mcp_servers():
    """
    获取所有 MCP 服务列表
    """
    return list(mcp_servers_db.values())


@app.get("/api/v1/mcp-servers/{server_id}", response_model=McpServer)
async def get_mcp_server(server_id: int = Path(..., description="MCP 服务 ID")):
    """
    根据 ID 获取单个 MCP 服务
    """
    if server_id not in mcp_servers_db:
        raise HTTPException(status_code=404, detail=f"MCP 服务 ID {server_id} 不存在")
    return mcp_servers_db[server_id]


@app.post("/api/v1/mcp-servers", response_model=McpServer, status_code=201)
async def create_mcp_server(server: McpServerCreate):
    """
    创建新 MCP 服务
    """
    global mcp_server_id_counter

    # 检查 prefix 是否已存在
    for existing_server in mcp_servers_db.values():
        if existing_server.prefix == server.prefix:
            raise HTTPException(status_code=400, detail=f"MCP 前缀 '{server.prefix}' 已存在，请使用其他前缀")

    # 验证所有 combination_ids 是否存在
    for comb_id in server.combination_ids:
        if comb_id not in combinations_db:
            raise HTTPException(status_code=400, detail=f"组合 ID {comb_id} 不存在")

    new_server = McpServer(
        id=mcp_server_id_counter,
        name=server.name,
        prefix=server.prefix,
        description=server.description,
        combination_ids=server.combination_ids,
        status="active",
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    mcp_servers_db[mcp_server_id_counter] = new_server
    mcp_server_id_counter += 1
    save_mcp_servers()  # 保存数据

    return new_server


@app.put("/api/v1/mcp-servers/{server_id}", response_model=McpServer)
async def update_mcp_server(
        server_id: int = Path(..., description="MCP 服务 ID"),
        server_update: McpServerUpdate = None
):
    """
    更新 MCP 服务信息
    """
    if server_id not in mcp_servers_db:
        raise HTTPException(status_code=404, detail=f"MCP 服务 ID {server_id} 不存在")

    existing_server = mcp_servers_db[server_id]

    # 更新字段
    if server_update.name is not None:
        existing_server.name = server_update.name
    if server_update.description is not None:
        existing_server.description = server_update.description
    if server_update.combination_ids is not None:
        # 验证所有 combination_ids 是否存在
        for comb_id in server_update.combination_ids:
            if comb_id not in combinations_db:
                raise HTTPException(status_code=400, detail=f"组合 ID {comb_id} 不存在")
        existing_server.combination_ids = server_update.combination_ids

    existing_server.updatedAt = datetime.now()
    save_mcp_servers()  # 保存数据

    # 通知工具列表已变更
    await notify_tools_changed(existing_server.prefix)

    return existing_server


@app.patch("/api/v1/mcp-servers/{server_id}/status", response_model=McpServer)
async def toggle_mcp_server_status(
        server_id: int = Path(..., description="MCP 服务 ID"),
        status: str = Query(..., description="新状态：active 或 inactive")
):
    """
    切换 MCP 服务状态（启用/停用）
    """
    if server_id not in mcp_servers_db:
        raise HTTPException(status_code=404, detail=f"MCP 服务 ID {server_id} 不存在")

    if status not in ["active", "inactive"]:
        raise HTTPException(status_code=400, detail="状态值必须为 'active' 或 'inactive'")

    existing_server = mcp_servers_db[server_id]
    existing_server.status = status
    existing_server.updatedAt = datetime.now()
    save_mcp_servers()  # 保存数据

    # 通知工具列表已变更（状态变化也会影响可用工具）
    await notify_tools_changed(existing_server.prefix)

    return existing_server


@app.delete("/api/v1/mcp-servers/{server_id}", status_code=204)
async def delete_mcp_server(server_id: int = Path(..., description="MCP 服务 ID")):
    """
    删除 MCP 服务
    """
    if server_id not in mcp_servers_db:
        raise HTTPException(status_code=404, detail=f"MCP 服务 ID {server_id} 不存在")

    del mcp_servers_db[server_id]
    save_mcp_servers()  # 保存数据
    return None


# ============= MCP Protocol Endpoint =============

@app.api_route("/mcp/{prefix}", methods=["GET", "POST"])
async def mcp_endpoint(prefix: str, request: Request):
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
    from fastapi.responses import JSONResponse

    # 查找对应的 MCP Server
    mcp_server = None
    for server in mcp_servers_db.values():
        if server.prefix == prefix:
            mcp_server = server
            break

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

        # 特殊处理 initialize 请求
        if rpc_request.method == "initialize":
            # 创建新会话
            session = await session_manager.create_session(prefix)

            # 创建 MCP Server Handler
            server_dict = mcp_server.model_dump()
            combinations_list = [comb.model_dump() for comb in combinations_db.values()]

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
        server_dict = mcp_server.model_dump()
        combinations_list = [comb.model_dump() for comb in combinations_db.values()]

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


@app.get("/mcp/{prefix}/config")
async def get_mcp_config(prefix: str):
    """
    获取 MCP Server 的配置信息

    返回可以直接复制到 AI 工具配置文件中的标准配置
    """
    # 查找对应的 MCP Server
    mcp_server = None
    for server in mcp_servers_db.values():
        if server.prefix == prefix:
            mcp_server = server
            break

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


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
