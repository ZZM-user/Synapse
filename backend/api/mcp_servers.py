# backend/api/mcp_servers.py
"""
MCP 服务管理 API 路由
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Path, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.mcp_server import McpServer, McpServerCreate, McpServerUpdate
from repositories.combination_repository import CombinationRepository
from repositories.mcp_server_repository import McpServerRepository
from mcp.session import session_manager

router = APIRouter(prefix="/api/v1/mcp-servers", tags=["mcp-servers"])


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


@router.get("", response_model=list[McpServer])
async def get_mcp_servers(db: AsyncSession = Depends(get_db)):
    """
    获取所有 MCP 服务列表
    """
    repo = McpServerRepository(db)
    db_servers = await repo.get_all()
    return [McpServer.from_orm(s) for s in db_servers]


@router.get("/{server_id}", response_model=McpServer)
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


@router.post("", response_model=McpServer, status_code=201)
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


@router.put("/{server_id}", response_model=McpServer)
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


@router.patch("/{server_id}/status", response_model=McpServer)
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
    existing.status = status
    existing.updated_at = datetime.now()
    await db.flush()
    await db.commit()
    await db.refresh(existing)

    # 通知工具列表已变更
    await notify_tools_changed(existing.prefix)

    return McpServer.from_orm(existing)


@router.delete("/{server_id}", status_code=204)
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
