# backend/api/users.py
"""
用户管理 API 路由

提供用户的 CRUD 操作，仅管理员可以访问。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_admin_user, hash_password
from core.database import get_db
from models.db_models import UserDB
from models.user import User, UserCreate, UserUpdate, UserListResponse

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
    dependencies=[Depends(get_current_admin_user)]  # 所有端点都需要管理员权限
)


@router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户列表（仅管理员）

    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话

    Returns:
        用户列表和总数
    """
    # 查询总数
    total_result = await db.execute(select(func.count()).select_from(UserDB))
    total = total_result.scalar()

    # 查询用户列表
    result = await db.execute(
        select(UserDB)
        .order_by(UserDB.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()

    return UserListResponse(
        users=[User.from_orm(user) for user in users],
        total=total
    )


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定用户信息（仅管理员）

    Args:
        user_id: 用户 ID
        db: 数据库会话

    Returns:
        用户信息

    Raises:
        HTTPException: 用户不存在时抛出 404 错误
    """
    user = await db.get(UserDB, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return User.from_orm(user)


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新用户（仅管理员）

    Args:
        user_data: 用户创建数据
        db: 数据库会话

    Returns:
        创建的用户信息

    Raises:
        HTTPException: 用户名已存在时抛出 400 错误
    """
    # 检查用户名是否已存在
    result = await db.execute(
        select(UserDB).where(UserDB.username == user_data.username)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # 创建新用户
    new_user = UserDB(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role=user_data.role
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return User.from_orm(new_user)


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户信息（仅管理员）

    Args:
        user_id: 用户 ID
        user_data: 更新数据
        db: 数据库会话

    Returns:
        更新后的用户信息

    Raises:
        HTTPException: 用户不存在时抛出 404 错误
    """
    user = await db.get(UserDB, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 更新字段
    if user_data.password is not None:
        user.password_hash = hash_password(user_data.password)

    if user_data.role is not None:
        user.role = user_data.role

    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    await db.commit()
    await db.refresh(user)

    return User.from_orm(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_admin: UserDB = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除用户（仅管理员）

    Args:
        user_id: 用户 ID
        current_admin: 当前管理员用户
        db: 数据库会话

    Raises:
        HTTPException:
            - 用户不存在时抛出 404 错误
            - 尝试删除自己时抛出 400 错误
    """
    # 不允许删除自己
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    user = await db.get(UserDB, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await db.delete(user)
    await db.commit()
