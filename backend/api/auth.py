# backend/api/auth.py
"""
认证 API 路由

提供用户登录、获取当前用户信息等认证相关的 API 端点。
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import authenticate_user, create_access_token, get_current_user
from core.database import get_db
from models.db_models import UserDB
from models.user import UserLogin, LoginResponse, User

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"]
)


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录

    验证用户名和密码，返回 JWT 访问令牌。

    Args:
        credentials: 登录凭据（用户名和密码）
        db: 数据库会话

    Returns:
        JWT 访问令牌和用户信息

    Raises:
        HTTPException: 用户名或密码错误时抛出 401 错误
    """
    # 验证用户名和密码
    user = await authenticate_user(db, credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 更新最后登录时间
    user.last_login_at = datetime.now()
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 生成 JWT Token
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }
    )

    # 返回 Token 和用户信息
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=User.from_orm(user)
    )


@router.get("/me", response_model=User)
async def get_me(
    current_user: UserDB = Depends(get_current_user)
):
    """
    获取当前登录用户信息

    Args:
        current_user: 当前用户（从 JWT Token 中解析）

    Returns:
        当前用户的详细信息
    """
    return User.from_orm(current_user)


@router.post("/logout")
async def logout():
    """
    用户登出

    注意：JWT 是无状态的，实际的登出逻辑由前端处理（删除 Token）。
    此端点主要用于前端调用，可以在这里添加额外的登出逻辑（如记录日志）。

    Returns:
        成功消息
    """
    return {"message": "Successfully logged out"}
