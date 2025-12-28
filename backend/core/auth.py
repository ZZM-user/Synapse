# backend/core/auth.py
"""
JWT 认证模块

提供完整的用户认证和授权机制：
- 密码哈希和验证（使用 bcrypt）
- JWT Token 生成和验证
- 用户身份认证依赖函数
- 管理员权限检查
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.db_models import UserDB

# ============================================
# 配置
# ============================================

# JWT 密钥（从环境变量读取，如果没有则使用默认值）
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer Token 安全方案
security = HTTPBearer(auto_error=True)


# ============================================
# 密码哈希工具函数
# ============================================

def hash_password(password: str) -> str:
    """
    对密码进行哈希

    Args:
        password: 明文密码

    Returns:
        密码哈希值
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配

    Args:
        plain_password: 明文密码
        hashed_password: 哈希值

    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================
# JWT Token 相关
# ============================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌

    Args:
        data: 要编码到 token 中的数据（通常包含 user_id, username, role）
        expires_delta: 过期时间，默认 24 小时

    Returns:
        JWT token 字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    解码 JWT 访问令牌

    Args:
        token: JWT token 字符串

    Returns:
        解码后的数据字典

    Raises:
        JWTError: Token 无效或过期
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================
# 依赖函数
# ============================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> UserDB:
    """
    获取当前登录用户

    从 JWT Token 中解析用户信息，并从数据库加载完整用户对象。

    Args:
        credentials: HTTP Bearer 认证凭据
        db: 数据库会话

    Returns:
        当前用户的数据库对象

    Raises:
        HTTPException: Token 无效或用户不存在时抛出 401 错误
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    user_id: int = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 从数据库加载用户
    user = await db.get(UserDB, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户是否被禁用
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return user


async def get_current_admin_user(
    current_user: UserDB = Depends(get_current_user)
) -> UserDB:
    """
    获取当前管理员用户

    检查当前用户是否具有管理员权限。

    Args:
        current_user: 当前用户

    Returns:
        当前管理员用户

    Raises:
        HTTPException: 用户不是管理员时抛出 403 错误
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required."
        )
    return current_user


# ============================================
# 用户认证
# ============================================

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[UserDB]:
    """
    验证用户名和密码

    Args:
        db: 数据库会话
        username: 用户名
        password: 密码

    Returns:
        用户对象（如果认证成功），否则返回 None
    """
    from sqlalchemy import select

    # 查找用户
    result = await db.execute(
        select(UserDB).where(UserDB.username == username)
    )
    user = result.scalar_one_or_none()

    if not user:
        return None

    # 验证密码
    if not verify_password(password, user.password_hash):
        return None

    # 检查用户是否被禁用
    if not user.is_active:
        return None

    return user
