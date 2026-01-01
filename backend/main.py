# backend/main.py
"""
Synapse MCP Gateway - 主应用入口

这是一个轻量级、高性能的协议转换网关，将 OpenAPI 服务转换为 MCP 格式。
"""
from contextlib import asynccontextmanager
from pathlib import Path as PathLib

import uvicorn
import asyncio
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

# 核心模块
from core.config import load_config
from core.database import init_database
from core.migration import auto_migrate_if_needed
from core.init_admin import ensure_default_admin
from models.db_models import Base
from mcp.session import session_manager

# API 路由
from api import services, combinations, mcp_servers, dashboard, tools, mcp_protocol, auth, users

# 数据目录
DATA_DIR = PathLib(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


async def run_session_cleanup():
    """Background task to clean up stale sessions"""
    while True:
        try:
            # Check every 10 minutes
            await asyncio.sleep(600)
            await session_manager.cleanup_stale_sessions()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"Error in session cleanup task: {e}")
            await asyncio.sleep(60)


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

    # 5. 确保默认管理员账户存在
    print("👤 检查默认管理员账户...")
    async with manager.session_maker() as session:
        await ensure_default_admin(session)
    
    # 6. 启动会话清理任务
    print("🧹 启动会话清理任务...")
    cleanup_task = asyncio.create_task(run_session_cleanup())

    print("=" * 60)
    print("✅ Synapse MCP Gateway 已启动")
    print("   访问 API 文档: http://localhost:8000/docs")
    print("=" * 60)

    yield

    # 停止后台任务
    print("\n🛑 停止后台任务...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    # 关闭数据库连接
    print("🛑 关闭数据库连接...")
    await manager.close()
    print("✅ Synapse MCP Gateway 已停止")


app = FastAPI(
    title="Synapse MCP Gateway",
    description="Converts OpenAPI specifications to AI Agent callable tools (MCP format).",
    version="0.6.2",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= 注册路由 =============
# 认证和用户管理
app.include_router(auth.router)
app.include_router(users.router)

# 业务功能
app.include_router(services.router)
app.include_router(combinations.router)
app.include_router(mcp_servers.router)
app.include_router(dashboard.router)
app.include_router(tools.router)

# MCP 协议（不受认证保护）
app.include_router(mcp_protocol.router)


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
