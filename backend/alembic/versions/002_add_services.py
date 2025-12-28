"""Add services table

Revision ID: 002_add_services
Revises: 001_initial
Create Date: 2025-12-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_services'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级：创建 services 表"""
    op.create_table(
        'services',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(length=255), nullable=False, comment='服务名称'),
        sa.Column('url', sa.Text(), nullable=False, comment='OpenAPI/Swagger 文档地址'),
        sa.Column('type', sa.String(length=50), nullable=False, comment='文档类型'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='状态：healthy/unhealthy'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('ix_services_id', 'services', ['id'])
    op.create_index('ix_services_name', 'services', ['name'])
    op.create_index('ix_services_status', 'services', ['status'])
    op.create_index('idx_service_status_created', 'services', ['status', 'created_at'])


def downgrade() -> None:
    """降级：删除 services 表"""
    op.drop_table('services')
