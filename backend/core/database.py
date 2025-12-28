"""
数据库管理模块
负责数据库连接、会话管理和依赖注入
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional
from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)

from .config import AppConfig, DatabaseConfig


class DatabaseManager:
    """
    数据库管理器（单例模式）
    负责创建和管理数据库引擎和会话
    """

    def __init__(self, config: AppConfig):
        """
        初始化数据库管理器

        Args:
            config: 应用配置对象
        """
        self.config = config
        self.engine: Optional[AsyncEngine] = None
        self.session_maker: Optional[async_sessionmaker[AsyncSession]] = None

    def create_engine(self):
        """
        根据配置创建数据库引擎（工厂模式）
        支持 SQLite, MySQL, PostgreSQL, Oracle, DM8
        """
        db_config = self.config.database
        db_type = db_config.type

        # 根据数据库类型构建 URL
        if db_type == "sqlite":
            url = self._build_sqlite_url()
        elif db_type == "mysql":
            url = self._build_mysql_url()
        elif db_type == "postgresql":
            url = self._build_postgresql_url()
        elif db_type == "oracle":
            url = self._build_oracle_url()
        elif db_type == "dm8":
            url = self._build_dm8_url()
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")

        # 获取数据库特定配置
        specific_config = db_config.get_config()

        # 创建异步引擎
        engine_kwargs = {
            "echo": specific_config.echo,
            "pool_pre_ping": True,  # 连接健康检查
        }

        # 非 SQLite 数据库添加连接池配置
        if db_type != "sqlite":
            engine_kwargs.update({
                "pool_size": specific_config.pool_size,
                "max_overflow": specific_config.max_overflow,
                "pool_recycle": specific_config.pool_recycle,
            })

        self.engine = create_async_engine(url, **engine_kwargs)

        # 创建会话工厂
        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,  # 提交后对象不过期
        )

        print(f"✅ 数据库引擎已创建: {db_type}")

    def _build_sqlite_url(self) -> str:
        """构建 SQLite 数据库 URL"""
        cfg = self.config.database.sqlite

        # 处理路径
        db_path = Path(cfg.path)
        if not db_path.is_absolute():
            # 相对路径，转为绝对路径（相对于 backend 目录）
            backend_dir = Path(__file__).parent.parent
            db_path = backend_dir / cfg.path

        # 确保目录存在
        db_path.parent.mkdir(parents=True, exist_ok=True)

        return f"sqlite+aiosqlite:///{db_path}"

    def _build_mysql_url(self) -> str:
        """构建 MySQL 数据库 URL"""
        cfg = self.config.database.mysql

        # URL 编码密码（处理特殊字符）
        password = quote_plus(cfg.password)

        return (
            f"mysql+aiomysql://{cfg.username}:{password}"
            f"@{cfg.host}:{cfg.port}/{cfg.database}"
            f"?charset={cfg.charset}"
        )

    def _build_postgresql_url(self) -> str:
        """构建 PostgreSQL 数据库 URL"""
        cfg = self.config.database.postgresql

        # URL 编码密码
        password = quote_plus(cfg.password)

        return (
            f"postgresql+asyncpg://{cfg.username}:{password}"
            f"@{cfg.host}:{cfg.port}/{cfg.database}"
        )

    def _build_oracle_url(self) -> str:
        """构建 Oracle 数据库 URL"""
        cfg = self.config.database.oracle

        # URL 编码密码
        password = quote_plus(cfg.password)

        return (
            f"oracle+oracledb://{cfg.username}:{password}"
            f"@{cfg.host}:{cfg.port}/?service_name={cfg.service_name}"
        )

    def _build_dm8_url(self) -> str:
        """构建 DM8 (达梦) 数据库 URL"""
        cfg = self.config.database.dm8

        # URL 编码密码
        password = quote_plus(cfg.password)

        # 注意：DM8 的驱动可能需要根据实际情况调整
        return (
            f"dm+dmPython://{cfg.username}:{password}"
            f"@{cfg.host}:{cfg.port}/{cfg.database}"
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话（带自动提交/回滚）

        Yields:
            AsyncSession: 数据库会话对象
        """
        if self.session_maker is None:
            raise RuntimeError("数据库引擎未初始化，请先调用 create_engine()")

        async with self.session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            print("✅ 数据库连接已关闭")


# 全局数据库管理器实例
db_manager: Optional[DatabaseManager] = None


def init_database(config: AppConfig) -> DatabaseManager:
    """
    初始化数据库管理器

    Args:
        config: 应用配置对象

    Returns:
        DatabaseManager: 数据库管理器实例
    """
    global db_manager
    db_manager = DatabaseManager(config)
    db_manager.create_engine()
    return db_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 依赖注入函数：获取数据库会话

    使用示例:
        @app.get("/api/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()

    Yields:
        AsyncSession: 数据库会话对象
    """
    if db_manager is None:
        raise RuntimeError("数据库管理器未初始化，请在应用启动时调用 init_database()")

    async with db_manager.get_session() as session:
        yield session
