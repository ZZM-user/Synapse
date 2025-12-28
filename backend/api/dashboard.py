# backend/api/dashboard.py
"""
Dashboard API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.db_models import CombinationDB, McpServerDB, ServiceDB

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    获取仪表盘统计数据
    """
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
