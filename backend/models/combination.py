# backend/models/combination.py
from datetime import datetime
from typing import List, Literal
from pydantic import BaseModel, Field


class CombinationEndpoint(BaseModel):
    """组合中的接口定义"""
    serviceName: str = Field(..., description="服务名称")
    serviceUrl: str = Field(..., description="服务的 OpenAPI URL")
    path: str = Field(..., description="API 路径")
    method: str = Field(..., description="HTTP 方法")
    summary: str = Field(default="", description="接口描述")


class CombinationBase(BaseModel):
    """组合基础模型"""
    name: str = Field(..., min_length=1, description="组合名称")
    description: str = Field(default="", description="组合描述")
    endpoints: List[CombinationEndpoint] = Field(default_factory=list, description="包含的接口列表")


class CombinationCreate(CombinationBase):
    """创建组合的请求模型"""
    pass


class CombinationUpdate(BaseModel):
    """更新组合的请求模型"""
    name: str | None = Field(None, min_length=1, description="组合名称")
    description: str | None = Field(None, description="组合描述")
    endpoints: List[CombinationEndpoint] | None = Field(None, description="包含的接口列表")


class Combination(CombinationBase):
    """组合完整模型（包含元数据）"""
    id: int = Field(..., description="组合 ID")
    status: Literal["active", "inactive"] = Field(default="active", description="组合状态")
    createdAt: datetime = Field(default_factory=datetime.now, description="创建时间")
    updatedAt: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "宠物店基础服务",
                "description": "包含宠物查询和用户管理的基础接口",
                "status": "active",
                "endpoints": [
                    {
                        "serviceName": "Petstore API",
                        "serviceUrl": "https://petstore3.swagger.io/api/v3/openapi.json",
                        "path": "/pet/{petId}",
                        "method": "GET",
                        "summary": "Find pet by ID"
                    }
                ],
                "createdAt": "2025-01-01T00:00:00",
                "updatedAt": "2025-01-01T00:00:00"
            }
        }
