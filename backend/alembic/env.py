"""
Alembic 环境配置
支持从 config.yaml 动态加载数据库配置
"""

from logging.config import fileConfig
import sys
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# 添加项目路径到 sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# 导入应用配置和模型
from core.config import load_config
from models.db_models import Base

# Alembic Config object
config = context.config

# 解释 Python 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 加载应用配置
app_config = load_config()

# 设置 target_metadata（用于自动生成迁移）
target_metadata = Base.metadata


def get_url():
    """动态获取数据库 URL"""
    from core.database import DatabaseManager

    # 创建临时的 DatabaseManager 实例来构建 URL
    manager = DatabaseManager(app_config)
    db_type = app_config.database.type

    # 根据数据库类型构建 URL（同步版本，用于 Alembic）
    if db_type == "sqlite":
        # SQLite: 移除 +aiosqlite 后缀，使用同步驱动
        url = manager._build_sqlite_url()
        url = url.replace("+aiosqlite", "")
    elif db_type == "mysql":
        # MySQL: 使用同步驱动
        url = manager._build_mysql_url()
        url = url.replace("+aiomysql", "+pymysql")
    elif db_type == "postgresql":
        # PostgreSQL: 使用同步驱动
        url = manager._build_postgresql_url()
        url = url.replace("+asyncpg", "+psycopg2")
    elif db_type == "oracle":
        # Oracle: 使用同步驱动
        url = manager._build_oracle_url()
        # oracledb 驱动本身支持同步和异步
        url = url.replace("+oracledb", "")
    elif db_type == "dm8":
        # DM8: 使用同步驱动
        url = manager._build_dm8_url()
        # dmPython 驱动本身是同步的
    else:
        raise ValueError(f"不支持的数据库类型: {db_type}")

    return url


# 设置数据库 URL
config.set_main_option("sqlalchemy.url", get_url())


def run_migrations_offline() -> None:
    """
    离线模式运行迁移

    生成 SQL 脚本而不实际连接数据库
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在线模式运行迁移

    连接到数据库并执行迁移
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
