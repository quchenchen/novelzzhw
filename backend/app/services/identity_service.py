"""身份系统业务逻辑服务"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete
from sqlalchemy.orm import selectinload
import json

from app.models.identity import Identity
from app.models.identity_career import IdentityCareer
from app.models.identity_knowledge import IdentityKnowledge
from app.models.character import Character
from app.models.career import Career
from app.schemas.identity import (
    IdentityCreate,
    IdentityUpdate,
    IdentityCareerCreate,
    IdentityCareerUpdate,
    IdentityKnowledgeCreate,
    IdentityKnowledgeUpdate
)
from app.logger import get_logger

logger = get_logger(__name__)


class IdentityService:
    """身份系统相关业务逻辑服务"""

    @staticmethod
    async def create_identity(
        project_id: str,
        identity_data: IdentityCreate,
        db: AsyncSession
    ) -> Identity:
        """
        创建新身份

        Args:
            project_id: 项目ID
            identity_data: 身份创建数据
            db: 数据库会话

        Returns:
            创建的身份对象

        Raises:
            ValueError: 角色不存在或数据验证失败
        """
        # 验证角色存在且属于该项目
        character_result = await db.execute(
            select(Character).where(
                Character.id == identity_data.character_id,
                Character.project_id == project_id
            )
        )
        character = character_result.scalar_one_or_none()
        if not character:
            raise ValueError(f"角色不存在或不属于该项目: {identity_data.character_id}")

        # 如果设置为主身份，先将该角色的其他主身份取消
        if identity_data.is_primary:
            await db.execute(
                select(Identity).where(
                    Identity.character_id == identity_data.character_id,
                    Identity.is_primary == True
                )
            )
            # 查询现有主身份
            existing_primary_result = await db.execute(
                select(Identity).where(
                    Identity.character_id == identity_data.character_id,
                    Identity.is_primary == True
                )
            )
            existing_primary = existing_primary_result.scalars().all()
            for identity in existing_primary:
                identity.is_primary = False
                logger.info(f"取消原主身份: {identity.name}")

        # 创建新身份
        identity = Identity(
            project_id=project_id,
            character_id=identity_data.character_id,
            name=identity_data.name,
            identity_type=identity_data.identity_type,
            is_primary=identity_data.is_primary,
            appearance=identity_data.appearance,
            personality=identity_data.personality,
            background=identity_data.background,
            voice_style=identity_data.voice_style,
            status=identity_data.status
        )
        db.add(identity)
        await db.flush()

        logger.info(f"创建身份成功: {identity.name} (ID: {identity.id}, 角色: {character.name})")
        return identity

    @staticmethod
    async def get_identity(
        identity_id: str,
        db: AsyncSession
    ) -> Optional[Identity]:
        """
        获取身份详情

        Args:
            identity_id: 身份ID
            db: 数据库会话

        Returns:
            身份对象，不存在则返回None
        """
        result = await db.execute(
            select(Identity).where(Identity.id == identity_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_identity_with_relations(
        identity_id: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        获取身份详情（包含职业和认知关系）

        Args:
            identity_id: 身份ID
            db: 数据库会话

        Returns:
            包含身份、职业列表、认知关系列表的字典
        """
        # 获取身份基础信息
        identity = await IdentityService.get_identity(identity_id, db)
        if not identity:
            return None

        # 获取职业关联
        careers_result = await db.execute(
            select(IdentityCareer).where(IdentityCareer.identity_id == identity_id)
        )
        identity_careers = careers_result.scalars().all()

        # 获取认知关系
        knowledge_result = await db.execute(
            select(IdentityKnowledge).where(IdentityKnowledge.identity_id == identity_id)
        )
        identity_knowledge = knowledge_result.scalars().all()

        return {
            "identity": identity,
            "careers": identity_careers,
            "knowledge": identity_knowledge
        }

    @staticmethod
    async def update_identity(
        identity_id: str,
        identity_update: IdentityUpdate,
        db: AsyncSession
    ) -> Optional[Identity]:
        """
        更新身份信息

        Args:
            identity_id: 身份ID
            identity_update: 更新数据
            db: 数据库会话

        Returns:
            更新后的身份对象，不存在则返回None
        """
        identity = await IdentityService.get_identity(identity_id, db)
        if not identity:
            return None

        update_data = identity_update.model_dump(exclude_unset=True)

        # 如果设置为主身份，先将该角色的其他主身份取消
        if update_data.get('is_primary') is True:
            existing_primary_result = await db.execute(
                select(Identity).where(
                    Identity.character_id == identity.character_id,
                    Identity.is_primary == True,
                    Identity.id != identity_id
                )
            )
            existing_primary = existing_primary_result.scalars().all()
            for existing_identity in existing_primary:
                existing_identity.is_primary = False
                logger.info(f"取消原主身份: {existing_identity.name}")

        # 更新字段
        for field, value in update_data.items():
            setattr(identity, field, value)

        await db.flush()
        logger.info(f"更新身份成功: {identity.name} (ID: {identity_id})")
        return identity

    @staticmethod
    async def delete_identity(
        identity_id: str,
        db: AsyncSession
    ) -> bool:
        """
        删除身份（级联删除职业关联和认知关系）

        Args:
            identity_id: 身份ID
            db: 数据库会话

        Returns:
            是否删除成功
        """
        identity = await IdentityService.get_identity(identity_id, db)
        if not identity:
            return False

        # 删除职业关联
        await db.execute(
            delete(IdentityCareer).where(IdentityCareer.identity_id == identity_id)
        )

        # 删除认知关系
        await db.execute(
            delete(IdentityKnowledge).where(IdentityKnowledge.identity_id == identity_id)
        )

        # 删除身份
        await db.execute(
            delete(Identity).where(Identity.id == identity_id)
        )

        logger.info(f"删除身份成功: {identity.name} (ID: {identity_id})")
        return True

    @staticmethod
    async def get_identities_by_project(
        project_id: str,
        db: AsyncSession,
        identity_type: Optional[str] = None,
        character_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Identity]:
        """
        获取项目的所有身份

        Args:
            project_id: 项目ID
            db: 数据库会话
            identity_type: 筛选身份类型
            character_id: 筛选角色ID
            status: 筛选状态

        Returns:
            身份列表
        """
        query = select(Identity).where(Identity.project_id == project_id)

        if identity_type:
            query = query.where(Identity.identity_type == identity_type)
        if character_id:
            query = query.where(Identity.character_id == character_id)
        if status:
            query = query.where(Identity.status == status)

        query = query.order_by(Identity.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_identities_by_character(
        character_id: str,
        db: AsyncSession
    ) -> List[Identity]:
        """
        获取角色的所有身份

        Args:
            character_id: 角色ID
            db: 数据库会话

        Returns:
            身份列表
        """
        result = await db.execute(
            select(Identity)
            .where(Identity.character_id == character_id)
            .order_by(Identity.is_primary.desc(), Identity.created_at.asc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_primary_identity(
        character_id: str,
        db: AsyncSession
    ) -> Optional[Identity]:
        """
        获取角色的主身份

        Args:
            character_id: 角色ID
            db: 数据库会话

        Returns:
            主身份对象，不存在则返回None
        """
        result = await db.execute(
            select(Identity).where(
                Identity.character_id == character_id,
                Identity.is_primary == True
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def add_identity_career(
        identity_id: str,
        career_data: IdentityCareerCreate,
        project_id: str,
        db: AsyncSession
    ) -> IdentityCareer:
        """
        为身份添加职业关联

        Args:
            identity_id: 身份ID
            career_data: 职业关联数据
            project_id: 项目ID（用于验证职业存在）
            db: 数据库会话

        Returns:
            创建的职业关联对象

        Raises:
            ValueError: 身份或职业不存在，或关联已存在
        """
        # 验证身份存在
        identity = await IdentityService.get_identity(identity_id, db)
        if not identity:
            raise ValueError(f"身份不存在: {identity_id}")

        # 验证职业存在且属于该项目
        career_result = await db.execute(
            select(Career).where(
                Career.id == career_data.career_id,
                Career.project_id == project_id
            )
        )
        career = career_result.scalar_one_or_none()
        if not career:
            raise ValueError(f"职业不存在或不属于该项目: {career_data.career_id}")

        # 验证职业类型匹配
        if career.type != career_data.career_type:
            raise ValueError(f"职业类型不匹配: 期望 {career.type}, 实际 {career_data.career_type}")

        # 检查是否已存在相同关联
        existing_result = await db.execute(
            select(IdentityCareer).where(
                IdentityCareer.identity_id == identity_id,
                IdentityCareer.career_id == career_data.career_id
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            raise ValueError(f"该身份已关联此职业: {career.name}")

        # 创建关联
        identity_career = IdentityCareer(
            identity_id=identity_id,
            career_id=career_data.career_id,
            career_type=career_data.career_type,
            current_stage=career_data.current_stage,
            stage_progress=career_data.stage_progress,
            started_at=career_data.started_at,
            reached_current_stage_at=career_data.reached_current_stage_at
        )
        db.add(identity_career)
        await db.flush()

        logger.info(f"为身份添加职业成功: {identity.name} -> {career.name}")
        return identity_career

    @staticmethod
    async def update_identity_career(
        identity_id: str,
        career_id: str,
        career_update: IdentityCareerUpdate,
        db: AsyncSession
    ) -> Optional[IdentityCareer]:
        """
        更新身份职业关联

        Args:
            identity_id: 身份ID
            career_id: 职业ID
            career_update: 更新数据
            db: 数据库会话

        Returns:
            更新后的职业关联对象，不存在则返回None
        """
        result = await db.execute(
            select(IdentityCareer).where(
                IdentityCareer.identity_id == identity_id,
                IdentityCareer.career_id == career_id
            )
        )
        identity_career = result.scalar_one_or_none()
        if not identity_career:
            return None

        update_data = career_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(identity_career, field, value)

        await db.flush()
        logger.info(f"更新身份职业关联成功: identity_id={identity_id}, career_id={career_id}")
        return identity_career

    @staticmethod
    async def delete_identity_career(
        identity_id: str,
        career_id: str,
        db: AsyncSession
    ) -> bool:
        """
        删除身份职业关联

        Args:
            identity_id: 身份ID
            career_id: 职业ID
            db: 数据库会话

        Returns:
            是否删除成功
        """
        result = await db.execute(
            select(IdentityCareer).where(
                IdentityCareer.identity_id == identity_id,
                IdentityCareer.career_id == career_id
            )
        )
        identity_career = result.scalar_one_or_none()
        if not identity_career:
            return False

        await db.execute(
            delete(IdentityCareer).where(
                IdentityCareer.identity_id == identity_id,
                IdentityCareer.career_id == career_id
            )
        )

        logger.info(f"删除身份职业关联成功: identity_id={identity_id}, career_id={career_id}")
        return True

    @staticmethod
    async def get_identity_careers(
        identity_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        获取身份的所有职业（含职业详情）

        Args:
            identity_id: 身份ID
            db: 数据库会话

        Returns:
            职业详情列表
        """
        # 获取职业关联
        result = await db.execute(
            select(IdentityCareer).where(IdentityCareer.identity_id == identity_id)
        )
        identity_careers = result.scalars().all()

        # 获取职业详情
        careers_detail = []
        for ic in identity_careers:
            career_result = await db.execute(
                select(Career).where(Career.id == ic.career_id)
            )
            career = career_result.scalar_one_or_none()
            if career:
                # 解析阶段信息
                stage_name = None
                stage_description = None
                if career.stages:
                    try:
                        stages = json.loads(career.stages)
                        for stage in stages:
                            if stage.get('level') == ic.current_stage:
                                stage_name = stage.get('name')
                                stage_description = stage.get('description')
                                break
                    except:
                        pass

                careers_detail.append({
                    "id": ic.id,
                    "identity_id": ic.identity_id,
                    "career_id": ic.career_id,
                    "career_name": career.name,
                    "career_type": ic.career_type,
                    "current_stage": ic.current_stage,
                    "stage_name": stage_name,
                    "stage_description": stage_description,
                    "stage_progress": ic.stage_progress,
                    "max_stage": career.max_stage,
                    "started_at": ic.started_at,
                    "reached_current_stage_at": ic.reached_current_stage_at,
                    "created_at": ic.created_at,
                    "updated_at": ic.updated_at
                })

        return careers_detail

    @staticmethod
    async def add_knowledge(
        identity_id: str,
        knowledge_data: IdentityKnowledgeCreate,
        project_id: str,
        db: AsyncSession
    ) -> IdentityKnowledge:
        """
        添加身份认知关系

        Args:
            identity_id: 身份ID
            knowledge_data: 认知关系数据
            project_id: 项目ID（用于验证角色存在）
            db: 数据库会话

        Returns:
            创建的认知关系对象

        Raises:
            ValueError: 身份或认知者不存在，或认知关系已存在
        """
        # 验证身份存在
        identity = await IdentityService.get_identity(identity_id, db)
        if not identity:
            raise ValueError(f"身份不存在: {identity_id}")

        # 验证认知者角色存在且属于该项目
        knower_result = await db.execute(
            select(Character).where(
                Character.id == knowledge_data.knower_character_id,
                Character.project_id == project_id
            )
        )
        knower = knower_result.scalar_one_or_none()
        if not knower:
            raise ValueError(f"认知者角色不存在或不属于该项目: {knowledge_data.knower_character_id}")

        # 检查是否已存在相同认知关系
        existing_result = await db.execute(
            select(IdentityKnowledge).where(
                IdentityKnowledge.identity_id == identity_id,
                IdentityKnowledge.knower_character_id == knowledge_data.knower_character_id
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            raise ValueError(f"该角色已有此身份的认知记录")

        # 创建认知关系
        knowledge = IdentityKnowledge(
            identity_id=identity_id,
            knower_character_id=knowledge_data.knower_character_id,
            knowledge_level=knowledge_data.knowledge_level,
            since_when=knowledge_data.since_when,
            discovered_how=knowledge_data.discovered_how,
            is_secret=knowledge_data.is_secret
        )
        db.add(knowledge)
        await db.flush()

        logger.info(f"添加认知关系成功: {knower.name} -> {identity.name} ({knowledge_data.knowledge_level})")
        return knowledge

    @staticmethod
    async def update_knowledge(
        identity_id: str,
        knowledge_id: str,
        knowledge_update: IdentityKnowledgeUpdate,
        db: AsyncSession
    ) -> Optional[IdentityKnowledge]:
        """
        更新身份认知关系

        Args:
            identity_id: 身份ID
            knowledge_id: 认知关系ID
            knowledge_update: 更新数据
            db: 数据库会话

        Returns:
            更新后的认知关系对象，不存在则返回None
        """
        result = await db.execute(
            select(IdentityKnowledge).where(
                IdentityKnowledge.id == knowledge_id,
                IdentityKnowledge.identity_id == identity_id
            )
        )
        knowledge = result.scalar_one_or_none()
        if not knowledge:
            return None

        update_data = knowledge_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(knowledge, field, value)

        await db.flush()
        logger.info(f"更新认知关系成功: knowledge_id={knowledge_id}")
        return knowledge

    @staticmethod
    async def delete_knowledge(
        identity_id: str,
        knowledge_id: str,
        db: AsyncSession
    ) -> bool:
        """
        删除身份认知关系

        Args:
            identity_id: 身份ID
            knowledge_id: 认知关系ID
            db: 数据库会话

        Returns:
            是否删除成功
        """
        result = await db.execute(
            select(IdentityKnowledge).where(
                IdentityKnowledge.id == knowledge_id,
                IdentityKnowledge.identity_id == identity_id
            )
        )
        knowledge = result.scalar_one_or_none()
        if not knowledge:
            return False

        await db.execute(
            delete(IdentityKnowledge).where(
                IdentityKnowledge.id == knowledge_id,
                IdentityKnowledge.identity_id == identity_id
            )
        )

        logger.info(f"删除认知关系成功: knowledge_id={knowledge_id}")
        return True

    @staticmethod
    async def get_identity_knowledge(
        identity_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        获取身份的所有认知关系（含认知者信息）

        Args:
            identity_id: 身份ID
            db: 数据库会话

        Returns:
            认知关系列表（含认知者名称）
        """
        # 获取认知关系
        result = await db.execute(
            select(IdentityKnowledge).where(IdentityKnowledge.identity_id == identity_id)
        )
        knowledge_list = result.scalars().all()

        # 获取认知者信息
        knowledge_with_knower = []
        for knowledge in knowledge_list:
            knower_result = await db.execute(
                select(Character).where(Character.id == knowledge.knower_character_id)
            )
            knower = knower_result.scalar_one_or_none()
            if knower:
                knowledge_with_knower.append({
                    "id": knowledge.id,
                    "identity_id": knowledge.identity_id,
                    "knower_character_id": knowledge.knower_character_id,
                    "knower_name": knower.name,
                    "knowledge_level": knowledge.knowledge_level,
                    "since_when": knowledge.since_when,
                    "discovered_how": knowledge.discovered_how,
                    "is_secret": knowledge.is_secret,
                    "created_at": knowledge.created_at
                })

        return knowledge_with_knower

    @staticmethod
    async def get_who_knows_identity(
        identity_id: str,
        db: AsyncSession,
        knowledge_level: Optional[str] = None
    ) -> List[Character]:
        """
        获取知道该身份的所有角色

        Args:
            identity_id: 身份ID
            db: 数据库会话
            knowledge_level: 筛选认知程度

        Returns:
            知道该身份的角色列表
        """
        query = select(IdentityKnowledge).where(IdentityKnowledge.identity_id == identity_id)
        if knowledge_level:
            query = query.where(IdentityKnowledge.knowledge_level == knowledge_level)

        result = await db.execute(query)
        knowledge_list = result.scalars().all()

        # 获取角色信息
        character_ids = [k.knower_character_id for k in knowledge_list]
        if not character_ids:
            return []

        characters_result = await db.execute(
            select(Character).where(Character.id.in_(character_ids))
        )
        return characters_result.scalars().all()


# 创建全局服务实例
identity_service = IdentityService()
