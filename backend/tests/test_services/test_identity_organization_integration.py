"""
测试分身系统与组织系统深度集成

模拟类似"伪装者"中明楼的双面间谍场景：
- 表面身份：汪伪政府经济顾问
- 秘密身份1：军统特工"毒蛇"
- 秘密身份2：中共地下党"黎明"
"""
import pytest
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.character import Character
from app.models.identity import Identity
from app.models.relationship import Organization, OrganizationMember
from app.models.identity_knowledge import IdentityKnowledge
from app.models.memory import StoryMemory
from app.services.identity_exposure_service import identity_exposure_service


@pytest.mark.asyncio
async def test_minglou_spy_scenario(db_session: AsyncSession):
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

    # ============ 1. 创建测试项目 ============
    project = Project(
        title="伪装者-明楼测试项目",
        genre="谍战",
        theme="双重潜伏",
        narrative_perspective="第三人称",
        world_time_period="1940年代",
        world_location="上海"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

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
    db_session.add(minglou)
    await db_session.commit()
    await db_session.refresh(minglou)

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
    db_session.add(public_identity)

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
    db_session.add(viper_identity)

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
    db_session.add(dawn_identity)

    await db_session.commit()
    await db_session.refresh(public_identity)
    await db_session.refresh(viper_identity)
    await db_session.refresh(dawn_identity)

    print(f"✅ 身份创建成功:")
    print(f"   - 公开身份: {public_identity.name} ({public_identity.identity_type})")
    print(f"   - 秘密身份1: {viper_identity.name} ({viper_identity.identity_type})")
    print(f"   - 秘密身份2: {dawn_identity.name} ({dawn_identity.identity_type})")

    # ============ 4. 创建三个组织 ============

    # 组织1：汪伪政府经济部（公开身份加入）
    puppet_org_char = Character(
        project_id=project.id,
        name="汪伪政府经济部",
        is_organization=True,
        organization_type="政府机构",
        organization_purpose="管理汪伪政府经济事务"
    )
    db_session.add(puppet_org_char)
    await db_session.flush()

    puppet_org = Organization(
        character_id=puppet_org_char.id,
        project_id=project.id,
        member_count=0,
        power_level=80,
        location="上海",
        motto="曲线救国"
    )
    db_session.add(puppet_org)

    # 组织2：军统上海站（毒蛇身份加入）
    military_org_char = Character(
        project_id=project.id,
        name="军统上海站",
        is_organization=True,
        organization_type="情报机构",
        organization_purpose="收集日军情报，进行暗杀破坏"
    )
    db_session.add(military_org_char)
    await db_session.flush()

    military_org = Organization(
        character_id=military_org_char.id,
        project_id=project.id,
        member_count=0,
        power_level=70,
        location="上海（地下）",
        motto="抗日救国"
    )
    db_session.add(military_org)

    # 组织3：中共地下党上海联络站（黎明身份加入）
    communist_org_char = Character(
        project_id=project.id,
        name="中共地下党上海联络站",
        is_organization=True,
        organization_type="地下组织",
        organization_purpose="宣传抗日思想，组织工人运动"
    )
    db_session.add(communist_org_char)
    await db_session.flush()

    communist_org = Organization(
        character_id=communist_org_char.id,
        project_id=project.id,
        member_count=0,
        power_level=60,
        location="上海（秘密据点）",
        motto="为人民服务"
    )
    db_session.add(communist_org)

    await db_session.commit()
    await db_session.refresh(puppet_org)
    await db_session.refresh(military_org)
    await db_session.refresh(communist_org)

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
    db_session.add(puppet_member)

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
    db_session.add(military_member)

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
    db_session.add(communist_member)

    await db_session.commit()

    print(f"\n✅ 成员关系创建成功:")
    print(f"   - 明楼（公开身份）→ {puppet_org_char.name}")
    print(f"   - 毒蛇（秘密身份）→ {military_org_char.name}")
    print(f"   - 黎明（秘密身份）→ {communist_org_char.name}")

    # ============ 6. 验证成员关系 ============

    # 验证：同一角色的不同身份可以在不同组织中
    puppet_members_result = await db_session.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == puppet_org.id
        )
    )
    puppet_members = puppet_members_result.scalars().all()

    assert len(puppet_members) == 1
    assert puppet_members[0].identity_id == public_identity.id
    print(f"\n✅ 验证通过：汪伪政府成员使用的是公开身份")

    # 验证：通过identity_id可以正确关联
    military_members_result = await db_session.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == military_org.id
        )
    )
    military_members = military_members_result.scalars().all()

    assert len(military_members) == 1
    assert military_members[0].identity_id == viper_identity.id
    print(f"✅ 验证通过：军统成员使用的是毒蛇身份")

    communist_members_result = await db_session.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == communist_org.id
        )
    )
    communist_members = communist_members_result.scalars().all()

    assert len(communist_members) == 1
    assert communist_members[0].identity_id == dawn_identity.id
    print(f"✅ 验证通过：中共地下党成员使用的是黎明身份")

    # ============ 7. 测试身份暴露场景 ============

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
    db_session.add(witness_char)
    await db_session.commit()
    await db_session.refresh(witness_char)

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
    result = await identity_exposure_service.process_identity_exposure(
        exposure_event=exposure_event,
        chapter_number=5,
        chapter_id="test-chapter-5",
        project_id=project.id,
        db=db_session
    )

    await db_session.commit()

    print(f"\n✅ 身份暴露处理完成:")
    print(f"   - 身份状态已更新: {result['identity_updated']}")
    print(f"   - 认知关系创建数: {result['knowledge_created']}")

    # 验证：毒蛇身份状态变为burned
    await db_session.refresh(viper_identity)
    assert viper_identity.status == "burned"
    print(f"✅ 验证通过：毒蛇身份状态已更新为 burned")

    # 验证：汪曼春知道了毒蛇身份
    knowledge_result = await db_session.execute(
        select(IdentityKnowledge).where(
            IdentityKnowledge.identity_id == viper_identity.id,
            IdentityKnowledge.knower_character_id == witness_char.id
        )
    )
    knowledge = knowledge_result.scalar_one_or_none()
    assert knowledge is not None
    assert knowledge.knowledge_level == "full"
    assert knowledge.is_secret == False
    print(f"✅ 验证通过：汪曼春已知晓毒蛇身份")

    # 验证：记忆系统记录了暴露事件
    memory_result = await db_session.execute(
        select(StoryMemory).where(
            StoryMemory.memory_type == "identity_exposure",
            StoryMemory.chapter_id == "test-chapter-5"
        )
    )
    memory = memory_result.scalar_one_or_none()
    assert memory is not None
    assert "毒蛇" in memory.content
    print(f"✅ 验证通过：记忆系统已记录暴露事件")

    # ============ 8. 验证其他身份未受影响 ============
    await db_session.refresh(public_identity)
    await db_session.refresh(dawn_identity)

    assert public_identity.status == "active"
    assert dawn_identity.status == "active"
    print(f"✅ 验证通过：其他秘密身份（黎明）未受影响")

    print("\n" + "="*50)
    print("🎉 所有测试通过！分身系统与组织系统集成正常")
    print("="*50)


