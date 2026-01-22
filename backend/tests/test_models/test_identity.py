"""
身份系统模型测试

测试 Identity, IdentityCareer, IdentityKnowledge 模型的基本功能
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.identity import Identity
from app.models.identity_career import IdentityCareer
from app.models.identity_knowledge import IdentityKnowledge
from app.models.character import Character
from app.models.career import Career
from app.models.project import Project


@pytest.mark.asyncio
class TestIdentityModel:
    """测试 Identity 模型"""

    async def test_create_identity(self, db_session: AsyncSession, test_project: Project, test_character: Character):
        """测试创建身份"""
        identity = Identity(
            project_id=test_project.id,
            character_id=test_character.id,
            name="伪装身份",
            identity_type="disguise",
            is_primary=False,
            appearance="普通书生模样",
            personality="温和有礼",
            background="来自江南的书生",
            voice_style="文绉绉",
            status="active"
        )
        db_session.add(identity)
        await db_session.commit()
        await db_session.refresh(identity)

        assert identity.id is not None
        assert identity.name == "伪装身份"
        assert identity.identity_type == "disguise"
        assert identity.is_primary is False
        assert identity.status == "active"

    async def test_identity_repr(self, db_session: AsyncSession, test_project: Project, test_character: Character):
        """测试 Identity 的 __repr__ 方法"""
        identity = Identity(
            project_id=test_project.id,
            character_id=test_character.id,
            name="测试身份",
            identity_type="secret"
        )
        db_session.add(identity)
        await db_session.commit()
        await db_session.refresh(identity)

        repr_str = repr(identity)
        assert "Identity" in repr_str
        assert identity.id in repr_str
        assert "测试身份" in repr_str

    async def test_identity_default_values(self, db_session: AsyncSession, test_project: Project, test_character: Character):
        """测试 Identity 的默认值"""
        identity = Identity(
            project_id=test_project.id,
            character_id=test_character.id,
            name="默认测试"
        )
        db_session.add(identity)
        await db_session.commit()
        await db_session.refresh(identity)

        assert identity.is_primary is False  # 默认不是主身份
        assert identity.identity_type == "real"  # 默认类型
        assert identity.status == "active"  # 默认状态


@pytest.mark.asyncio
class TestIdentityCareerModel:
    """测试 IdentityCareer 模型"""

    async def test_create_identity_career(self, db_session: AsyncSession, test_identity: Identity, test_career: Career):
        """测试创建身份职业关联"""
        identity_career = IdentityCareer(
            identity_id=test_identity.id,
            career_id=test_career.id,
            career_type="main",
            current_stage=3,
            stage_progress=50,
            started_at="第5章",
            reached_current_stage_at="第20章"
        )
        db_session.add(identity_career)
        await db_session.commit()
        await db_session.refresh(identity_career)

        assert identity_career.id is not None
        assert identity_career.current_stage == 3
        assert identity_career.stage_progress == 50
        assert identity_career.started_at == "第5章"

    async def test_identity_career_default_values(self, db_session: AsyncSession, test_identity: Identity, test_career: Career):
        """测试 IdentityCareer 的默认值"""
        identity_career = IdentityCareer(
            identity_id=test_identity.id,
            career_id=test_career.id,
            career_type="sub"
        )
        db_session.add(identity_career)
        await db_session.commit()
        await db_session.refresh(identity_career)

        assert identity_career.current_stage == 1  # 默认阶段
        assert identity_career.stage_progress == 0  # 默认进度

    async def test_identity_career_repr(self, db_session: AsyncSession, test_identity: Identity, test_career: Career):
        """测试 IdentityCareer 的 __repr__ 方法"""
        identity_career = IdentityCareer(
            identity_id=test_identity.id,
            career_id=test_career.id,
            career_type="main"
        )
        db_session.add(identity_career)
        await db_session.commit()
        await db_session.refresh(identity_career)

        repr_str = repr(identity_career)
        assert "IdentityCareer" in repr_str


@pytest.mark.asyncio
class TestIdentityKnowledgeModel:
    """测试 IdentityKnowledge 模型"""

    async def test_create_identity_knowledge(self, db_session: AsyncSession, test_identity: Identity, test_knower_character: Character):
        """测试创建认知关系"""
        knowledge = IdentityKnowledge(
            identity_id=test_identity.id,
            knower_character_id=test_knower_character.id,
            knowledge_level="full",
            since_when="第10章",
            discovered_how="偶然目击",
            is_secret=True
        )
        db_session.add(knowledge)
        await db_session.commit()
        await db_session.refresh(knowledge)

        assert knowledge.id is not None
        assert knowledge.knowledge_level == "full"
        assert knowledge.discovered_how == "偶然目击"
        assert knowledge.is_secret is True

    async def test_identity_knowledge_default_values(self, db_session: AsyncSession, test_identity: Identity, test_knower_character: Character):
        """测试 IdentityKnowledge 的默认值"""
        knowledge = IdentityKnowledge(
            identity_id=test_identity.id,
            knower_character_id=test_knower_character.id,
            knowledge_level="suspected"
        )
        db_session.add(knowledge)
        await db_session.commit()
        await db_session.refresh(knowledge)

        assert knowledge.is_secret is True  # 默认是秘密

    async def test_identity_knowledge_repr(self, db_session: AsyncSession, test_identity: Identity, test_knower_character: Character):
        """测试 IdentityKnowledge 的 __repr__ 方法"""
        knowledge = IdentityKnowledge(
            identity_id=test_identity.id,
            knower_character_id=test_knower_character.id,
            knowledge_level="partial"
        )
        db_session.add(knowledge)
        await db_session.commit()
        await db_session.refresh(knowledge)

        repr_str = repr(knowledge)
        assert "IdentityKnowledge" in repr_str


@pytest.mark.asyncio
class TestIdentityRelationships:
    """测试身份系统模型关系"""

    async def test_identity_character_relationship(
        self,
        db_session: AsyncSession,
        test_project: Project,
        test_character: Character
    ):
        """测试身份与角色的关系"""
        identity = Identity(
            project_id=test_project.id,
            character_id=test_character.id,
            name="测试身份"
        )
        db_session.add(identity)
        await db_session.commit()
        await db_session.refresh(identity)

        # 通过 identity 查询关联的 character
        result = await db_session.execute(
            select(Character).where(Character.id == identity.character_id)
        )
        character = result.scalar_one_or_none()

        assert character is not None
        assert character.id == test_character.id
        assert character.name == "主角张三"

    async def test_identity_career_relationship(
        self,
        db_session: AsyncSession,
        test_identity: Identity,
        test_career: Career
    ):
        """测试身份职业与职业的关系"""
        identity_career = IdentityCareer(
            identity_id=test_identity.id,
            career_id=test_career.id,
            career_type="main"
        )
        db_session.add(identity_career)
        await db_session.commit()

        # 查询身份的所有职业
        result = await db_session.execute(
            select(IdentityCareer).where(IdentityCareer.identity_id == test_identity.id)
        )
        careers = result.scalars().all()

        assert len(careers) == 1
        assert careers[0].career_id == test_career.id

    async def test_identity_knowledge_relationship(
        self,
        db_session: AsyncSession,
        test_identity: Identity,
        test_knower_character: Character
    ):
        """测试认知关系的双向查询"""
        knowledge = IdentityKnowledge(
            identity_id=test_identity.id,
            knower_character_id=test_knower_character.id,
            knowledge_level="partial"
        )
        db_session.add(knowledge)
        await db_session.commit()

        # 查询身份的认知关系
        result = await db_session.execute(
            select(IdentityKnowledge).where(IdentityKnowledge.identity_id == test_identity.id)
        )
        knowledge_list = result.scalars().all()

        assert len(knowledge_list) == 1
        assert knowledge_list[0].knower_character_id == test_knower_character.id


@pytest.mark.asyncio
class TestIdentityCascadeDelete:
    """测试级联删除"""

    async def test_delete_identity_deletes_careers(
        self,
        db_session: AsyncSession,
        test_identity: Identity,
        test_career: Career
    ):
        """测试删除身份时级联删除职业关联"""
        # 创建职业关联
        identity_career = IdentityCareer(
            identity_id=test_identity.id,
            career_id=test_career.id,
            career_type="main"
        )
        db_session.add(identity_career)
        await db_session.commit()

        # 删除身份
        await db_session.delete(test_identity)
        await db_session.commit()

        # 验证职业关联已被删除
        result = await db_session.execute(
            select(IdentityCareer).where(IdentityCareer.identity_id == test_identity.id)
        )
        careers = result.scalars().all()

        assert len(careers) == 0

    async def test_delete_identity_deletes_knowledge(
        self,
        db_session: AsyncSession,
        test_identity: Identity,
        test_knower_character: Character
    ):
        """测试删除身份时级联删除认知关系"""
        # 创建认知关系
        knowledge = IdentityKnowledge(
            identity_id=test_identity.id,
            knower_character_id=test_knower_character.id,
            knowledge_level="full"
        )
        db_session.add(knowledge)
        await db_session.commit()

        # 删除身份
        await db_session.delete(test_identity)
        await db_session.commit()

        # 验证认知关系已被删除
        result = await db_session.execute(
            select(IdentityKnowledge).where(IdentityKnowledge.identity_id == test_identity.id)
        )
        knowledge_list = result.scalars().all()

        assert len(knowledge_list) == 0


@pytest.mark.asyncio
class TestIdentityConstraints:
    """测试身份系统约束"""

    async def test_identity_types(self, db_session: AsyncSession, test_project: Project, test_character: Character):
        """测试所有有效的身份类型"""
        valid_types = ["real", "public", "secret", "disguise"]

        for identity_type in valid_types:
            identity = Identity(
                project_id=test_project.id,
                character_id=test_character.id,
                name=f"{identity_type}_身份",
                identity_type=identity_type
            )
            db_session.add(identity)
            await db_session.commit()
            await db_session.refresh(identity)

            assert identity.identity_type == identity_type

    async def test_identity_statuses(self, db_session: AsyncSession, test_project: Project, test_character: Character):
        """测试所有有效的身份状态"""
        valid_statuses = ["active", "inactive", "burned"]

        for status in valid_statuses:
            identity = Identity(
                project_id=test_project.id,
                character_id=test_character.id,
                name=f"{status}_身份",
                status=status
            )
            db_session.add(identity)
            await db_session.commit()
            await db_session.refresh(identity)

            assert identity.status == status

    async def test_knowledge_levels(self, db_session: AsyncSession, test_identity: Identity, test_knower_character: Character):
        """测试所有有效的认知程度"""
        valid_levels = ["full", "partial", "suspected"]

        for level in valid_levels:
            knowledge = IdentityKnowledge(
                identity_id=test_identity.id,
                knower_character_id=test_knower_character.id,
                knowledge_level=level
            )
            db_session.add(knowledge)
            await db_session.commit()
            await db_session.refresh(knowledge)

            assert knowledge.knowledge_level == level

    async def test_career_types(self, db_session: AsyncSession, test_identity: Identity, test_career: Career):
        """测试所有有效的职业类型"""
        valid_types = ["main", "sub"]

        for career_type in valid_types:
            identity_career = IdentityCareer(
                identity_id=test_identity.id,
                career_id=test_career.id,
                career_type=career_type
            )
            db_session.add(identity_career)
            await db_session.commit()
            await db_session.refresh(identity_career)

            assert identity_career.career_type == career_type
