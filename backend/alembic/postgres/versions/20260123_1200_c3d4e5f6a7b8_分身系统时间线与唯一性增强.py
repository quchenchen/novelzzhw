"""分身系统时间线与唯一性增强

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-01-23 12:00:00.000000

本次迁移包含以下改进：
1. 添加 exposed_at_chapter 字段到 identities 表
   - 记录身份在第几章被暴露
   - 用于实现时间线感知的身份状态计算
   - 生成第N章时，若N<exposed_at_chapter则身份状态为active

2. 添加唯一性约束到 organization_members 表
   - 防止同一角色的同一身份在同一组织中产生多条记录
   - 使用部分索引实现条件唯一性

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 添加 exposed_at_chapter 列到 identities 表
    op.add_column('identities',
        sa.Column('exposed_at_chapter', sa.Integer(), nullable=True)
    )

    # 为 exposed_at_chapter 添加索引
    op.create_index(
        'ix_identities_exposed_at_chapter',
        'identities', ['exposed_at_chapter'],
        unique=False
    )

    # 2. 添加唯一性约束到 organization_members 表
    # 对于有 identity_id 的记录：organization_id + character_id 必须唯一
    op.create_index(
        'idx_org_member_identity_unique',
        'organization_members',
        ['organization_id', 'character_id'],
        unique=True,
        postgresql_where=sa.text("identity_id IS NOT NULL")
    )

    # 对于没有 identity_id 的记录：organization_id + character_id 必须唯一
    op.create_index(
        'idx_org_member_character_unique',
        'organization_members',
        ['organization_id', 'character_id'],
        unique=True,
        postgresql_where=sa.text("identity_id IS NULL")
    )


def downgrade() -> None:
    # 删除唯一性约束
    op.drop_index('idx_org_member_character_unique', table_name='organization_members')
    op.drop_index('idx_org_member_identity_unique', table_name='organization_members')

    # 删除 exposed_at_chapter 索引
    op.drop_index('ix_identities_exposed_at_chapter', table_name='identities')

    # 删除 exposed_at_chapter 列
    op.drop_column('identities', 'exposed_at_chapter')
