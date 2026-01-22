"""身份系统API"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.database import get_db
from app.models.identity import Identity
from app.models.identity_career import IdentityCareer
from app.models.identity_knowledge import IdentityKnowledge
from app.models.character import Character
from app.models.career import Career
from app.schemas.identity import (
    IdentityCreate,
    IdentityUpdate,
    IdentityResponse,
    IdentityListResponse,
    IdentityDetailResponse,
    IdentityCareerCreate,
    IdentityCareerUpdate,
    IdentityCareerDetail,
    IdentityCareerResponse,
    IdentityKnowledgeCreate,
    IdentityKnowledgeUpdate,
    IdentityKnowledgeResponse,
    IdentityKnowledgeWithKnower
)
from app.services.identity_service import identity_service
from app.api.common import verify_project_access, get_user_id
from app.logger import get_logger

router = APIRouter(prefix="/identities", tags=["身份系统"])
logger = get_logger(__name__)


# ===== Identity CRUD =====

@router.get(
    "/project/{project_id}",
    response_model=IdentityListResponse,
    summary="获取项目的所有身份"
)
async def get_project_identities(
    project_id: str,
    request: Request,
    character_id: Optional[str] = None,
    identity_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定项目的所有身份

    支持筛选:
    - character_id: 筛选指定角色的身份
    - identity_type: 筛选身份类型 (real/public/secret/disguise)
    - status: 筛选状态 (active/inactive/burned)
    """
    user_id = get_user_id(request)
    await verify_project_access(project_id, user_id, db)

    identities = await identity_service.get_identities_by_project(
        project_id=project_id,
        db=db,
        identity_type=identity_type,
        character_id=character_id,
        status=status
    )

    return IdentityListResponse(
        total=len(identities),
        items=identities
    )


