"""Initial database schema

Revision ID: 001_initial
Revises:
Create Date: 2025-12-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级：创建表"""
    # 创建 combinations 表
    op.create_table(
        'combinations',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(length=255), nullable=False, comment='组合名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='组合描述'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='状态：active/inactive'),
        sa.Column('endpoints', sa.JSON(), nullable=False, comment='API 端点列表'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('ix_combinations_id', 'combinations', ['id'])
    op.create_index('ix_combinations_name', 'combinations', ['name'])
    op.create_index('ix_combinations_status', 'combinations', ['status'])
    op.create_index('idx_combination_status_created', 'combinations', ['status', 'created_at'])

    # 创建 mcp_servers 表
    op.create_table(
        'mcp_servers',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(length=255), nullable=False, comment='MCP 服务名称'),
        sa.Column('prefix', sa.String(length=50), nullable=False, comment='MCP 前缀（唯一标识）'),
        sa.Column('description', sa.Text(), nullable=True, comment='MCP 服务描述'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='状态：active/inactive'),
        sa.Column('combination_ids', sa.JSON(), nullable=False, comment='包含的组合 ID 列表'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('prefix')
    )

    # 创建索引
    op.create_index('ix_mcp_servers_id', 'mcp_servers', ['id'])
    op.create_index('ix_mcp_servers_name', 'mcp_servers', ['name'])
    op.create_index('ix_mcp_servers_prefix', 'mcp_servers', ['prefix'], unique=True)
    op.create_index('ix_mcp_servers_status', 'mcp_servers', ['status'])
    op.create_index('idx_mcp_server_prefix_status', 'mcp_servers', ['prefix', 'status'])


def downgrade() -> None:
    """降级：删除表"""
    op.drop_table('mcp_servers')
    op.drop_table('combinations')
