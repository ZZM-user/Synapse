# backend/main.py
import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path as PathLib
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Path, Request, Depends
from sse_starlette.sse import EventSourceResponse
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

# 核心模块
from core.config import load_config
from core.database import init_database, get_db, db_manager
from core.migration import auto_migrate_if_needed
from models.db_models import Base

# MCP 相关
from mcp.openapi_to_mcp import convert_openapi_to_mcp
from mcp.protocol import JsonRpcRequest, McpError, create_error_response
from mcp.server import McpServerHandler
from mcp.session import session_manager

# 模型
from models.combination import Combination, CombinationCreate, CombinationUpdate
from models.mcp_server import McpServer, McpServerCreate, McpServerUpdate
from models.service import Service, ServiceCreate, ServiceUpdate

# Repository 层
from repositories.combination_repository import CombinationRepository
from repositories.mcp_server_repository import McpServerRepository
from repositories.service_repository import ServiceRepository

# 服务层
from services.openapi_fetcher import fetch_openapi_spec, extract_api_endpoints


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 启动和关闭时的操作"""
    print("=" * 60)
    print("🚀 Synapse MCP Gateway 启动中...")
    print("=" * 60)

    # 1. 加载配置
    print("📋 加载配置文件...")
    app_config = load_config()
    print(f"   数据库类型: {app_config.database.type}")

    # 2. 初始化数据库
    print("🗄️  初始化数据库连接...")
    manager = init_database(app_config)  # 保存返回的 manager 实例

    # 3. 创建表结构（如果不存在）
    print("📊 创建数据库表结构...")
    async with manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 4. 执行数据迁移（JSON → 数据库）
    print("🔄 检查数据迁移...")
    async with manager.session_maker() as session:
        migrated = await auto_migrate_if_needed(
            session=session,
            config=app_config.migration,
            data_dir=DATA_DIR
        )
        if migrated:
            print("   数据迁移完成！")

    print("=" * 60)
    print("✅ Synapse MCP Gateway 已启动")
    print("   访问 API 文档: http://localhost:8000/docs")
    print("=" * 60)

    yield

    # 关闭数据库连接
    print("\n🛑 关闭数据库连接...")
    await manager.close()
    print("✅ Synapse MCP Gateway 已停止")


app = FastAPI(
    title="Synapse MCP Gateway",
    description="Converts OpenAPI specifications to AI Agent callable tools (MCP format).",
    version="0.4.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据目录
DATA_DIR = PathLib(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

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


# ============= Service Management API =============

@app.get("/api/v1/services", response_model=list[Service])
async def get_services(db: AsyncSession = Depends(get_db)):
    """
    获取所有服务列表
    """
    repo = ServiceRepository(db)
    db_services = await repo.get_all()
    return [Service.from_orm(s) for s in db_services]


@app.get("/api/v1/services/{service_id}", response_model=Service)
async def get_service(
    service_id: int = Path(..., description="服务 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    根据 ID 获取单个服务
    """
    repo = ServiceRepository(db)
    db_service = await repo.get_by_id(service_id)

    if not db_service:
        raise HTTPException(status_code=404, detail=f"服务 ID {service_id} 不存在")

    return Service.from_orm(db_service)


