"""add_users_table

Revision ID: c7a50d642d7d
Revises: 002_add_services
Create Date: 2025-12-29 00:51:59.849628

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7a50d642d7d'
down_revision: Union[str, Sequence[str], None] = '002_add_services'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 创建 users 表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False, comment='用户名（唯一）'),
        sa.Column('password_hash', sa.String(length=255), nullable=False, comment='密码哈希'),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='user', comment='角色：admin/user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='是否激活'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True, comment='最后登录时间'),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'], unique=False)
    op.create_index('idx_user_role_active', 'users', ['role', 'is_active'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 删除索引
    op.drop_index('idx_user_role_active', table_name='users')
    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_id', table_name='users')

    # 删除表
    op.drop_table('users')
