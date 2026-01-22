"""
身份系统测试配置文件

提供测试所需的 fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models.base import Base
from app.models.project import Project
from app.models.character import Character
from app.models.career import Career
from app.models.identity import Identity
from app.models.identity_career import IdentityCareer
from app.models.identity_knowledge import IdentityKnowledge


# 测试数据库 URL（使用内存 SQLite）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    # 创建异步引擎
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # 创建会话工厂
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # 创建会话
    async with async_session_maker() as session:
        yield session

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def user_headers() -> dict:
    """模拟已登录用户的请求头"""
    return {
        "X-User-ID": "test-user-id",
        "Authorization": "Bearer test-token"
    }


@pytest.fixture
async def test_project(db_session: AsyncSession) -> Project:
    """创建测试项目"""
    project = Project(
        title="身份系统测试项目",
        genre="玄幻",
        theme="多重身份",
        narrative_perspective="第三人称"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def test_character(db_session: AsyncSession, test_project: Project) -> Character:
    """创建测试角色"""
    character = Character(
        project_id=test_project.id,
        name="主角张三",
        age=25,
        gender="男",
        role_type="protagonist",
        personality="表面温和，实则深沉",
        background="隐藏实力的修仙天才"
    )
    db_session.add(character)
    await db_session.commit()
    await db_session.refresh(character)
    return character


@pytest.fixture
async def test_career(db_session: AsyncSession, test_project: Project) -> Career:
    """创建测试职业"""
    import json

    career = Career(
        project_id=test_project.id,
        name="剑修",
        type="main",
        max_stage=10,
        stages=json.dumps([
            {"level": 1, "name": "炼气期", "description": "初入修仙"},
            {"level": 2, "name": "筑基期", "description": "筑基成功"},
            {"level": 3, "name": "金丹期", "description": "结成金丹"},
        ])
    )
    db_session.add(career)
    await db_session.commit()
    await db_session.refresh(career)
    return career


@pytest.fixture
async def test_identity(
    db_session: AsyncSession,
    test_project: Project,
    test_character: Character
) -> Identity:
    """创建测试身份"""
    identity = Identity(
        project_id=test_project.id,
        character_id=test_character.id,
        name="隐藏剑修",
        identity_type="secret",
        is_primary=False,
        personality="冷酷果断",
        background="暗中修炼的高手",
        status="active"
    )
    db_session.add(identity)
    await db_session.commit()
    await db_session.refresh(identity)
    return identity


@pytest.fixture
async def test_knower_character(db_session: AsyncSession, test_project: Project) -> Character:
    """创建测试认知者角色"""
    character = Character(
        project_id=test_project.id,
        name="李四",
        age=30,
        gender="男",
        role_type="supporting",
        personality="精明多疑",
        background="商会会长"
    )
    db_session.add(character)
    await db_session.commit()
    await db_session.refresh(character)
    return character
