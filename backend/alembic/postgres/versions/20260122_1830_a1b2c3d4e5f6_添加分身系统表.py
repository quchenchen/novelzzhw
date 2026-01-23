"""添加分身系统表

Revision ID: a1b2c3d4e5f6
Revises: 6a73f37e9adb
Create Date: 2026-01-22 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '6a73f37e9adb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建身份表 (identities)
    op.create_table('identities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False, comment='项目ID'),
        sa.Column('character_id', sa.String(length=36), nullable=False, comment='角色ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='身份名称/别名'),
        sa.Column('identity_type', sa.String(length=50), nullable=False, server_default='real', comment='身份类型: real(真实)/public(公开)/secret(秘密)/disguise(伪装)'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false', comment='是否为主身份'),
        sa.Column('appearance', sa.Text(), nullable=True, comment='外貌描述'),
        sa.Column('personality', sa.Text(), nullable=True, comment='性格表现'),
        sa.Column('background', sa.Text(), nullable=True, comment='身份背景'),
        sa.Column('voice_style', sa.Text(), nullable=True, comment='说话风格'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active', comment='状态: active(活跃)/inactive(未激活)/burned(已暴露)'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_identities_type', 'identities', ['identity_type'], unique=False)
    op.create_index('idx_identities_status', 'identities', ['status'], unique=False)
    op.create_index('idx_identities_project_id', 'identities', ['project_id'], unique=False)
    op.create_index('idx_identities_character_id', 'identities', ['character_id'], unique=False)
    op.create_index('idx_identities_character_type', 'identities', ['character_id', 'identity_type'], unique=False)

    # 创建身份职业关联表 (identity_careers)
    op.create_table('identity_careers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('identity_id', sa.String(length=36), nullable=False, comment='身份ID'),
        sa.Column('career_id', sa.String(length=36), nullable=False, comment='职业ID'),
        sa.Column('career_type', sa.String(length=50), nullable=False, comment='职业类型: main(主职业)/sub(副职业)'),
        sa.Column('current_stage', sa.Integer(), nullable=False, server_default='1', comment='当前阶段'),
        sa.Column('stage_progress', sa.Integer(), nullable=False, server_default='0', comment='阶段内进度(0-100)'),
        sa.Column('started_at', sa.String(length=100), nullable=True, comment='开始修炼时间（小说时间线）'),
        sa.Column('reached_current_stage_at', sa.String(length=100), nullable=True, comment='到达当前阶段时间'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['career_id'], ['careers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('identity_id', 'career_id', name='uq_identity_career')
    )
    op.create_index('idx_identity_careers_type', 'identity_careers', ['career_type'], unique=False)
    op.create_index('idx_identity_careers_identity_id', 'identity_careers', ['identity_id'], unique=False)
    op.create_index('idx_identity_careers_career_id', 'identity_careers', ['career_id'], unique=False)

    # 创建身份认知关系表 (identity_knowledge)
    op.create_table('identity_knowledge',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('identity_id', sa.String(length=36), nullable=False, comment='身份ID'),
        sa.Column('knower_character_id', sa.String(length=36), nullable=False, comment='知道此身份的角色ID'),
        sa.Column('knowledge_level', sa.String(length=50), nullable=False, comment='认知程度: full(完全知晓)/partial(部分知晓)/suspected(怀疑)'),
        sa.Column('since_when', sa.String(length=100), nullable=True, comment='何时开始知道（小说时间线）'),
        sa.Column('discovered_how', sa.Text(), nullable=True, comment='如何发现的'),
        sa.Column('is_secret', sa.Boolean(), nullable=False, server_default='true', comment='是否为秘密'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knower_character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('identity_id', 'knower_character_id', name='uq_identity_knower')
    )
    op.create_index('idx_identity_knowledge_level', 'identity_knowledge', ['knowledge_level'], unique=False)
    op.create_index('idx_identity_knowledge_identity_id', 'identity_knowledge', ['identity_id'], unique=False)
    op.create_index('idx_identity_knowledge_knower_id', 'identity_knowledge', ['knower_character_id'], unique=False)


def downgrade() -> None:
    # 删除身份认知关系表
    op.drop_index('idx_identity_knowledge_knower_id', table_name='identity_knowledge')
    op.drop_index('idx_identity_knowledge_identity_id', table_name='identity_knowledge')
    op.drop_index('idx_identity_knowledge_level', table_name='identity_knowledge')
    op.drop_table('identity_knowledge')

    # 删除身份职业关联表
    op.drop_index('idx_identity_careers_career_id', table_name='identity_careers')
    op.drop_index('idx_identity_careers_identity_id', table_name='identity_careers')
    op.drop_index('idx_identity_careers_type', table_name='identity_careers')
    op.drop_table('identity_careers')

    # 删除身份表
    op.drop_index('idx_identities_character_type', table_name='identities')
    op.drop_index('idx_identities_character_id', table_name='identities')
    op.drop_index('idx_identities_project_id', table_name='identities')
    op.drop_index('idx_identities_status', table_name='identities')
    op.drop_index('idx_identities_type', table_name='identities')
    op.drop_table('identities')
