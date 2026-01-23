"""添加身份ID到组织成员表

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-23 10:00:00.000000

添加 identity_id 字段到 organization_members 表，支持角色的特定身份加入组织。
这使得"同一角色的不同身份可以加入不同组织"成为可能，例如：
- 主角的真实身份加入正义组织
- 主角的隐藏身份加入犯罪组织（卧底场景）

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 identity_id 列到 organization_members 表
    op.add_column('organization_members',
        sa.Column('identity_id', sa.String(length=36), nullable=True)
    )

    # 创建外键约束
    op.create_foreign_key(
        'fk_organization_members_identity_id',
        'organization_members', 'identities',
        ['identity_id'], ['id'],
        ondelete='SET NULL'
    )

    # 创建索引以提高查询性能
    op.create_index(
        'ix_organization_members_identity_id',
        'organization_members', ['identity_id'],
        unique=False
    )


def downgrade() -> None:
    # 删除索引
    op.drop_index('ix_organization_members_identity_id', table_name='organization_members')

    # 删除外键约束
    op.drop_constraint('fk_organization_members_identity_id', 'organization_members', type_='foreignkey')

    # 删除列
    op.drop_column('organization_members', 'identity_id')