@app.post("/api/v1/services", response_model=Service, status_code=201)
async def create_service(
    service: ServiceCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新服务
    """
    repo = ServiceRepository(db)

    # 创建服务
    db_service = await repo.create(
        name=service.name,
        url=service.url,
        type=service.type
    )

    await db.commit()
    return Service.from_orm(db_service)


@app.put("/api/v1/services/{service_id}", response_model=Service)
async def update_service(
    service_id: int = Path(..., description="服务 ID"),
    service_update: ServiceUpdate = None,
    db: AsyncSession = Depends(get_db)
):
    """
    更新服务信息
    """
    repo = ServiceRepository(db)

    # 检查服务是否存在
    existing = await repo.get_by_id(service_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"服务 ID {service_id} 不存在")

    # 更新服务
    db_service = await repo.update(
        service_id=service_id,
        name=service_update.name,
        url=service_update.url,
        type=service_update.type
    )

    await db.commit()

    if not db_service:
        raise HTTPException(status_code=404, detail=f"服务 ID {service_id} 不存在")

    return Service.from_orm(db_service)


@app.delete("/api/v1/services/{service_id}", status_code=204)
async def delete_service(
    service_id: int = Path(..., description="服务 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    删除服务
    """
    repo = ServiceRepository(db)

    success = await repo.delete(service_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"服务 ID {service_id} 不存在")

    await db.commit()
    return None


# ============= Combination Management API =============

@app.get("/api/v1/combinations", response_model=list[Combination])
async def get_combinations(db: AsyncSession = Depends(get_db)):
    """
    获取所有组合列表
    """
    repo = CombinationRepository(db)
    db_combinations = await repo.get_all()
    return [Combination.from_orm(c) for c in db_combinations]


@app.get("/api/v1/combinations/{combination_id}", response_model=Combination)
async def get_combination(
    combination_id: int = Path(..., description="组合 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    根据 ID 获取单个组合
    """
    repo = CombinationRepository(db)
    db_combination = await repo.get_by_id(combination_id)

    if not db_combination:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    return Combination.from_orm(db_combination)


@app.post("/api/v1/combinations", response_model=Combination, status_code=201)
async def create_combination(
    combination: CombinationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新组合
    """
    repo = CombinationRepository(db)

    # 创建组合
    db_combination = await repo.create(
        name=combination.name,
        description=combination.description,
        endpoints=[ep.model_dump() for ep in combination.endpoints]
    )

    await db.commit()
    return Combination.from_orm(db_combination)


@app.put("/api/v1/combinations/{combination_id}", response_model=Combination)
async def update_combination(
    combination_id: int = Path(..., description="组合 ID"),
    combination_update: CombinationUpdate = None,
    db: AsyncSession = Depends(get_db)
):
    """
    更新组合信息
    """
    repo = CombinationRepository(db)

    # 检查组合是否存在
    existing = await repo.get_by_id(combination_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    # 更新组合
    db_combination = await repo.update(
        combination_id=combination_id,
        name=combination_update.name,
        description=combination_update.description,
        endpoints=[ep.model_dump() for ep in combination_update.endpoints] if combination_update.endpoints else None
    )

    await db.commit()

    if not db_combination:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    return Combination.from_orm(db_combination)


@app.patch("/api/v1/combinations/{combination_id}/status", response_model=Combination)
async def toggle_combination_status(
    combination_id: int = Path(..., description="组合 ID"),
    status: str = Query(..., description="新状态：active 或 inactive"),
    db: AsyncSession = Depends(get_db)
):
    """
    切换组合状态（启用/停用）
    """
    if status not in ["active", "inactive"]:
        raise HTTPException(status_code=400, detail="状态值必须为 'active' 或 'inactive'")

    repo = CombinationRepository(db)

    # 检查组合是否存在
    existing = await repo.get_by_id(combination_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    # 手动更新状态（因为 toggle_status 会切换，而我们这里需要设置特定值）
    from datetime import datetime
    db_combination = await repo.update(
        combination_id=combination_id,
        name=None,
        description=None,
        endpoints=None
    )

    # 直接设置状态
    existing.status = status
    existing.updated_at = datetime.now()
    await db.flush()
    await db.commit()
    await db.refresh(existing)

    return Combination.from_orm(existing)


@app.delete("/api/v1/combinations/{combination_id}", status_code=204)
async def delete_combination(
    combination_id: int = Path(..., description="组合 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    删除组合
    """
    repo = CombinationRepository(db)

    success = await repo.delete(combination_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    await db.commit()
    return None


# ============= MCP Server Management API =============

@app.get("/api/v1/mcp-servers", response_model=list[McpServer])
async def get_mcp_servers(db: AsyncSession = Depends(get_db)):
    """
    获取所有 MCP 服务列表
    """
    repo = McpServerRepository(db)
    db_servers = await repo.get_all()
    return [McpServer.from_orm(s) for s in db_servers]


@app.get("/api/v1/mcp-servers/{server_id}", response_model=McpServer)
async def get_mcp_server(
    server_id: int = Path(..., description="MCP 服务 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    根据 ID 获取单个 MCP 服务
    """
    repo = McpServerRepository(db)
    db_server = await repo.get_by_id(server_id)

    if not db_server:
        raise HTTPException(status_code=404, detail=f"MCP 服务 ID {server_id} 不存在")

    return McpServer.from_orm(db_server)


@app.post("/api/v1/mcp-servers", response_model=McpServer, status_code=201)
async def create_mcp_server(
    server: McpServerCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新 MCP 服务
    """
    server_repo = McpServerRepository(db)
    comb_repo = CombinationRepository(db)

    # 检查 prefix 是否已存在
    if await server_repo.check_prefix_exists(server.prefix):
        raise HTTPException(status_code=400, detail=f"MCP 前缀 '{server.prefix}' 已存在，请使用其他前缀")

    # 验证所有 combination_ids 是否存在
    for comb_id in server.combination_ids:
        if not await comb_repo.get_by_id(comb_id):
            raise HTTPException(status_code=400, detail=f"组合 ID {comb_id} 不存在")

    # 创建 MCP 服务
    db_server = await server_repo.create(
        name=server.name,
        prefix=server.prefix,
        description=server.description,
        combination_ids=server.combination_ids
    )

    await db.commit()
    return McpServer.from_orm(db_server)


@app.put("/api/v1/mcp-servers/{server_id}", response_model=McpServer)
async def update_mcp_server(
    server_id: int = Path(..., description="MCP 服务 ID"),
    server_update: McpServerUpdate = None,
    db: AsyncSession = Depends(get_db)
):
    """
    更新 MCP 服务信息
    """
    server_repo = McpServerRepository(db)
    comb_repo = CombinationRepository(db)

    # 检查服务是否存在
    existing = await server_repo.get_by_id(server_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"MCP 服务 ID {server_id} 不存在")

    # 如果更新了 combination_ids，验证它们是否存在
    if server_update.combination_ids is not None:
        for comb_id in server_update.combination_ids:
            if not await comb_repo.get_by_id(comb_id):
                raise HTTPException(status_code=400, detail=f"组合 ID {comb_id} 不存在")

    # 更新服务
    db_server = await server_repo.update(
        server_id=server_id,
        name=server_update.name,
        prefix=None,  # 不允许更新 prefix
        description=server_update.description,
        combination_ids=server_update.combination_ids
    )

    await db.commit()

    if not db_server:
        raise HTTPException(status_code=404, detail=f"MCP 服务 ID {server_id} 不存在")

    # 通知工具列表已变更
    await notify_tools_changed(db_server.prefix)

    return McpServer.from_orm(db_server)


@app.patch("/api/v1/mcp-servers/{server_id}/status", response_model=McpServer)
async def toggle_mcp_server_status(
    server_id: int = Path(..., description="MCP 服务 ID"),
    status: str = Query(..., description="新状态：active 或 inactive"),
    db: AsyncSession = Depends(get_db)
):
    """
    切换 MCP 服务状态（启用/停用）
    """
    if status not in ["active", "inactive"]:
        raise HTTPException(status_code=400, detail="状态值必须为 'active' 或 'inactive'")

    repo = McpServerRepository(db)

    # 检查服务是否存在
    existing = await repo.get_by_id(server_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"MCP 服务 ID {server_id} 不存在")

    # 直接设置状态
    from datetime import datetime
    existing.status = status
    existing.updated_at = datetime.now()
    await db.flush()
    await db.commit()
    await db.refresh(existing)

    # 通知工具列表已变更
    await notify_tools_changed(existing.prefix)

    return McpServer.from_orm(existing)


@app.delete("/api/v1/mcp-servers/{server_id}", status_code=204)
async def delete_mcp_server(
    server_id: int = Path(..., description="MCP 服务 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    删除 MCP 服务
    """
    repo = McpServerRepository(db)

    success = await repo.delete(server_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"MCP 服务 ID {server_id} 不存在")

    await db.commit()
    return None


# ============= Dashboard Statistics API =============

@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    获取仪表盘统计数据
    """
    from sqlalchemy import select, func
    from models.db_models import CombinationDB, McpServerDB, ServiceDB

    # 服务统计
    services_total = await db.scalar(select(func.count()).select_from(ServiceDB))

    # 组合统计
    combinations_total = await db.scalar(select(func.count()).select_from(CombinationDB))
    combinations_active = await db.scalar(
        select(func.count()).select_from(CombinationDB).where(CombinationDB.status == "active")
    )

    # MCP 服务统计
    mcp_servers_total = await db.scalar(select(func.count()).select_from(McpServerDB))
    mcp_servers_active = await db.scalar(
        select(func.count()).select_from(McpServerDB).where(McpServerDB.status == "active")
    )

    # 获取最近创建的项目
    recent_combinations = await db.execute(
        select(CombinationDB)
        .order_by(CombinationDB.created_at.desc())
        .limit(5)
    )
    recent_combinations_list = [
        {
            "id": c.id,
            "name": c.name,
            "type": "combination",
            "status": c.status,
            "created_at": c.created_at.isoformat()
        }
        for c in recent_combinations.scalars()
    ]

    recent_servers = await db.execute(
        select(McpServerDB)
        .order_by(McpServerDB.created_at.desc())
        .limit(5)
    )
    recent_servers_list = [
        {
            "id": s.id,
            "name": s.name,
            "type": "mcp_server",
            "status": s.status,
            "created_at": s.created_at.isoformat()
        }
        for s in recent_servers.scalars()
    ]

    # 合并并按时间排序
    recent_items = sorted(
        recent_combinations_list + recent_servers_list,
        key=lambda x: x["created_at"],
        reverse=True
    )[:5]

    # 计算接口总数（从所有组合中）
    all_combinations = await db.execute(select(CombinationDB))
    total_endpoints = sum(len(c.endpoints) for c in all_combinations.scalars())

    return {
        "services": {
            "total": services_total or 0
        },
        "combinations": {
            "total": combinations_total or 0,
            "active": combinations_active or 0,
            "inactive": (combinations_total or 0) - (combinations_active or 0)
        },
        "mcp_servers": {
            "total": mcp_servers_total or 0,
            "active": mcp_servers_active or 0,
            "inactive": (mcp_servers_total or 0) - (mcp_servers_active or 0)
        },
        "endpoints": {
            "total": total_endpoints
        },
        "recent_items": recent_items
    }


# ============= MCP Protocol Endpoint =============

@app.api_route("/mcp/{prefix}", methods=["GET", "POST"])
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
    from fastapi.responses import JSONResponse

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


@app.get("/mcp/{prefix}/config")
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


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
