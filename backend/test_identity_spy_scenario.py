#!/usr/bin/env python3
"""
分身系统与组织系统深度集成测试 - 明楼双面间谍场景

这是一个独立的测试脚本，不需要导入 FastAPI app
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.project import Project
from app.models.character import Character
from app.models.identity import Identity
from app.models.relationship import Organization, OrganizationMember
from app.models.identity_knowledge import IdentityKnowledge
from app.models.memory import StoryMemory
from app.services.identity_exposure_service import IdentityExposureService


# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


async def get_test_db():
    """创建测试数据库"""
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

    return async_session_maker, engine


async def test_minglou_spy_scenario():
    """
    完整测试明楼式的双面间谍场景

    场景设定：
    1. 创建角色"明楼"
    2. 创建三个身份：
       - 公开身份：明楼（经济顾问）
       - 秘密身份：毒蛇（军统特工）
       - 秘密身份：黎明（中共地下党）
    3. 创建三个组织
    4. 不同身份加入不同组织
    5. 测试身份暴露后的状态变化
    """
    print("\n" + "="*60)
    print("🎭 分身系统与组织系统集成测试 - 明楼双面间谍场景")
    print("="*60)

    # 获取数据库会话
    session_maker, engine = await get_test_db()

    async with session_maker() as db:
        # ============ 1. 创建测试项目 ============
        project = Project(
            user_id="test_user_for_identity_system",  # 必需字段
            title="伪装者-明楼测试项目",
            genre="谍战",
            theme="双重潜伏",
            narrative_perspective="第三人称",
            world_time_period="1940年代",
            world_location="上海"
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)

        print(f"\n✅ 项目创建成功: {project.title} (ID: {project.id})")

        # ============ 2. 创建角色"明楼" ============
        minglou = Character(
            project_id=project.id,
            name="明楼",
            age=35,
            gender="男",
            role_type="protagonist",
            personality="心思缜密，城府极深",
            background="留洋归来的经济学博士",
            appearance="戴金丝眼镜，西装笔挺，儒雅斯文"
        )
        db.add(minglou)
        await db.commit()
        await db.refresh(minglou)

        print(f"✅ 角色创建成功: {minglou.name} (ID: {minglou.id})")

        # ============ 3. 创建三个身份 ============

        # 公开身份：明楼（经济顾问）
        public_identity = Identity(
            project_id=project.id,
            character_id=minglou.id,
            name="明楼",
            identity_type="public",
            is_primary=True,
            status="active",
            personality="儒雅温和的经济学家",
            background="汪伪政府经济司首席财经顾问",
            appearance="戴金丝眼镜，西装笔挺"
        )
        db.add(public_identity)

        # 秘密身份1：毒蛇（军统特工）
        viper_identity = Identity(
            project_id=project.id,
            character_id=minglou.id,
            name="毒蛇",
            identity_type="secret",
            is_primary=False,
            status="active",
            personality="冷酷果断的特工",
            background="军统上海站核心特工，代号毒蛇",
            appearance="面具后的真面目"
        )
        db.add(viper_identity)

        # 秘密身份2：黎明（中共地下党）
        dawn_identity = Identity(
            project_id=project.id,
            character_id=minglou.id,
            name="黎明",
            identity_type="secret",
            is_primary=False,
            status="active",
            personality="坚定的共产主义者",
            background="中共地下党上海联络站核心成员，代号黎明",
            appearance="朴素低调"
        )
        db.add(dawn_identity)

        await db.commit()
        await db.refresh(public_identity)
        await db.refresh(viper_identity)
        await db.refresh(dawn_identity)

        print(f"\n✅ 身份创建成功:")
        print(f"   - 公开身份: {public_identity.name} ({public_identity.identity_type}) - ID: {public_identity.id}")
        print(f"   - 秘密身份1: {viper_identity.name} ({viper_identity.identity_type}) - ID: {viper_identity.id}")
        print(f"   - 秘密身份2: {dawn_identity.name} ({dawn_identity.identity_type}) - ID: {dawn_identity.id}")

        # ============ 4. 创建三个组织 ============

        # 组织1：汪伪政府经济部（公开身份加入）
        puppet_org_char = Character(
            project_id=project.id,
            name="汪伪政府经济部",
            is_organization=True,
            organization_type="政府机构",
            organization_purpose="管理汪伪政府经济事务"
        )
        db.add(puppet_org_char)
        await db.flush()

        puppet_org = Organization(
            character_id=puppet_org_char.id,
            project_id=project.id,
            member_count=0,
            power_level=80,
            location="上海",
            motto="曲线救国"
        )
        db.add(puppet_org)

        # 组织2：军统上海站（毒蛇身份加入）
        military_org_char = Character(
            project_id=project.id,
            name="军统上海站",
            is_organization=True,
            organization_type="情报机构",
            organization_purpose="收集日军情报，进行暗杀破坏"
        )
        db.add(military_org_char)
        await db.flush()

        military_org = Organization(
            character_id=military_org_char.id,
            project_id=project.id,
            member_count=0,
            power_level=70,
            location="上海（地下）",
            motto="抗日救国"
        )
        db.add(military_org)

        # 组织3：中共地下党上海联络站（黎明身份加入）
        communist_org_char = Character(
            project_id=project.id,
            name="中共地下党上海联络站",
            is_organization=True,
            organization_type="地下组织",
            organization_purpose="宣传抗日思想，组织工人运动"
        )
        db.add(communist_org_char)
        await db.flush()

        communist_org = Organization(
            character_id=communist_org_char.id,
            project_id=project.id,
            member_count=0,
            power_level=60,
            location="上海（秘密据点）",
            motto="为人民服务"
        )
        db.add(communist_org)

        await db.commit()
        await db.refresh(puppet_org)
        await db.refresh(military_org)
        await db.refresh(communist_org)

        print(f"\n✅ 组织创建成功:")
        print(f"   - {puppet_org_char.name} (ID: {puppet_org.id})")
        print(f"   - {military_org_char.name} (ID: {military_org.id})")
        print(f"   - {communist_org_char.name} (ID: {communist_org.id})")

        # ============ 5. 不同身份加入不同组织 ============

        # 公开身份"明楼"加入汪伪政府经济部
        puppet_member = OrganizationMember(
            organization_id=puppet_org.id,
            character_id=minglou.id,
            identity_id=public_identity.id,  # 关联公开身份
            position="首席财经顾问",
            rank=9,
            loyalty=50,  # 表面忠诚
            status="active",
            source="manual"
        )
        db.add(puppet_member)

        # 秘密身份"毒蛇"加入军统
        military_member = OrganizationMember(
            organization_id=military_org.id,
            character_id=minglou.id,
            identity_id=viper_identity.id,  # 关联毒蛇身份
            position="核心特工",
            rank=8,
            loyalty=90,
            status="active",
            source="manual"
        )
        db.add(military_member)

        # 秘密身份"黎明"加入中共地下党
        communist_member = OrganizationMember(
            organization_id=communist_org.id,
            character_id=minglou.id,
            identity_id=dawn_identity.id,  # 关联黎明身份
            position="联络员",
            rank=7,
            loyalty=100,
            status="active",
            source="manual"
        )
        db.add(communist_member)

        await db.commit()

        print(f"\n✅ 成员关系创建成功:")
        print(f"   - 明楼（公开身份 ID:{public_identity.id}）→ {puppet_org_char.name}")
        print(f"   - 毒蛇（秘密身份 ID:{viper_identity.id}）→ {military_org_char.name}")
        print(f"   - 黎明（秘密身份 ID:{dawn_identity.id}）→ {communist_org_char.name}")

        # ============ 6. 验证成员关系 ============

        # 验证：同一角色的不同身份可以在不同组织中
        puppet_members_result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == puppet_org.id
            )
        )
        puppet_members = puppet_members_result.scalars().all()

        assert len(puppet_members) == 1, f"Expected 1 member in puppet org, got {len(puppet_members)}"
        assert puppet_members[0].identity_id == public_identity.id, "Puppet org should use public identity"
        print(f"\n✅ 验证通过：汪伪政府成员使用的是公开身份 (identity_id={puppet_members[0].identity_id})")

        # 验证：通过identity_id可以正确关联
        military_members_result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == military_org.id
            )
        )
        military_members = military_members_result.scalars().all()

        assert len(military_members) == 1, f"Expected 1 member in military org, got {len(military_members)}"
        assert military_members[0].identity_id == viper_identity.id, "Military org should use viper identity"
        print(f"✅ 验证通过：军统成员使用的是毒蛇身份 (identity_id={military_members[0].identity_id})")

        communist_members_result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == communist_org.id
            )
        )
        communist_members = communist_members_result.scalars().all()

        assert len(communist_members) == 1, f"Expected 1 member in communist org, got {len(communist_members)}"
        assert communist_members[0].identity_id == dawn_identity.id, "Communist org should use dawn identity"
        print(f"✅ 验证通过：中共地下党成员使用的是黎明身份 (identity_id={communist_members[0].identity_id})")

        # ============ 7. 测试身份暴露场景 ============

        print("\n" + "-"*60)
        print("📢 开始测试身份暴露场景...")
        print("-"*60)

        # 创建目击者角色
        witness_char = Character(
            project_id=project.id,
            name="汪曼春",
            age=28,
            gender="女",
            role_type="supporting",
            personality="敏锐多疑",
            background="76号特务委员会主任"
        )
        db.add(witness_char)
        await db.commit()
        await db.refresh(witness_char)

        # 模拟身份暴露事件：毒蛇身份被汪曼春发现
        exposure_event = {
            "character_name": "明楼",
            "exposed_identity_name": "毒蛇",
            "exposure_type": "secret_revealed",
            "exposure_context": "在76号审讯室，明楼暴露出特工技能",
            "witnesses": ["汪曼春"],
            "impact_on_organization": "军统特工身份暴露，汪伪政府可能采取行动"
        }

        # 处理身份暴露
        exposure_service = IdentityExposureService()
        result = await exposure_service.process_identity_exposure(
            exposure_event=exposure_event,
            chapter_number=5,
            chapter_id="test-chapter-5",
            project_id=project.id,
            db=db
        )

        await db.commit()

        print(f"\n✅ 身份暴露处理完成:")
        print(f"   - 身份状态已更新: {result['identity_updated']}")
        print(f"   - 认知关系创建数: {result['knowledge_created']}")
        print(f"   - 受影响的组织: {len(result['organizations_affected'])}")

        # 验证：毒蛇身份状态变为burned
        await db.refresh(viper_identity)
        assert viper_identity.status == "burned", f"Viper identity should be burned, got {viper_identity.status}"
        print(f"\n✅ 验证通过：毒蛇身份状态已更新为 burned")

        # 验证：汪曼春知道了毒蛇身份
        knowledge_result = await db.execute(
            select(IdentityKnowledge).where(
                IdentityKnowledge.identity_id == viper_identity.id,
                IdentityKnowledge.knower_character_id == witness_char.id
            )
        )
        knowledge = knowledge_result.scalar_one_or_none()
        assert knowledge is not None, "Knowledge should be created"
        assert knowledge.knowledge_level == "full", f"Knowledge level should be full, got {knowledge.knowledge_level}"
        assert knowledge.is_secret == False, "Knowledge should not be secret after exposure"
        print(f"✅ 验证通过：汪曼春已知晓毒蛇身份 (knowledge_level={knowledge.knowledge_level})")

        # 验证：记忆系统记录了暴露事件
        memory_result = await db.execute(
            select(StoryMemory).where(
                StoryMemory.memory_type == "identity_exposure",
                StoryMemory.chapter_id == "test-chapter-5"
            )
        )
        memory = memory_result.scalar_one_or_none()
        assert memory is not None, "Memory should be created"
        assert "毒蛇" in memory.content, f"Memory should mention 毒蛇, got: {memory.content}"
        print(f"✅ 验证通过：记忆系统已记录暴露事件")
        print(f"   记忆内容: {memory.content[:100]}...")

        # ============ 8. 验证其他身份未受影响 ============
        await db.refresh(public_identity)
        await db.refresh(dawn_identity)

        assert public_identity.status == "active", f"Public identity should still be active, got {public_identity.status}"
        assert dawn_identity.status == "active", f"Dawn identity should still be active, got {dawn_identity.status}"
        print(f"\n✅ 验证通过：其他身份未受影响")
        print(f"   - 公开身份(明楼)状态: {public_identity.status}")
        print(f"   - 秘密身份(黎明)状态: {dawn_identity.status}")

    # 清理
    await engine.dispose()

    print("\n" + "="*60)
    print("🎉 所有测试通过！分身系统与组织系统集成正常")
    print("="*60)
    print("\n📋 测试总结:")
    print("  ✅ 同一角色的不同身份可以加入不同组织")
    print("  ✅ 组织成员通过 identity_id 正确关联身份")
    print("  ✅ 身份暴露自动更新身份状态为 burned")
    print("  ✅ 身份暴露自动创建认知关系 (IdentityKnowledge)")
    print("  ✅ 身份暴露自动记录到记忆系统")
    print("  ✅ 暴露一个身份不影响其他身份")
    print("="*60 + "\n")


async def test_same_character_different_orgs():
    """测试同一角色的不同身份加入不同组织"""
    print("\n" + "="*60)
    print("🔧 测试：同一角色的不同身份加入不同组织")
    print("="*60)

    session_maker, engine = await get_test_db()

    async with session_maker() as db:
        # 创建测试项目
        project = Project(title="多重身份组织测试", genre="武侠")
        db.add(project)
        await db.commit()
        await db.refresh(project)

        # 创建角色
        character = Character(
            project_id=project.id,
            name="李四",
            role_type="protagonist"
        )
        db.add(character)
        await db.commit()
        await db.refresh(character)

        # 创建两个身份
        identity1 = Identity(
            project_id=project.id,
            character_id=character.id,
            name="李四",
            identity_type="public",
            is_primary=True,
            status="active"
        )
        identity2 = Identity(
            project_id=project.id,
            character_id=character.id,
            name="黑衣客",
            identity_type="secret",
            is_primary=False,
            status="active"
        )
        db.add_all([identity1, identity2])
        await db.commit()
        await db.refresh(identity1)
        await db.refresh(identity2)

        # 创建两个组织
        org1_char = Character(
            project_id=project.id,
            name="正道联盟",
            is_organization=True
        )
        org2_char = Character(
            project_id=project.id,
            name="魔教",
            is_organization=True
        )
        db.add_all([org1_char, org2_char])
        await db.flush()

        org1 = Organization(
            character_id=org1_char.id,
            project_id=project.id,
            member_count=0
        )
        org2 = Organization(
            character_id=org2_char.id,
            project_id=project.id,
            member_count=0
        )
        db.add_all([org1, org2])
        await db.commit()
        await db.refresh(org1)
        await db.refresh(org2)

        # 同一角色的两个身份分别加入两个组织
        member1 = OrganizationMember(
            organization_id=org1.id,
            character_id=character.id,
            identity_id=identity1.id,  # 公开身份加入正道
            position="弟子"
        )
        member2 = OrganizationMember(
            organization_id=org2.id,
            character_id=character.id,
            identity_id=identity2.id,  # 秘密身份加入魔教
            position="长老"
        )
        db.add_all([member1, member2])
        await db.commit()

        # 验证
        result1 = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org1.id
            )
        )
        members1 = result1.scalars().all()

        result2 = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org2.id
            )
        )
        members2 = result2.scalars().all()

        assert len(members1) == 1 and len(members2) == 1
        assert members1[0].identity_id == identity1.id
        assert members2[0].identity_id == identity2.id
        assert members1[0].character_id == members2[0].character_id

        print(f"✅ 同一角色(ID:{character.id})的两个身份:")
        print(f"   - {identity1.name} (ID:{identity1.id}) → {org1_char.name}")
        print(f"   - {identity2.name} (ID:{identity2.id}) → {org2_char.name}")
        print("✅ 测试通过！")

    await engine.dispose()


async def main():
    """运行所有测试"""
    try:
        # 运行主测试
        await test_minglou_spy_scenario()

        # 运行附加测试
        await test_same_character_different_orgs()

        return 0
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
