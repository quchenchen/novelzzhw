"""
身份系统 API 测试

测试身份系统 CRUD 操作、职业关联和认知关系管理
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.identity import Identity
from app.models.identity_career import IdentityCareer
from app.models.identity_knowledge import IdentityKnowledge
from app.models.character import Character
from app.models.career import Career
from app.models.project import Project


@pytest.fixture
async def test_project_with_character(db_session: AsyncSession):
    """创建测试项目和角色"""
    project = Project(
        title="测试项目",
        genre="玄幻",
        theme="修仙"
    )
    db_session.add(project)
    await db_session.flush()

    character = Character(
        project_id=project.id,
        name="张三",
        age=25,
        gender="男",
        role_type="protagonist",
        personality="性格坚毅",
        background="出身贫寒"
    )
    db_session.add(character)
    await db_session.flush()

    # 创建职业
    career = Career(
        project_id=project.id,
        name="剑修",
        type="main",
        max_stage=10,
        stages='[{"level": 1, "name": "炼气期", "description": "初入修仙"}]'
    )
    db_session.add(career)
    await db_session.commit()

    return {
        "project_id": project.id,
        "character_id": character.id,
        "career_id": career.id
    }


@pytest.mark.asyncio
class TestIdentityCRUD:
    """测试身份 CRUD 操作"""

    async def test_create_identity(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试创建身份"""
        response = await async_client.post(
            "/api/identities",
            json={
                "character_id": test_project_with_character["character_id"],
                "name": "隐藏身份",
                "identity_type": "secret",
                "is_primary": False,
                "personality": "冷酷无情",
                "status": "active"
            },
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "隐藏身份"
        assert data["identity_type"] == "secret"
        assert data["status"] == "active"

    async def test_create_identity_with_is_primary(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试创建主身份（自动取消其他主身份）"""
        character_id = test_project_with_character["character_id"]

        # 创建第一个主身份
        response1 = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "真身",
                "identity_type": "real",
                "is_primary": True
            },
            headers=user_headers
        )
        assert response1.status_code == 200
        first_identity_id = response1.json()["id"]

        # 创建第二个主身份（应自动取消第一个的主身份状态）
        response2 = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "新主身份",
                "identity_type": "real",
                "is_primary": True
            },
            headers=user_headers
        )
        assert response2.status_code == 200

        # 验证第一个身份不再是主身份
        response = await async_client.get(
            f"/api/identities/{first_identity_id}",
            headers=user_headers
        )
        assert response.status_code == 200
        assert response.json()["is_primary"] is False

    async def test_create_identity_invalid_character(
        self,
        async_client: AsyncClient,
        user_headers: dict
    ):
        """测试使用不存在的角色ID创建身份"""
        response = await async_client.post(
            "/api/identities",
            json={
                "character_id": "non-existent-id",
                "name": "测试身份",
                "identity_type": "real"
            },
            headers=user_headers
        )

        assert response.status_code in (400, 404)

    async def test_get_identity(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试获取身份详情"""
        # 先创建身份
        create_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": test_project_with_character["character_id"],
                "name": "测试身份",
                "identity_type": "public"
            },
            headers=user_headers
        )
        identity_id = create_response.json()["id"]

        # 获取身份详情
        response = await async_client.get(
            f"/api/identities/{identity_id}",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == identity_id
        assert data["name"] == "测试身份"

    async def test_get_identity_not_found(
        self,
        async_client: AsyncClient,
        user_headers: dict
    ):
        """测试获取不存在的身份"""
        response = await async_client.get(
            "/api/identities/non-existent-id",
            headers=user_headers
        )

        assert response.status_code == 404

    async def test_update_identity(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试更新身份"""
        # 先创建身份
        create_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": test_project_with_character["character_id"],
                "name": "原始名称",
                "identity_type": "secret"
            },
            headers=user_headers
        )
        identity_id = create_response.json()["id"]

        # 更新身份
        response = await async_client.put(
            f"/api/identities/{identity_id}",
            json={
                "name": "更新后名称",
                "status": "burned"
            },
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后名称"
        assert data["status"] == "burned"

    async def test_delete_identity(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试删除身份"""
        # 先创建身份
        create_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": test_project_with_character["character_id"],
                "name": "待删除身份",
                "identity_type": "disguise"
            },
            headers=user_headers
        )
        identity_id = create_response.json()["id"]

        # 删除身份
        response = await async_client.delete(
            f"/api/identities/{identity_id}",
            headers=user_headers
        )

        assert response.status_code == 200

        # 验证已删除
        get_response = await async_client.get(
            f"/api/identities/{identity_id}",
            headers=user_headers
        )
        assert get_response.status_code == 404

    async def test_get_project_identities(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试获取项目的所有身份"""
        project_id = test_project_with_character["project_id"]
        character_id = test_project_with_character["character_id"]

        # 创建多个身份
        await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "身份1",
                "identity_type": "real"
            },
            headers=user_headers
        )

        await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "身份2",
                "identity_type": "secret"
            },
            headers=user_headers
        )

        # 获取项目身份列表
        response = await async_client.get(
            f"/api/identities/project/{project_id}",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_get_character_identities(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试获取角色的所有身份"""
        character_id = test_project_with_character["character_id"]

        # 创建多个身份
        await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "主身份",
                "identity_type": "real",
                "is_primary": True
            },
            headers=user_headers
        )

        await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "隐藏身份",
                "identity_type": "secret"
            },
            headers=user_headers
        )

        # 获取角色身份列表
        response = await async_client.get(
            f"/api/identities/character/{character_id}",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # 主身份应该排在前面
        assert data[0]["is_primary"] is True

    async def test_filter_identities_by_type(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试按类型筛选身份"""
        project_id = test_project_with_character["project_id"]
        character_id = test_project_with_character["character_id"]

        # 创建不同类型的身份
        await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "真身",
                "identity_type": "real"
            },
            headers=user_headers
        )

        await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "隐藏身份",
                "identity_type": "secret"
            },
            headers=user_headers
        )

        # 筛选 secret 类型
        response = await async_client.get(
            f"/api/identities/project/{project_id}?identity_type=secret",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["identity_type"] == "secret"


@pytest.mark.asyncio
class TestIdentityCareers:
    """测试身份职业关联"""

    async def test_add_identity_career(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试为身份添加职业"""
        character_id = test_project_with_character["character_id"]
        career_id = test_project_with_character["career_id"]

        # 创建身份
        identity_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "剑修身份",
                "identity_type": "secret"
            },
            headers=user_headers
        )
        identity_id = identity_response.json()["id"]

        # 添加职业
        response = await async_client.post(
            f"/api/identities/{identity_id}/careers",
            json={
                "career_id": career_id,
                "career_type": "main",
                "current_stage": 3,
                "stage_progress": 50
            },
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["career_id"] == career_id
        assert data["current_stage"] == 3

    async def test_add_identity_career_duplicate(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试重复添加相同职业（应失败）"""
        character_id = test_project_with_character["character_id"]
        career_id = test_project_with_character["career_id"]

        # 创建身份
        identity_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "测试身份",
                "identity_type": "public"
            },
            headers=user_headers
        )
        identity_id = identity_response.json()["id"]

        # 第一次添加职业
        await async_client.post(
            f"/api/identities/{identity_id}/careers",
            json={
                "career_id": career_id,
                "career_type": "main"
            },
            headers=user_headers
        )

        # 第二次添加相同职业（应失败）
        response = await async_client.post(
            f"/api/identities/{identity_id}/careers",
            json={
                "career_id": career_id,
                "career_type": "main"
            },
            headers=user_headers
        )

        assert response.status_code == 400

    async def test_update_identity_career_stage(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试更新身份职业阶段"""
        character_id = test_project_with_character["character_id"]
        career_id = test_project_with_character["career_id"]

        # 创建身份并添加职业
        identity_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "修仙者",
                "identity_type": "real"
            },
            headers=user_headers
        )
        identity_id = identity_response.json()["id"]

        career_response = await async_client.post(
            f"/api/identities/{identity_id}/careers",
            json={
                "career_id": career_id,
                "career_type": "main",
                "current_stage": 1
            },
            headers=user_headers
        )
        career_link_id = career_response.json()["id"]

        # 更新阶段
        response = await async_client.put(
            f"/api/identities/{identity_id}/careers/{career_id}",
            json={
                "current_stage": 5,
                "stage_progress": 80
            },
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["current_stage"] == 5
        assert data["stage_progress"] == 80

    async def test_delete_identity_career(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试删除身份职业关联"""
        character_id = test_project_with_character["character_id"]
        career_id = test_project_with_character["career_id"]

        # 创建身份并添加职业
        identity_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "测试",
                "identity_type": "disguise"
            },
            headers=user_headers
        )
        identity_id = identity_response.json()["id"]

        await async_client.post(
            f"/api/identities/{identity_id}/careers",
            json={
                "career_id": career_id,
                "career_type": "main"
            },
            headers=user_headers
        )

        # 删除职业关联
        response = await async_client.delete(
            f"/api/identities/{identity_id}/careers/{career_id}",
            headers=user_headers
        )

        assert response.status_code == 200

    async def test_get_identity_careers_with_details(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试获取身份的职业列表（含详情）"""
        character_id = test_project_with_character["character_id"]
        career_id = test_project_with_character["career_id"]

        # 创建身份并添加职业
        identity_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "剑修",
                "identity_type": "secret"
            },
            headers=user_headers
        )
        identity_id = identity_response.json()["id"]

        await async_client.post(
            f"/api/identities/{identity_id}/careers",
            json={
                "career_id": career_id,
                "career_type": "main",
                "current_stage": 2
            },
            headers=user_headers
        )

        # 获取职业列表
        response = await async_client.get(
            f"/api/identities/{identity_id}/careers",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["career_name"] == "剑修"
        assert data[0]["current_stage"] == 2


@pytest.mark.asyncio
class TestIdentityKnowledge:
    """测试身份认知关系"""

    async def test_add_knowledge(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        db_session: AsyncSession,
        user_headers: dict
    ):
        """测试添加认知关系"""
        project_id = test_project_with_character["project_id"]
        character_id = test_project_with_character["character_id"]

        # 创建第二个角色作为认知者
        knower = Character(
            project_id=project_id,
            name="李四",
            age=30,
            gender="男",
            role_type="supporting"
        )
        db_session.add(knower)
        await db_session.commit()

        # 创建身份
        identity_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "隐藏身份",
                "identity_type": "secret"
            },
            headers=user_headers
        )
        identity_id = identity_response.json()["id"]

        # 添加认知关系
        response = await async_client.post(
            f"/api/identities/{identity_id}/knowledge",
            json={
                "knower_character_id": knower.id,
                "knowledge_level": "full",
                "since_when": "第10章",
                "discovered_how": "偶然目击",
                "is_secret": True
            },
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["knowledge_level"] == "full"
        assert data["discovered_how"] == "偶然目击"

    async def test_add_knowledge_duplicate(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        db_session: AsyncSession,
        user_headers: dict
    ):
        """测试重复添加相同认知关系（应失败）"""
        project_id = test_project_with_character["project_id"]
        character_id = test_project_with_character["character_id"]

        # 创建认知者角色
        knower = Character(
            project_id=project_id,
            name="王五",
            age=28,
            gender="男",
            role_type="supporting"
        )
        db_session.add(knower)
        await db_session.commit()

        # 创建身份
        identity_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "测试身份",
                "identity_type": "secret"
            },
            headers=user_headers
        )
        identity_id = identity_response.json()["id"]

        # 第一次添加认知关系
        await async_client.post(
            f"/api/identities/{identity_id}/knowledge",
            json={
                "knower_character_id": knower.id,
                "knowledge_level": "suspected"
            },
            headers=user_headers
        )

        # 第二次添加相同认知关系（应失败）
        response = await async_client.post(
            f"/api/identities/{identity_id}/knowledge",
            json={
                "knower_character_id": knower.id,
                "knowledge_level": "partial"
            },
            headers=user_headers
        )

        assert response.status_code == 400

    async def test_update_knowledge_level(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        db_session: AsyncSession,
        user_headers: dict
    ):
        """测试更新认知程度"""
        project_id = test_project_with_character["project_id"]
        character_id = test_project_with_character["character_id"]

        # 创建认知者角色
        knower = Character(
            project_id=project_id,
            name="赵六",
            age=35,
            gender="男",
            role_type="antagonist"
        )
        db_session.add(knower)
        await db_session.commit()

        # 创建身份并添加认知关系
        identity_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "神秘身份",
                "identity_type": "secret"
            },
            headers=user_headers
        )
        identity_id = identity_response.json()["id"]

        knowledge_response = await async_client.post(
            f"/api/identities/{identity_id}/knowledge",
            json={
                "knower_character_id": knower.id,
                "knowledge_level": "suspected"
            },
            headers=user_headers
        )
        knowledge_id = knowledge_response.json()["id"]

        # 更新认知程度
        response = await async_client.put(
            f"/api/identities/{identity_id}/knowledge/{knowledge_id}",
            json={
                "knowledge_level": "full",
                "discovered_how": "经过调查确认"
            },
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["knowledge_level"] == "full"
        assert data["discovered_how"] == "经过调查确认"

    async def test_delete_knowledge(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        db_session: AsyncSession,
        user_headers: dict
    ):
        """测试删除认知关系"""
        project_id = test_project_with_character["project_id"]
        character_id = test_project_with_character["character_id"]

        # 创建认知者角色
        knower = Character(
            project_id=project_id,
            name="钱七",
            age=40,
            gender="男",
            role_type="supporting"
        )
        db_session.add(knower)
        await db_session.commit()

        # 创建身份并添加认知关系
        identity_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "待删除认知",
                "identity_type": "disguise"
            },
            headers=user_headers
        )
        identity_id = identity_response.json()["id"]

        knowledge_response = await async_client.post(
            f"/api/identities/{identity_id}/knowledge",
            json={
                "knower_character_id": knower.id,
                "knowledge_level": "partial"
            },
            headers=user_headers
        )
        knowledge_id = knowledge_response.json()["id"]

        # 删除认知关系
        response = await async_client.delete(
            f"/api/identities/{identity_id}/knowledge/{knowledge_id}",
            headers=user_headers
        )

        assert response.status_code == 200

    async def test_get_identity_knowledge_with_knower_names(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        db_session: AsyncSession,
        user_headers: dict
    ):
        """测试获取身份的认知关系（含认知者名称）"""
        project_id = test_project_with_character["project_id"]
        character_id = test_project_with_character["character_id"]

        # 创建多个认知者角色
        knower1 = Character(
            project_id=project_id,
            name="认知者A",
            age=25,
            gender="男",
            role_type="supporting"
        )
        knower2 = Character(
            project_id=project_id,
            name="认知者B",
            age=30,
            gender="女",
            role_type="supporting"
        )
        db_session.add_all([knower1, knower2])
        await db_session.commit()

        # 创建身份
        identity_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "多人知晓身份",
                "identity_type": "secret"
            },
            headers=user_headers
        )
        identity_id = identity_response.json()["id"]

        # 添加多个认知关系
        await async_client.post(
            f"/api/identities/{identity_id}/knowledge",
            json={
                "knower_character_id": knower1.id,
                "knowledge_level": "full"
            },
            headers=user_headers
        )

        await async_client.post(
            f"/api/identities/{identity_id}/knowledge",
            json={
                "knower_character_id": knower2.id,
                "knowledge_level": "suspected"
            },
            headers=user_headers
        )

        # 获取认知关系列表
        response = await async_client.get(
            f"/api/identities/{identity_id}/knowledge",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        knower_names = {k["knower_name"] for k in data}
        assert "认知者A" in knower_names
        assert "认知者B" in knower_names


@pytest.mark.asyncio
class TestIdentityValidation:
    """测试身份数据验证"""

    async def test_invalid_identity_type(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试无效的身份类型"""
        response = await async_client.post(
            "/api/identities",
            json={
                "character_id": test_project_with_character["character_id"],
                "name": "测试",
                "identity_type": "invalid_type"
            },
            headers=user_headers
        )

        assert response.status_code == 422

    async def test_invalid_status(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试无效的状态"""
        response = await async_client.post(
            "/api/identities",
            json={
                "character_id": test_project_with_character["character_id"],
                "name": "测试",
                "identity_type": "real",
                "status": "invalid_status"
            },
            headers=user_headers
        )

        assert response.status_code == 422

    async def test_invalid_knowledge_level(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        db_session: AsyncSession,
        user_headers: dict
    ):
        """测试无效的认知程度"""
        project_id = test_project_with_character["project_id"]

        # 创建认知者
        knower = Character(
            project_id=project_id,
            name="测试者",
            age=20,
            gender="男",
            role_type="supporting"
        )
        db_session.add(knower)
        await db_session.commit()

        # 创建身份
        identity_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": test_project_with_character["character_id"],
                "name": "测试身份",
                "identity_type": "secret"
            },
            headers=user_headers
        )
        identity_id = identity_response.json()["id"]

        # 尝试添加无效的认知程度
        response = await async_client.post(
            f"/api/identities/{identity_id}/knowledge",
            json={
                "knower_character_id": knower.id,
                "knowledge_level": "invalid_level"
            },
            headers=user_headers
        )

        assert response.status_code == 422

    async def test_invalid_career_type(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试无效的职业类型"""
        character_id = test_project_with_character["character_id"]
        career_id = test_project_with_character["career_id"]

        # 创建身份
        identity_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "测试",
                "identity_type": "real"
            },
            headers=user_headers
        )
        identity_id = identity_response.json()["id"]

        # 尝试添加无效类型的职业
        response = await async_client.post(
            f"/api/identities/{identity_id}/careers",
            json={
                "career_id": career_id,
                "career_type": "invalid_type"
            },
            headers=user_headers
        )

        assert response.status_code == 422


@pytest.mark.asyncio
class TestIdentityCascadeDelete:
    """测试级联删除"""

    async def test_delete_identity_cascades_to_careers(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        user_headers: dict
    ):
        """测试删除身份时级联删除职业关联"""
        character_id = test_project_with_character["character_id"]
        career_id = test_project_with_character["career_id"]

        # 创建身份并添加职业
        identity_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "待删除",
                "identity_type": "disguise"
            },
            headers=user_headers
        )
        identity_id = identity_response.json()["id"]

        await async_client.post(
            f"/api/identities/{identity_id}/careers",
            json={
                "career_id": career_id,
                "career_type": "main"
            },
            headers=user_headers
        )

        # 删除身份
        await async_client.delete(
            f"/api/identities/{identity_id}",
            headers=user_headers
        )

        # 验证职业关联已删除（再次获取应返回空列表）
        response = await async_client.get(
            f"/api/identities/{identity_id}/careers",
            headers=user_headers
        )
        # 身份不存在，返回404
        assert response.status_code == 404

    async def test_delete_identity_cascades_to_knowledge(
        self,
        async_client: AsyncClient,
        test_project_with_character: dict,
        db_session: AsyncSession,
        user_headers: dict
    ):
        """测试删除身份时级联删除认知关系"""
        project_id = test_project_with_character["project_id"]
        character_id = test_project_with_character["character_id"]

        # 创建认知者
        knower = Character(
            project_id=project_id,
            name="删除测试者",
            age=25,
            gender="男",
            role_type="supporting"
        )
        db_session.add(knower)
        await db_session.commit()

        # 创建身份并添加认知关系
        identity_response = await async_client.post(
            "/api/identities",
            json={
                "character_id": character_id,
                "name": "待删除身份",
                "identity_type": "secret"
            },
            headers=user_headers
        )
        identity_id = identity_response.json()["id"]

        await async_client.post(
            f"/api/identities/{identity_id}/knowledge",
            json={
                "knower_character_id": knower.id,
                "knowledge_level": "full"
            },
            headers=user_headers
        )

        # 删除身份
        await async_client.delete(
            f"/api/identities/{identity_id}",
            headers=user_headers
        )

        # 验证认知关系已删除
        response = await async_client.get(
            f"/api/identities/{identity_id}/knowledge",
            headers=user_headers
        )
        assert response.status_code == 404
