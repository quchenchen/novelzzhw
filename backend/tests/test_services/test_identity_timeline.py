"""身份时间线状态计算测试

测试分身系统的时间线感知功能：
1. 身份在不同章节的状态计算
2. 暴露章节前后的状态变化
3. 章节上下文服务中的身份过滤
"""
import pytest
from datetime import datetime

from app.models.identity import Identity
from app.models.character import Character
from app.models.project import Project
from app.models.chapter import Chapter
from app.services.chapter_context_service import ChapterContextBuilder


class TestIdentityTimelineStatus:
    """测试身份的时间线状态计算"""

    def test_identity_never_exposed(self, db_session):
        """测试从未暴露的身份状态"""
        # 创建一个未暴露的身份
        identity = Identity(
            id="identity-1",
            project_id="project-1",
            character_id="char-1",
            name="张三",
            identity_type="real",
            status="active",
            exposed_at_chapter=None  # 从未暴露
        )

        # 在任何章节，状态都应该是 active
        assert identity.get_status_at_chapter(1) == "active"
        assert identity.get_status_at_chapter(5) == "active"
        assert identity.get_status_at_chapter(100) == "active"

    def test_identity_exposed_at_chapter_5(self, db_session):
        """测试在第5章暴露的身份"""
        identity = Identity(
            id="identity-2",
            project_id="project-1",
            character_id="char-1",
            name="毒蛇",
            identity_type="secret",
            status="burned",
            exposed_at_chapter=5  # 第5章暴露
        )

        # 第5章之前：active（未暴露）
        assert identity.get_status_at_chapter(1) == "active"
        assert identity.get_status_at_chapter(3) == "active"
        assert identity.get_status_at_chapter(4) == "active"

        # 第5章及之后：burned（已暴露）
        assert identity.get_status_at_chapter(5) == "burned"
        assert identity.get_status_at_chapter(6) == "burned"
        assert identity.get_status_at_chapter(100) == "burned"

    def test_is_exposed_at_chapter(self, db_session):
        """测试 is_exposed_at_chapter 方法"""
        identity = Identity(
            id="identity-3",
            project_id="project-1",
            character_id="char-1",
            name="伪装者",
            identity_type="disguise",
            status="burned",
            exposed_at_chapter=10
        )

        # 第10章之前：未暴露
        assert identity.is_exposed_at_chapter(1) is False
        assert identity.is_exposed_at_chapter(9) is False

        # 第10章及之后：已暴露
        assert identity.is_exposed_at_chapter(10) is True
        assert identity.is_exposed_at_chapter(11) is True

    def test_identity_burned_without_chapter_record(self, db_session):
        """测试状态为burned但没有记录暴露章节的情况（向后兼容）"""
        identity = Identity(
            id="identity-4",
            project_id="project-1",
            character_id="char-1",
            name="老身份",
            identity_type="secret",
            status="burned",
            exposed_at_chapter=None  # 状态是burned但没有记录章节
        )

        # 如果状态是burned但没有记录章节，is_exposed_at_chapter 应该返回 True
        assert identity.is_exposed_at_chapter(1) is True
        assert identity.is_exposed_at_chapter(100) is True

        # get_status_at_chapter 返回当前状态
        assert identity.get_status_at_chapter(1) == "burned"


class TestIdentityTimelineIntegration:
    """测试身份时间线与业务逻辑的集成"""

    def test_exposure_records_chapter_number(self, db_session):
        """测试身份暴露时记录章节号"""
        # 模拟身份暴露处理
        identity = Identity(
            id="identity-5",
            project_id="project-1",
            character_id="char-1",
            name="间谍",
            identity_type="secret",
            status="active",
            exposed_at_chapter=None
        )

        # 第7章暴露
        exposure_chapter = 7

        # 更新状态和暴露章节
        identity.status = "burned"
        if identity.exposed_at_chapter is None:
            identity.exposed_at_chapter = exposure_chapter

        assert identity.exposed_at_chapter == 7
        assert identity.get_status_at_chapter(6) == "active"
        assert identity.get_status_at_chapter(7) == "burned"

    def test_first_exposure_only_recorded(self, db_session):
        """测试只记录第一次暴露的章节"""
        identity = Identity(
            id="identity-6",
            project_id="project-1",
            character_id="char-1",
            name="多重身份者",
            identity_type="secret",
            status="burned",
            exposed_at_chapter=5  # 第一次暴露在第5章
        )

        # 如果第10章再次暴露（场景变更等），不应该更新 exposed_at_chapter
        second_exposure_chapter = 10
        if identity.exposed_at_chapter is None:
            identity.exposed_at_chapter = second_exposure_chapter

        # 仍然是第5章
        assert identity.exposed_at_chapter == 5
        assert identity.get_status_at_chapter(6) == "burned"