@pytest.mark.asyncio
async def test_identity_query_by_organization(db_session: AsyncSession):
    """测试查询组织成员时能正确显示身份信息"""

    # 创建测试项目
    project = Project(
        title="组织成员查询测试",
        genre="玄幻",
        theme="多重身份"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # 创建角色
    character = Character(
        project_id=project.id,
        name="张三",
        role_type="protagonist"
    )
    db_session.add(character)
    await db_session.commit()
    await db_session.refresh(character)

    # 创建两个身份
    public_id = Identity(
        project_id=project.id,
        character_id=character.id,
        name="张三",
        identity_type="public",
        is_primary=True,
        status="active"
    )
    secret_id = Identity(
        project_id=project.id,
        character_id=character.id,
        name="暗夜",
        identity_type="secret",
        is_primary=False,
        status="active"
    )
    db_session.add_all([public_id, secret_id])
    await db_session.commit()
    await db_session.refresh(public_id)
    await db_session.refresh(secret_id)

    # 创建组织
    org_char = Character(
        project_id=project.id,
        name="天剑门",
        is_organization=True
    )
    db_session.add(org_char)
    await db_session.flush()

    org = Organization(
        character_id=org_char.id,
        project_id=project.id,
        member_count=0
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    # 添加成员（使用秘密身份）
    member = OrganizationMember(
        organization_id=org.id,
        character_id=character.id,
        identity_id=secret_id.id,  # 使用秘密身份
        position="外门弟子"
    )
    db_session.add(member)
    await db_session.commit()

    # 查询验证
    result = await db_session.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org.id
        )
    )
    members = result.scalars().all()

    assert len(members) == 1
    assert members[0].identity_id == secret_id.id
    print("✅ 组织成员身份关联查询正确")


@pytest.mark.asyncio
async def test_same_character_different_identities_different_orgs(
    db_session: AsyncSession
):
    """测试同一角色的不同身份可以加入不同组织"""

    # 创建测试项目
    project = Project(title="多重身份组织测试", genre="武侠")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # 创建角色
    character = Character(
        project_id=project.id,
        name="李四",
        role_type="protagonist"
    )
    db_session.add(character)
    await db_session.commit()
    await db_session.refresh(character)

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
    db_session.add_all([identity1, identity2])
    await db_session.commit()
    await db_session.refresh(identity1)
    await db_session.refresh(identity2)

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
    db_session.add_all([org1_char, org2_char])
    await db_session.flush()

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
    db_session.add_all([org1, org2])
    await db_session.commit()
    await db_session.refresh(org1)
    await db_session.refresh(org2)

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
    db_session.add_all([member1, member2])
    await db_session.commit()

    # 验证：两个成员关系都存在且关联不同身份
    result1 = await db_session.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org1.id
        )
    )
    members1 = result1.scalars().all()

    result2 = await db_session.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org2.id
        )
    )
    members2 = result2.scalars().all()

    assert len(members1) == 1
    assert len(members2) == 1
    assert members1[0].identity_id == identity1.id
    assert members2[0].identity_id == identity2.id
    assert members1[0].character_id == members2[0].character_id  # 同一角色

    print("✅ 同一角色的不同身份成功加入不同组织")


if __name__ == "__main__":
    # 直接运行此文件进行测试
    import sys
    sys.path.insert(0, "/Users/quchenchen/Documents/github/MuMu/backend")

    import asyncio
    from app.database import get_db_session_factory

    async def main():
        """使用真实数据库进行测试"""
        from sqlalchemy.ext.asyncio import AsyncSession

        # 获取数据库会话
        session_factory = get_db_session_factory()
        async with session_factory() as db:
            # 运行测试
            await test_minglou_spy_scenario(db)
            await test_identity_query_by_organization(db)
            await test_same_character_different_identities_different_orgs(db)

    asyncio.run(main())
