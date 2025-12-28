# backend/core/init_admin.py
"""
默认管理员初始化

在应用首次启动时，如果数据库中没有任何用户，
则创建一个默认管理员账户。
"""

import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import hash_password
from models.db_models import UserDB


async def ensure_default_admin(db: AsyncSession):
    """
    确保至少存在一个管理员账户

    如果数据库中没有任何用户，则创建默认管理员。

    Args:
        db: 数据库会话
    """
    # 检查是否已存在用户
    result = await db.execute(select(UserDB))
    existing_users = result.scalars().all()

    if existing_users:
        print(f"ℹ️  数据库中已存在 {len(existing_users)} 个用户，跳过默认管理员创建")
        return

    # 从环境变量读取默认管理员信息
    admin_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

    # 创建默认管理员
    admin_user = UserDB(
        username=admin_username,
        password_hash=hash_password(admin_password),
        role="admin",
        is_active=True
    )

    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)

    print("=" * 60)
    print("🎉 默认管理员账户已创建")
    print("=" * 60)
    print(f"用户名: {admin_username}")
    print(f"密码:   {admin_password}")
    print("=" * 60)
    print("⚠️  警告: 请立即登录并修改默认密码！")
    print("=" * 60)