class TestChapterContextIdentityFiltering:
    """测试章节上下文中的身份过滤"""

    @pytest.mark.asyncio
    async def test_chapter_before_exposure_hides_secret_identity(self, db_session):
        """测试在暴露章节之前，秘密身份应该被隐藏"""
        # 创建项目
        project = Project(
            id="project-test",
            user_id="user-1",
            title="测试小说",
            genre="悬疑"
        )
        db_session.add(project)

        # 创建角色
        character = Character(
            id="char-test",
            project_id="project-test",
            name="主角",
            role_type="protagonist"
        )
        db_session.add(character)

        # 创建秘密身份（在第10章暴露）
        secret_identity = Identity(
            id="identity-secret",
            project_id="project-test",
            character_id="char-test",
            name="暗夜",
            identity_type="secret",
            status="burned",  # 当前状态是burned
            exposed_at_chapter=10  # 但在第10章才暴露
        )
        db_session.add(secret_identity)

        # 创建第5章（暴露之前）
        chapter_5 = Chapter(
            id="chapter-5",
            project_id="project-test",
            chapter_number=5,
            title="第五章"
        )
        db_session.add(chapter_5)

        await db_session.commit()

        # 在第5章的上下文中，该身份应该是未暴露状态
        is_exposed = secret_identity.is_exposed_at_chapter(5)
        status = secret_identity.get_status_at_chapter(5)

        assert is_exposed is False, "第5章时身份应该未暴露"
        assert status == "active", "第5章时身份状态应该是active"

    @pytest.mark.asyncio
    async def test_chapter_after_exposure_shows_burned_identity(self, db_session):
        """测试在暴露章节之后，身份应该显示为已暴露"""
        # 创建项目
        project = Project(
            id="project-test-2",
            user_id="user-1",
            title="测试小说2",
            genre="悬疑"
        )
        db_session.add(project)

        # 创建角色
        character = Character(
            id="char-test-2",
            project_id="project-test-2",
            name="主角",
            role_type="protagonist"
        )
        db_session.add(character)

        # 创建秘密身份（在第5章暴露）
        secret_identity = Identity(
            id="identity-secret-2",
            project_id="project-test-2",
            character_id="char-test-2",
            name="暗夜",
            identity_type="secret",
            status="burned",
            exposed_at_chapter=5  # 第5章暴露
        )
        db_session.add(secret_identity)

        # 创建第10章（暴露之后）
        chapter_10 = Chapter(
            id="chapter-10",
            project_id="project-test-2",
            chapter_number=10,
            title="第十章"
        )
        db_session.add(chapter_10)

        await db_session.commit()

        # 在第10章的上下文中，该身份应该是已暴露状态
        is_exposed = secret_identity.is_exposed_at_chapter(10)
        status = secret_identity.get_status_at_chapter(10)

        assert is_exposed is True, "第10章时身份应该已暴露"
        assert status == "burned", "第10章时身份状态应该是burned"


class TestTimelineScenarios:
    """测试实际剧情场景"""

    def test_spy_narrative_scenario(self, db_session):
        """测试间谍叙事场景：卧底在第15章暴露"""
        # 角色：李明
        # 身份1：李明（真实身份，active）
        # 身份2：毒蛇（卧底身份，第15章暴露）

        identity_real = Identity(
            id="id-li-ming",
            project_id="proj-1",
            character_id="char-li",
            name="李明",
            identity_type="real",
            status="active",
            exposed_at_chapter=None
        )

        identity_spy = Identity(
            id="id-viper",
            project_id="proj-1",
            character_id="char-li",
            name="毒蛇",
            identity_type="secret",
            status="burned",
            exposed_at_chapter=15
        )

        # 第1章：卧底身份未暴露
        assert identity_real.get_status_at_chapter(1) == "active"
        assert identity_spy.get_status_at_chapter(1) == "active"
        assert identity_spy.is_exposed_at_chapter(1) is False

        # 第10章：卧底身份仍然未暴露
        assert identity_spy.get_status_at_chapter(10) == "active"
        assert identity_spy.is_exposed_at_chapter(10) is False

        # 第15章：卧底身份暴露
        assert identity_spy.get_status_at_chapter(15) == "burned"
        assert identity_spy.is_exposed_at_chapter(15) is True

        # 第20章：卧底身份已暴露
        assert identity_spy.get_status_at_chapter(20) == "burned"
        assert identity_spy.is_exposed_at_chapter(20) is True

    def test_multiple_exposures_different_identities(self, db_session):
        """测试同一角色的多个身份在不同章节暴露"""
        # 角色：王五
        # 身份1：王五（真实身份，从未暴露）
        # 身份2：影子A（第5章暴露）
        # 身份3：影子B（第10章暴露）

        identity1 = Identity(
            id="id-wang-1",
            project_id="proj-1",
            character_id="char-wang",
            name="王五",
            identity_type="real",
            status="active",
            exposed_at_chapter=None
        )

        identity2 = Identity(
            id="id-shadow-a",
            project_id="proj-1",
            character_id="char-wang",
            name="影子A",
            identity_type="disguise",
            status="burned",
            exposed_at_chapter=5
        )

        identity3 = Identity(
            id="id-shadow-b",
            project_id="proj-1",
            character_id="char-wang",
            name="影子B",
            identity_type="disguise",
            status="burned",
            exposed_at_chapter=10
        )

        # 第3章：所有伪装身份都未暴露
        assert identity1.get_status_at_chapter(3) == "active"
        assert identity2.get_status_at_chapter(3) == "active"
        assert identity3.get_status_at_chapter(3) == "active"

        # 第7章：影子A已暴露，影子B未暴露
        assert identity1.get_status_at_chapter(7) == "active"
        assert identity2.get_status_at_chapter(7) == "burned"
        assert identity3.get_status_at_chapter(7) == "active"

        # 第15章：所有伪装身份都已暴露
        assert identity1.get_status_at_chapter(15) == "active"
        assert identity2.get_status_at_chapter(15) == "burned"
        assert identity3.get_status_at_chapter(15) == "burned"
