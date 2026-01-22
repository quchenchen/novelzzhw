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
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('character_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('identity_type', sa.String(length=50), nullable=False, server_default='real'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('appearance', sa.Text(), nullable=True),
        sa.Column('personality', sa.Text(), nullable=True),
        sa.Column('background', sa.Text(), nullable=True),
        sa.Column('voice_style', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_identities_identity_type'), 'identities', ['identity_type'], unique=False)
    op.create_index(op.f('ix_identities_status'), 'identities', ['status'], unique=False)
    op.create_index(op.f('ix_identities_project_id'), 'identities', ['project_id'], unique=False)
    op.create_index(op.f('ix_identities_character_id'), 'identities', ['character_id'], unique=False)

    # 创建身份职业关联表 (identity_careers)
    op.create_table('identity_careers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('identity_id', sa.String(length=36), nullable=False),
        sa.Column('career_id', sa.String(length=36), nullable=False),
        sa.Column('career_type', sa.String(length=50), nullable=False),
        sa.Column('current_stage', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('stage_progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.String(length=100), nullable=True),
        sa.Column('reached_current_stage_at', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['career_id'], ['careers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('identity_id', 'career_id', name='uq_identity_career')
    )
    op.create_index(op.f('ix_identity_careers_career_type'), 'identity_careers', ['career_type'], unique=False)
    op.create_index(op.f('ix_identity_careers_identity_id'), 'identity_careers', ['identity_id'], unique=False)
    op.create_index(op.f('ix_identity_careers_career_id'), 'identity_careers', ['career_id'], unique=False)

    # 创建身份认知关系表 (identity_knowledge)
    op.create_table('identity_knowledge',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('identity_id', sa.String(length=36), nullable=False),
        sa.Column('knower_character_id', sa.String(length=36), nullable=False),
        sa.Column('knowledge_level', sa.String(length=50), nullable=False),
        sa.Column('since_when', sa.String(length=100), nullable=True),
        sa.Column('discovered_how', sa.Text(), nullable=True),
        sa.Column('is_secret', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['identity_id'], ['identities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knower_character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('identity_id', 'knower_character_id', name='uq_identity_knower')
    )
    op.create_index(op.f('ix_identity_knowledge_knowledge_level'), 'identity_knowledge', ['knowledge_level'], unique=False)
    op.create_index(op.f('ix_identity_knowledge_identity_id'), 'identity_knowledge', ['identity_id'], unique=False)
    op.create_index(op.f('ix_identity_knowledge_knower_character_id'), 'identity_knowledge', ['knower_character_id'], unique=False)


def downgrade() -> None:
    # 删除身份认知关系表
    op.drop_index(op.f('ix_identity_knowledge_knower_character_id'), table_name='identity_knowledge')
    op.drop_index(op.f('ix_identity_knowledge_identity_id'), table_name='identity_knowledge')
    op.drop_index(op.f('ix_identity_knowledge_knowledge_level'), table_name='identity_knowledge')
    op.drop_table('identity_knowledge')

    # 删除身份职业关联表
    op.drop_index(op.f('ix_identity_careers_career_id'), table_name='identity_careers')
    op.drop_index(op.f('ix_identity_careers_identity_id'), table_name='identity_careers')
    op.drop_index(op.f('ix_identity_careers_career_type'), table_name='identity_careers')
    op.drop_table('identity_careers')

    # 删除身份表
    op.drop_index(op.f('ix_identities_character_id'), table_name='identities')
    op.drop_index(op.f('ix_identities_project_id'), table_name='identities')
    op.drop_index(op.f('ix_identities_status'), table_name='identities')
    op.drop_index(op.f('ix_identities_identity_type'), table_name='identities')
    op.drop_table('identities')
