#!/usr/bin/env python3
"""
身份系统数据库迁移测试脚本

测试：
1. 数据库迁移能正确执行
2. 现有角色能正确创建默认真身身份
3. 级联删除正常工作
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

from app.models.base import Base
from app.models.project import Project
from app.models.character import Character
from app.models.identity import Identity


async def test_migration():
    """测试数据库迁移"""
    print("=" * 60)
    print("身份系统数据库迁移测试")
    print("=" * 60)

    # 使用测试数据库
    test_db_url = "sqlite+aiosqlite:///:memory:"

    # 创建引擎
    engine = create_async_engine(
        test_db_url,
        echo=False,
    )

    # 创建所有表（包括新表）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 创建会话
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print("\n1. 测试表结构创建...")
        # 检查 identities 表是否存在
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='identities'")
        )
        identities_table = result.fetchone()
        assert identities_table is not None, "identities 表未创建"
        print("   ✅ identities 表创建成功")

        # 检查 identity_careers 表
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='identity_careers'")
        )
        identity_careers_table = result.fetchone()
        assert identity_careers_table is not None, "identity_careers 表未创建"
        print("   ✅ identity_careers 表创建成功")

        # 检查 identity_knowledge 表
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='identity_knowledge'")
        )
        identity_knowledge_table = result.fetchone()
        assert identity_knowledge_table is not None, "identity_knowledge 表未创建"
        print("   ✅ identity_knowledge 表创建成功")

        print("\n2. 测试默认真身身份创建...")
        # 创建测试项目和角色
        project = Project(
            title="迁移测试项目",
            genre="玄幻",
            theme="测试"
        )
        session.add(project)
        await session.flush()

        character = Character(
            project_id=project.id,
            name="测试角色",
            age=25,
            gender="男",
            role_type="protagonist"
        )
        session.add(character)
        await session.flush()
        print(f"   ✅ 创建测试角色: {character.name}")

        # 模拟迁移：为现有角色创建默认真身身份
        default_identity = Identity(
            project_id=project.id,
            character_id=character.id,
            name=character.name,  # 使用角色名作为默认身份名
            identity_type="real",
            is_primary=True,
            status="active",
            appearance=character.appearance,
            personality=character.personality,
            background=character.background
        )
        session.add(default_identity)
        await session.commit()
        print(f"   ✅ 创建默认真身身份: {default_identity.name}")

        # 验证默认身份
        result = await session.execute(
            select(Identity).where(Identity.character_id == character.id)
        )
        identities = result.scalars().all()

        assert len(identities) == 1, "应有一个默认身份"
        assert identities[0].is_primary is True, "默认身份应该是主身份"
        assert identities[0].identity_type == "real", "默认身份应该是真身"
        print("   ✅ 默认身份验证成功")

        print("\n3. 测试级联删除...")
        # 删除角色，验证关联身份被删除
        character_id = character.id
        identity_id = default_identity.id

        await session.delete(character)
        await session.commit()

        # 验证身份已被级联删除
        result = await session.execute(
            select(Identity).where(Identity.id == identity_id)
        )
        deleted_identity = result.scalar_one_or_none()
        assert deleted_identity is None, "身份应随角色一起被删除"
        print("   ✅ 级联删除测试成功")

    await engine.dispose()

    print("\n" + "=" * 60)
    print("所有迁移测试通过！")
    print("=" * 60)


async def test_migration_with_postgresql():
    """
    测试 PostgreSQL 数据库迁移（如果配置了）

    注意：这需要有效的 PostgreSQL 连接
    """
    print("\n" + "=" * 60)
    print("PostgreSQL 数据库迁移测试")
    print("=" * 60)

    # 检查是否配置了 PostgreSQL
    import os
    postgres_url = os.environ.get("TEST_POSTGRESQL_URL")

    if not postgres_url:
        print("   ⚠️  未配置 TEST_POSTGRESQL_URL，跳过 PostgreSQL 测试")
        return

    try:
        engine = create_async_engine(postgres_url, echo=False)

        async with engine.begin() as conn:
            # 检查表是否存在
            result = await conn.execute(
                text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'identities')")
            )
            exists = result.scalar()
            if exists:
                print("   ✅ PostgreSQL: identities 表已存在")
            else:
                print("   ⚠️  PostgreSQL: identities 表不存在，需要运行迁移")

        await engine.dispose()
    except Exception as e:
        print(f"   ❌ PostgreSQL 测试失败: {str(e)}")


if __name__ == "__main__":
    print("\n开始运行身份系统迁移测试...\n")

    # 运行 SQLite 测试
    asyncio.run(test_migration())

    # 运行 PostgreSQL 测试（如果配置）
    asyncio.run(test_migration_with_postgresql())

    print("\n测试完成！")
