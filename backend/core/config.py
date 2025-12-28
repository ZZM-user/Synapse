"""
配置管理模块
负责加载和验证应用配置，支持 YAML 配置文件和环境变量
"""

import os
import re
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv


class SQLiteConfig(BaseModel):
    """SQLite 数据库配置"""
    path: str = Field(default="./data/synapse.db", description="数据库文件路径")
    echo: bool = Field(default=False, description="是否打印 SQL 语句")
    pool_pre_ping: bool = Field(default=True, description="连接池健康检查")


class MySQLConfig(BaseModel):
    """MySQL 数据库配置"""
    host: str = Field(default="localhost")
    port: int = Field(default=3306)
    database: str = Field(default="synapse")
    username: str = Field(default="synapse_user")
    password: str = Field(default="")
    charset: str = Field(default="utf8mb4")
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    pool_recycle: int = Field(default=3600)
    echo: bool = Field(default=False)


class PostgreSQLConfig(BaseModel):
    """PostgreSQL 数据库配置"""
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="synapse")
    username: str = Field(default="synapse_user")
    password: str = Field(default="")
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    pool_recycle: int = Field(default=3600)
    echo: bool = Field(default=False)


class OracleConfig(BaseModel):
    """Oracle 数据库配置"""
    host: str = Field(default="localhost")
    port: int = Field(default=1521)
    service_name: str = Field(default="ORCL")
    username: str = Field(default="synapse_user")
    password: str = Field(default="")
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    pool_recycle: int = Field(default=3600)
    echo: bool = Field(default=False)


class DM8Config(BaseModel):
    """DM8 (达梦) 数据库配置"""
    host: str = Field(default="localhost")
    port: int = Field(default=5236)
    database: str = Field(default="SYSDBA")
    username: str = Field(default="SYSDBA")
    password: str = Field(default="")
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    pool_recycle: int = Field(default=3600)
    echo: bool = Field(default=False)


class DatabaseConfig(BaseModel):
    """数据库配置"""
    type: Literal["sqlite", "mysql", "postgresql", "oracle", "dm8"] = Field(
        default="sqlite",
        description="数据库类型"
    )
    sqlite: SQLiteConfig = Field(default_factory=SQLiteConfig)
    mysql: MySQLConfig = Field(default_factory=MySQLConfig)
    postgresql: PostgreSQLConfig = Field(default_factory=PostgreSQLConfig)
    oracle: OracleConfig = Field(default_factory=OracleConfig)
    dm8: DM8Config = Field(default_factory=DM8Config)

    def get_config(self):
        """获取当前数据库类型的配置"""
        return getattr(self, self.type)


class MigrationConfig(BaseModel):
    """数据迁移配置"""
    enabled: bool = Field(default=True, description="是否启用自动 JSON → DB 迁移")
    backup_json: bool = Field(default=True, description="迁移后是否备份 JSON 文件")
    backup_dir: str = Field(default="./data/backups", description="备份目录")
    on_conflict: Literal["skip", "overwrite", "fail"] = Field(
        default="skip",
        description="冲突策略：skip（跳过）, overwrite（覆盖）, fail（失败）"
    )


class AppSettings(BaseModel):
    """应用设置"""
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")


class AppConfig(BaseModel):
    """应用配置"""
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    migration: MigrationConfig = Field(default_factory=MigrationConfig)
    app: AppSettings = Field(default_factory=AppSettings)

    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "AppConfig":
        """
        加载配置文件

        Args:
            config_path: 配置文件路径（相对于 backend 目录）

        Returns:
            AppConfig 实例
        """
        # 加载环境变量
        load_dotenv()

        # 获取配置文件绝对路径
        if not Path(config_path).is_absolute():
            # 假设是相对于 backend 目录
            backend_dir = Path(__file__).parent.parent
            config_path = backend_dir / config_path

        config_file = Path(config_path)

        # 如果配置文件不存在，使用默认配置
        if not config_file.exists():
            print(f"⚠️  配置文件 {config_path} 不存在，使用默认配置（SQLite）")
            return cls()

        # 读取 YAML 配置
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # 替换环境变量占位符
        config_data = cls._replace_env_vars(config_data)

        # 创建配置对象
        return cls(**config_data)

    @classmethod
    def _replace_env_vars(cls, data):
        """
        递归替换配置中的环境变量占位符

        支持 ${VAR_NAME} 格式的环境变量引用
        """
        if isinstance(data, dict):
            return {k: cls._replace_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls._replace_env_vars(item) for item in data]
        elif isinstance(data, str):
            # 查找并替换 ${VAR_NAME} 格式的环境变量
            pattern = r'\$\{([^}]+)\}'

            def replacer(match):
                var_name = match.group(1)
                value = os.getenv(var_name)
                if value is None:
                    print(f"⚠️  环境变量 {var_name} 未设置，使用空字符串")
                    return ""
                return value

            return re.sub(pattern, replacer, data)
        else:
            return data


def load_config(config_path: str = "config.yaml") -> AppConfig:
    """
    便捷函数：加载配置

    Args:
        config_path: 配置文件路径

    Returns:
        AppConfig 实例
    """
    return AppConfig.load(config_path)
