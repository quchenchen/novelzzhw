"""分身系统时间线与唯一性增强

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-01-23 12:00:00.000000

本次迁移包含以下改进：
1. 添加 exposed_at_chapter 字段到 identities 表
   - 记录身份在第几章被暴露
   - 用于实现时间线感知的身份状态计算
   - 生成第N章时，若N<exposed_at_chapter则身份状态为active

2. 添加唯一性约束提示
   - SQLite 不支持部分索引的条件唯一性
   - 通过应用层逻辑确保唯一性（在 API 层已实现检查）

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
    # 添加 exposed_at_chapter 列到 identities 表
    op.add_column('identities',
        sa.Column('exposed_at_chapter', sa.Integer(), nullable=True)
    )

    # 为 exposed_at_chapter 添加索引
    op.create_index(
        op.f('ix_identities_exposed_at_chapter'),
        'identities', ['exposed_at_chapter'],
        unique=False
    )

    # 注：SQLite 的唯一性约束通过应用层逻辑实现
    # 在 organizations.py 的 add_organization_member 函数中已添加重复检查


def downgrade() -> None:
    # 删除 exposed_at_chapter 索引
    op.drop_index(op.f('ix_identities_exposed_at_chapter'), table_name='identities')

    # 删除 exposed_at_chapter 列
    op.drop_column('identities', 'exposed_at_chapter')
