# backend/models/mcp_server.py
from datetime import datetime
from typing import List, Literal
from pydantic import BaseModel, Field, field_validator


class McpServerBase(BaseModel):
    """MCP 服务基础模型"""
    name: str = Field(..., min_length=1, description="MCP 服务名称")
    prefix: str = Field(..., min_length=1, max_length=50, description="MCP 前缀（唯一标识）")
    description: str = Field(default="", description="MCP 服务描述")
    combination_ids: List[int] = Field(default_factory=list, description="包含的组合 ID 列表")

    @field_validator('prefix')
    @classmethod
    def validate_prefix(cls, v: str) -> str:
        """验证前缀格式：只允许字母、数字、下划线、连字符"""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('MCP 前缀只能包含字母、数字、下划线和连字符')
        return v.lower()  # 统一转换为小写


class McpServerCreate(McpServerBase):
    """创建 MCP 服务的请求模型"""
    pass


class McpServerUpdate(BaseModel):
    """更新 MCP 服务的请求模型"""
    name: str | None = Field(None, min_length=1, description="MCP 服务名称")
    description: str | None = Field(None, description="MCP 服务描述")
    combination_ids: List[int] | None = Field(None, description="包含的组合 ID 列表")


class McpServer(McpServerBase):
    """MCP 服务完整模型（包含元数据）"""
    id: int = Field(..., description="MCP 服务 ID")
    status: Literal["active", "inactive"] = Field(default="active", description="服务状态")
    createdAt: datetime = Field(default_factory=datetime.now, description="创建时间")
    updatedAt: datetime = Field(default_factory=datetime.now, description="更新时间")

    model_config = {
        "from_attributes": True,  # Pydantic v2: 支持从 ORM 模型转换
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "用户管理服务",
                "prefix": "user-service",
                "description": "包含用户相关的所有 API 组合",
                "status": "active",
                "combination_ids": [1, 2, 3],
                "createdAt": "2025-01-01T00:00:00",
                "updatedAt": "2025-01-01T00:00:00"
            }
        }
    }

    @classmethod
    def from_orm(cls, db_obj):
        """
        从数据库对象转换为 Pydantic 模型

        Args:
            db_obj: McpServerDB 数据库对象

        Returns:
            McpServer: Pydantic 模型实例
        """
        from models.db_models import McpServerDB

        if not isinstance(db_obj, McpServerDB):
            raise TypeError(f"期望 McpServerDB 类型，得到 {type(db_obj)}")

        return cls(
            id=db_obj.id,
            name=db_obj.name,
            prefix=db_obj.prefix,
            description=db_obj.description,
            combination_ids=db_obj.combination_ids,
            status=db_obj.status,
            createdAt=db_obj.created_at,
            updatedAt=db_obj.updated_at,
        )
