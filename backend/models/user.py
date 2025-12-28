"""
用户相关的 Pydantic 模型
"""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


# ============================================
# 基础模型
# ============================================

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    role: Literal["admin", "user"] = Field(default="user", description="用户角色")
    is_active: bool = Field(default=True, description="是否激活")


# ============================================
# 请求模型（用于创建和更新）
# ============================================

class UserCreate(BaseModel):
    """创建用户请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    role: Literal["admin", "user"] = Field(default="user", description="用户角色")


class UserUpdate(BaseModel):
    """更新用户请求模型"""
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="新密码（可选）")
    role: Optional[Literal["admin", "user"]] = Field(None, description="用户角色（可选）")
    is_active: Optional[bool] = Field(None, description="是否激活（可选）")


class UserLogin(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


# ============================================
# 响应模型
# ============================================

class User(UserBase):
    """用户响应模型（不包含密码）"""
    id: int
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, db_obj):
        """从数据库对象转换"""
        return cls(
            id=db_obj.id,
            username=db_obj.username,
            role=db_obj.role,
            is_active=db_obj.is_active,
            created_at=db_obj.created_at,
            updated_at=db_obj.updated_at,
            last_login_at=db_obj.last_login_at,
        )


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str = Field(..., description="JWT 访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user: User = Field(..., description="用户信息")


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: list[User]
    total: int
