"""
SQLAlchemy 数据库表模型
定义了 Combination 和 McpServer 的数据库结构
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.orm import declarative_base

# 创建基类
Base = declarative_base()


class CombinationDB(Base):
    """组合数据库模型"""
    __tablename__ = "combinations"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 基本信息
    name = Column(String(255), nullable=False, index=True, comment="组合名称")
    description = Column(Text, default="", comment="组合描述")
    status = Column(String(20), default="active", index=True, comment="状态：active/inactive")

    # JSON 字段：存储 endpoints 列表
    # 结构：[{"serviceName": str, "serviceUrl": str, "path": str, "method": str, "summary": str}]
    endpoints = Column(JSON, nullable=False, default=list, comment="API 端点列表")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")

    # 复合索引
    __table_args__ = (
        Index('idx_combination_status_created', 'status', 'created_at'),
    )

    def __repr__(self):
        return f"<CombinationDB(id={self.id}, name='{self.name}', status='{self.status}')>"


class McpServerDB(Base):
    """MCP 服务数据库模型"""
    __tablename__ = "mcp_servers"

    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 基本信息
    name = Column(String(255), nullable=False, index=True, comment="MCP 服务名称")
    prefix = Column(String(50), unique=True, nullable=False, index=True, comment="MCP 前缀（唯一标识）")
    description = Column(Text, default="", comment="MCP 服务描述")
    status = Column(String(20), default="active", index=True, comment="状态：active/inactive")

    # JSON 字段：存储 combination_ids
    # 结构：[1, 2, 3, ...]
    combination_ids = Column(JSON, nullable=False, default=list, comment="包含的组合 ID 列表")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")

    # 复合索引
    __table_args__ = (
        Index('idx_mcp_server_prefix_status', 'prefix', 'status'),
    )

    def __repr__(self):
        return f"<McpServerDB(id={self.id}, name='{self.name}', prefix='{self.prefix}', status='{self.status}')>"
