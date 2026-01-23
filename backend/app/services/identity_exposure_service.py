"""身份暴露处理服务

当章节分析识别到身份暴露事件时，自动处理以下操作：
1. 更新身份状态为 burned
2. 更新 IdentityKnowledge（添加新的知晓者）
3. 处理组织成员关系变化
4. 记录暴露事件到记忆系统
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.identity import Identity
from app.models.identity_knowledge import IdentityKnowledge
from app.models.relationship import OrganizationMember, Organization
from app.models.memory import StoryMemory
from app.models.character import Character
from app.logger import get_logger

logger = get_logger(__name__)


class IdentityExposureService:
    """身份暴露处理服务"""

    def __init__(self):
        self.logger = logger

    async def process_identity_exposure(
        self,
        exposure_event: Dict[str, Any],
        chapter_number: int,
        chapter_id: str,
        project_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        处理身份暴露事件，自动更新相关系统

        处理流程：
        1. 查找被暴露的身份
        2. 更新身份状态为 burned
        3. 更新 IdentityKnowledge（添加新的知晓者）
        4. 处理组织成员关系变化
        5. 记录暴露事件到记忆系统

        Args:
            exposure_event: 身份暴露事件数据
            chapter_number: 章节号
            chapter_id: 章节ID
            project_id: 项目ID
            db: 数据库会话

        Returns:
            处理结果字典
        """
        character_name = exposure_event.get("character_name")
        exposed_identity_name = exposure_event.get("exposed_identity_name")
        exposure_type = exposure_event.get("exposure_type", "secret_revealed")
        exposure_context = exposure_event.get("exposure_context", "")
        witnesses = exposure_event.get("witnesses", [])
        impact_on_organization = exposure_event.get("impact_on_organization", "")

        self.logger.info(f"🎭 处理身份暴露事件：{character_name} 的身份 {exposed_identity_name} 被暴露")

        result = {
            "character_name": character_name,
            "exposed_identity_name": exposed_identity_name,
            "identity_updated": False,
            "knowledge_created": 0,
            "organizations_affected": []
        }

        # 1. 查找角色
        character_result = await db.execute(
            select(Character).where(
                Character.project_id == project_id,
                Character.name == character_name
            )
        )
        character = character_result.scalar_one_or_none()
        if not character:
            self.logger.warning(f"⚠️ 未找到角色：{character_name}")
            return result

        # 2. 查找被暴露的身份
        identity_result = await db.execute(
            select(Identity).where(
                Identity.character_id == character.id,
                Identity.name == exposed_identity_name
            )
        )
        identity = identity_result.scalar_one_or_none()
        if not identity:
            self.logger.warning(f"⚠️ 未找到身份：{exposed_identity_name}")
            return result

        # 3. 更新身份状态为 burned，并记录暴露章节号
        if identity.status != "burned":
            identity.status = "burned"
            # 记录暴露时的章节号（只记录第一次暴露）
            if identity.exposed_at_chapter is None:
                identity.exposed_at_chapter = chapter_number
            result["identity_updated"] = True
            self.logger.info(f"✅ 身份状态已更新为 burned（暴露于第{chapter_number}章）：{identity.name}")

        # 4. 处理目击者的认知关系
        for witness_name in witnesses:
            witness_result = await db.execute(
                select(Character).where(
                    Character.project_id == project_id,
                    Character.name == witness_name
                )
            )
            witness = witness_result.scalar_one_or_none()
            if witness:
                # 检查是否已存在认知关系
                existing_knowledge = await db.execute(
                    select(IdentityKnowledge).where(
                        IdentityKnowledge.identity_id == identity.id,
                        IdentityKnowledge.knower_character_id == witness.id
                    )
                )
                knowledge = existing_knowledge.scalar_one_or_none()

                if not knowledge:
                    # 创建新的认知关系
                    knowledge = IdentityKnowledge(
                        identity_id=identity.id,
                        knower_character_id=witness.id,
                        knowledge_level="full" if exposure_type == "secret_revealed" else "partial",
                        since_when=f"第{chapter_number}章",
                        discovered_how=exposure_context,
                        is_secret=False  # 身份已暴露，不再是秘密
                    )
                    db.add(knowledge)
                    result["knowledge_created"] += 1
                    self.logger.info(f"  ✅ 创建认知关系：{witness.name} 知晓 {identity.name}")
                else:
                    # 更新现有认知关系
                    knowledge.knowledge_level = "full"
                    knowledge.is_secret = False
                    knowledge.discovered_how = exposure_context
                    self.logger.info(f"  ℹ️ 更新认知关系：{witness.name} 已知晓 {identity.name}")

        # 5. 处理组织成员关系变化
        if exposure_type in ("secret_revealed", "disguise_broken"):
            # 查找该身份加入的组织
            member_result = await db.execute(
                select(OrganizationMember).where(
                    OrganizationMember.identity_id == identity.id
                )
            )
            memberships = member_result.scalars().all()

            for membership in memberships:
                org_result = await db.execute(
                    select(Organization).where(Organization.id == membership.organization_id)
                )
                org = org_result.scalar_one_or_none()

                if org:
                    # 根据暴露类型自动更新成员状态
                    old_status = membership.status
                    if exposure_type == "secret_revealed" and membership.status == "active":
                        # 秘密身份暴露，标记为可疑
                        membership.status = "suspected"
                        membership.notes = (membership.notes or "") + f"\n[系统] 身份暴露于第{chapter_number}章：{exposure_context}"
                        self.logger.info(f"  ✅ 组织成员状态更新: {old_status} -> suspected")
                    elif exposure_type == "disguise_broken":
                        # 伪装身份被识破，标记为被驱逐
                        membership.status = "expelled"
                        membership.notes = (membership.notes or "") + f"\n[系统] 伪装被识破于第{chapter_number}章：{exposure_context}"
                        self.logger.info(f"  ✅ 组织成员状态更新: {old_status} -> expelled")

                    result["organizations_affected"].append({
                        "organization_id": org.id,
                        "membership_id": membership.id,
                        "action": "成员状态已自动更新",
                        "old_status": old_status,
                        "new_status": membership.status,
                        "reason": f"身份已暴露于第{chapter_number}章：{exposure_context}"
                    })

        # 6. 记录暴露事件到记忆系统
        memory_content = (
            f"身份暴露事件：{character_name} 的身份「{exposed_identity_name}」"
            f"在第{chapter_number}章被暴露。"
        )
        if exposure_context:
            memory_content += f" 暴露场景：{exposure_context}。"
        if witnesses:
            memory_content += f" 目击者：{', '.join(witnesses)}。"
        if impact_on_organization:
            memory_content += f" 影响：{impact_on_organization}。"

        # 尝试记录到记忆系统，如果 chapter 不存在则跳过
        try:
            # 验证 chapter 是否存在
            from app.models.chapter import Chapter
            chapter_exists = await db.execute(
                select(Chapter).where(Chapter.id == chapter_id)
            )
            if chapter_exists.scalar_one_or_none():
                memory = StoryMemory(
                    project_id=project_id,
                    chapter_id=chapter_id,
                    memory_type="identity_exposure",
                    content=memory_content,
                    story_timeline=chapter_number,
                    importance_score=0.9,
                    metadata={
                        "character_name": character_name,
                        "identity_name": exposed_identity_name,
                        "exposure_type": exposure_type,
                        "witnesses": witnesses
                    }
                )
                db.add(memory)
                self.logger.info(f"  ✅ 记录身份暴露事件到记忆系统")
            else:
                self.logger.warning(f"  ⚠️ 章节 {chapter_id} 不存在，跳过记忆记录")
        except Exception as e:
            self.logger.warning(f"  ⚠️ 记录记忆失败（非致命错误）: {str(e)}")

        return result

    async def process_chapter_identity_exposures(
        self,
        analysis_result: Dict[str, Any],
        chapter_number: int,
        chapter_id: str,
        project_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        批量处理章节中的所有身份暴露事件

        Args:
            analysis_result: 章节分析结果
            chapter_number: 章节号
            chapter_id: 章节ID
            project_id: 项目ID
            db: 数据库会话

        Returns:
            处理结果列表
        """
        identity_exposures = analysis_result.get("identity_exposures", [])
        results = []

        if not identity_exposures:
            self.logger.info(f"第{chapter_number}章没有身份暴露事件")
            return results

        self.logger.info(f"🎭 第{chapter_number}章发现 {len(identity_exposures)} 个身份暴露事件")

        for exposure in identity_exposures:
            try:
                result = await self.process_identity_exposure(
                    exposure, chapter_number, chapter_id, project_id, db
                )
                results.append(result)
            except Exception as e:
                self.logger.error(f"处理身份暴露事件失败：{str(e)}")
                results.append({
                    "error": str(e),
                    "exposure": exposure
                })

        return results


# 创建全局实例
identity_exposure_service = IdentityExposureService()