@router.post(
    "",
    response_model=IdentityResponse,
    summary="创建身份"
)
async def create_identity(
    identity_data: IdentityCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新身份

    - 需要提供角色ID (character_id)
    - 如果设置为主身份 (is_primary=true)，会自动取消该角色的其他主身份
    - 身份类型可选: real(真实)/public(公开)/secret(秘密)/disguise(伪装)
    """
    user_id = get_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")

    # 获取角色以确定项目ID
    character_result = await db.execute(
        select(Character).where(Character.id == identity_data.character_id)
    )
    character = character_result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 验证项目权限
    await verify_project_access(character.project_id, user_id, db)

    try:
        identity = await identity_service.create_identity(
            project_id=character.project_id,
            identity_data=identity_data,
            db=db
        )
        await db.commit()
        await db.refresh(identity)
        return identity
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建身份失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建身份失败: {str(e)}")


@router.get(
    "/{identity_id}",
    response_model=IdentityDetailResponse,
    summary="获取身份详情"
)
async def get_identity(
    identity_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    获取身份详情，包含职业列表和认知关系列表
    """
    result = await db.execute(
        select(Identity).where(Identity.id == identity_id)
    )
    identity = result.scalar_one_or_none()

    if not identity:
        raise HTTPException(status_code=404, detail="身份不存在")

    # 验证项目权限
    user_id = get_user_id(request)
    await verify_project_access(identity.project_id, user_id, db)

    # 获取职业列表
    careers = await identity_service.get_identity_careers(identity_id, db)

    # 获取认知关系
    knowledge_list = await identity_service.get_identity_knowledge(identity_id, db)

    return IdentityDetailResponse(
        id=identity.id,
        project_id=identity.project_id,
        character_id=identity.character_id,
        name=identity.name,
        identity_type=identity.identity_type,
        is_primary=identity.is_primary,
        appearance=identity.appearance,
        personality=identity.personality,
        background=identity.background,
        voice_style=identity.voice_style,
        status=identity.status,
        created_at=identity.created_at,
        updated_at=identity.updated_at,
        careers=careers,
        knowledge=knowledge_list
    )


@router.put(
    "/{identity_id}",
    response_model=IdentityResponse,
    summary="更新身份"
)
async def update_identity(
    identity_id: str,
    identity_update: IdentityUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    更新身份信息

    - 如果将 is_primary 设置为 true，会自动取消该角色的其他主身份
    - 只更新提供的字段，未提供的字段保持不变
    """
    result = await db.execute(
        select(Identity).where(Identity.id == identity_id)
    )
    identity = result.scalar_one_or_none()

    if not identity:
        raise HTTPException(status_code=404, detail="身份不存在")

    # 验证项目权限
    user_id = get_user_id(request)
    await verify_project_access(identity.project_id, user_id, db)

    try:
        updated_identity = await identity_service.update_identity(
            identity_id=identity_id,
            identity_update=identity_update,
            db=db
        )
        await db.commit()
        await db.refresh(updated_identity)
        return updated_identity
    except Exception as e:
        logger.error(f"更新身份失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新身份失败: {str(e)}")


@router.delete(
    "/{identity_id}",
    summary="删除身份"
)
async def delete_identity(
    identity_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    删除身份

    - 级联删除该身份的职业关联
    - 级联删除该身份的认知关系
    """
    result = await db.execute(
        select(Identity).where(Identity.id == identity_id)
    )
    identity = result.scalar_one_or_none()

    if not identity:
        raise HTTPException(status_code=404, detail="身份不存在")

    # 验证项目权限
    user_id = get_user_id(request)
    await verify_project_access(identity.project_id, user_id, db)

    success = await identity_service.delete_identity(identity_id, db)
    if not success:
        raise HTTPException(status_code=500, detail="删除身份失败")

    await db.commit()
    return {"message": "身份删除成功"}


# ===== Character Identities =====

@router.get(
    "/character/{character_id}",
    response_model=List[IdentityResponse],
    summary="获取角色的所有身份"
)
async def get_character_identities(
    character_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定角色的所有身份

    - 主身份排在前面
    - 按创建时间升序排列
    """
    # 获取角色以确定项目ID
    character_result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    character = character_result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 验证项目权限
    user_id = get_user_id(request)
    await verify_project_access(character.project_id, user_id, db)

    identities = await identity_service.get_identities_by_character(character_id, db)
    return identities


# ===== Identity Careers =====

@router.get(
    "/{identity_id}/careers",
    response_model=List[IdentityCareerDetail],
    summary="获取身份的职业列表"
)
async def get_identity_careers(
    identity_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    获取身份的所有职业关联（含职业详情）
    """
    result = await db.execute(
        select(Identity).where(Identity.id == identity_id)
    )
    identity = result.scalar_one_or_none()
    if not identity:
        raise HTTPException(status_code=404, detail="身份不存在")

    # 验证项目权限
    user_id = get_user_id(request)
    await verify_project_access(identity.project_id, user_id, db)

    careers = await identity_service.get_identity_careers(identity_id, db)
    return careers


@router.post(
    "/{identity_id}/careers",
    response_model=IdentityCareerResponse,
    summary="为身份添加职业"
)
async def add_identity_career(
    identity_id: str,
    career_data: IdentityCareerCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    为身份添加职业关联

    - 需要提供职业ID和职业类型 (main/sub)
    - current_stage 必须在职业的最大阶段范围内
    """
    result = await db.execute(
        select(Identity).where(Identity.id == identity_id)
    )
    identity = result.scalar_one_or_none()
    if not identity:
        raise HTTPException(status_code=404, detail="身份不存在")

    # 验证项目权限
    user_id = get_user_id(request)
    await verify_project_access(identity.project_id, user_id, db)

    # 覆盖 identity_id
    career_data.identity_id = identity_id

    try:
        identity_career = await identity_service.add_identity_career(
            identity_id=identity_id,
            career_data=career_data,
            project_id=identity.project_id,
            db=db
        )
        await db.commit()
        await db.refresh(identity_career)
        return identity_career
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"添加身份职业失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加身份职业失败: {str(e)}")


@router.put(
    "/{identity_id}/careers/{career_id}",
    response_model=IdentityCareerResponse,
    summary="更新身份职业阶段"
)
async def update_identity_career(
    identity_id: str,
    career_id: str,
    career_update: IdentityCareerUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    更新身份职业关联的阶段和进度

    - 可以更新 current_stage（阶段）和 stage_progress（进度）
    - 也可以更新时间信息
    """
    result = await db.execute(
        select(Identity).where(Identity.id == identity_id)
    )
    identity = result.scalar_one_or_none()
    if not identity:
        raise HTTPException(status_code=404, detail="身份不存在")

    # 验证项目权限
    user_id = get_user_id(request)
    await verify_project_access(identity.project_id, user_id, db)

    try:
        updated_career = await identity_service.update_identity_career(
            identity_id=identity_id,
            career_id=career_id,
            career_update=career_update,
            db=db
        )
        if not updated_career:
            raise HTTPException(status_code=404, detail="身份职业关联不存在")

        await db.commit()
        await db.refresh(updated_career)
        return updated_career
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新身份职业失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新身份职业失败: {str(e)}")


@router.delete(
    "/{identity_id}/careers/{career_id}",
    summary="删除身份职业"
)
async def delete_identity_career(
    identity_id: str,
    career_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    删除身份的职业关联
    """
    result = await db.execute(
        select(Identity).where(Identity.id == identity_id)
    )
    identity = result.scalar_one_or_none()
    if not identity:
        raise HTTPException(status_code=404, detail="身份不存在")

    # 验证项目权限
    user_id = get_user_id(request)
    await verify_project_access(identity.project_id, user_id, db)

    success = await identity_service.delete_identity_career(identity_id, career_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="身份职业关联不存在")

    await db.commit()
    return {"message": "身份职业删除成功"}


# ===== Identity Knowledge =====

@router.get(
    "/{identity_id}/knowledge",
    response_model=List[IdentityKnowledgeWithKnower],
    summary="获取身份的认知关系"
)
async def get_identity_knowledge(
    identity_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    获取身份的所有认知关系（含认知者信息）

    返回哪些角色知道这个身份，以及他们的认知程度
    """
    result = await db.execute(
        select(Identity).where(Identity.id == identity_id)
    )
    identity = result.scalar_one_or_none()
    if not identity:
        raise HTTPException(status_code=404, detail="身份不存在")

    # 验证项目权限
    user_id = get_user_id(request)
    await verify_project_access(identity.project_id, user_id, db)

    knowledge_list = await identity_service.get_identity_knowledge(identity_id, db)
    return knowledge_list


@router.post(
    "/{identity_id}/knowledge",
    response_model=IdentityKnowledgeResponse,
    summary="添加认知关系"
)
async def add_identity_knowledge(
    identity_id: str,
    knowledge_data: IdentityKnowledgeCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    添加身份认知关系

    - 记录哪个角色 (knower_character_id) 知道了这个身份
    - 可以指定认知程度 (full/partial/suspected)
    - 可以记录何时知道、如何发现等信息
    """
    result = await db.execute(
        select(Identity).where(Identity.id == identity_id)
    )
    identity = result.scalar_one_or_none()
    if not identity:
        raise HTTPException(status_code=404, detail="身份不存在")

    # 验证项目权限
    user_id = get_user_id(request)
    await verify_project_access(identity.project_id, user_id, db)

    # 覆盖 identity_id
    knowledge_data.identity_id = identity_id

    try:
        knowledge = await identity_service.add_knowledge(
            identity_id=identity_id,
            knowledge_data=knowledge_data,
            project_id=identity.project_id,
            db=db
        )
        await db.commit()
        await db.refresh(knowledge)
        return knowledge
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"添加认知关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加认知关系失败: {str(e)}")


@router.put(
    "/{identity_id}/knowledge/{knowledge_id}",
    response_model=IdentityKnowledgeResponse,
    summary="更新认知关系"
)
async def update_identity_knowledge(
    identity_id: str,
    knowledge_id: str,
    knowledge_update: IdentityKnowledgeUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    更新身份认知关系

    - 可以更新认知程度
    - 可以更新发现方式等信息
    """
    result = await db.execute(
        select(Identity).where(Identity.id == identity_id)
    )
    identity = result.scalar_one_or_none()
    if not identity:
        raise HTTPException(status_code=404, detail="身份不存在")

    # 验证项目权限
    user_id = get_user_id(request)
    await verify_project_access(identity.project_id, user_id, db)

    try:
        updated_knowledge = await identity_service.update_knowledge(
            identity_id=identity_id,
            knowledge_id=knowledge_id,
            knowledge_update=knowledge_update,
            db=db
        )
        if not updated_knowledge:
            raise HTTPException(status_code=404, detail="认知关系不存在")

        await db.commit()
        await db.refresh(updated_knowledge)
        return updated_knowledge
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新认知关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新认知关系失败: {str(e)}")


@router.delete(
    "/{identity_id}/knowledge/{knowledge_id}",
    summary="删除认知关系"
)
async def delete_identity_knowledge(
    identity_id: str,
    knowledge_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    删除身份认知关系

    - 移除角色对该身份的认知记录
    """
    result = await db.execute(
        select(Identity).where(Identity.id == identity_id)
    )
    identity = result.scalar_one_or_none()
    if not identity:
        raise HTTPException(status_code=404, detail="身份不存在")

    # 验证项目权限
    user_id = get_user_id(request)
    await verify_project_access(identity.project_id, user_id, db)

    success = await identity_service.delete_knowledge(identity_id, knowledge_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="认知关系不存在")

    await db.commit()
    return {"message": "认知关系删除成功"}
