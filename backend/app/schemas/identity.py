"""身份相关的Pydantic模型"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime


# ===== Identity 相关 =====

class IdentityBase(BaseModel):
    """身份基础模型"""
    name: str = Field(..., description="身份名称/别名", min_length=1, max_length=100)
    identity_type: str = Field(..., description="身份类型: real(真实)/public(公开)/secret(秘密)/disguise(伪装)")
    is_primary: bool = Field(False, description="是否为主身份")
    appearance: Optional[str] = Field(None, description="外貌描述")
    personality: Optional[str] = Field(None, description="性格表现")
    background: Optional[str] = Field(None, description="身份背景")
    voice_style: Optional[str] = Field(None, description="说话风格")
    status: str = Field("active", description="状态: active(活跃)/inactive(未激活)/burned(已暴露)")

    @field_validator('identity_type')
    @classmethod
    def validate_identity_type(cls, v: str) -> str:
        """验证身份类型"""
        valid_types = {'real', 'public', 'secret', 'disguise'}
        if v not in valid_types:
            raise ValueError(f'identity_type must be one of {valid_types}')
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """验证状态"""
        valid_statuses = {'active', 'inactive', 'burned'}
        if v not in valid_statuses:
            raise ValueError(f'status must be one of {valid_statuses}')
        return v


class IdentityCreate(IdentityBase):
    """创建身份的请求模型"""
    character_id: str = Field(..., description="角色ID")


class IdentityUpdate(BaseModel):
    """更新身份的请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    identity_type: Optional[str] = None
    is_primary: Optional[bool] = None
    appearance: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    voice_style: Optional[str] = None
    status: Optional[str] = None


class IdentityResponse(IdentityBase):
    """身份响应模型"""
    id: str
    project_id: str
    character_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IdentityListResponse(BaseModel):
    """身份列表响应模型"""
    total: int
    items: List[IdentityResponse]


class IdentityDetailResponse(IdentityResponse):
    """身份详情响应模型（包含职业和认知关系）"""
    careers: List['IdentityCareerDetail'] = Field(default_factory=list, description="身份职业列表")
    knowledge: List['IdentityKnowledgeResponse'] = Field(default_factory=list, description="认知关系列表")


# ===== IdentityCareer 相关 =====

class IdentityCareerBase(BaseModel):
    """身份职业关联基础模型"""
    career_id: str = Field(..., description="职业ID")
    career_type: str = Field(..., description="职业类型: main(主职业)/sub(副职业)")
    current_stage: int = Field(1, description="当前阶段", ge=1)
    stage_progress: int = Field(0, description="阶段内进度（0-100）", ge=0, le=100)
    started_at: Optional[str] = Field(None, description="开始修炼时间")
    reached_current_stage_at: Optional[str] = Field(None, description="到达当前阶段时间")

    @field_validator('career_type')
    @classmethod
    def validate_career_type(cls, v: str) -> str:
        """验证职业类型"""
        if v not in {'main', 'sub'}:
            raise ValueError('career_type must be either "main" or "sub"')
        return v


class IdentityCareerCreate(IdentityCareerBase):
    """创建身份职业关联的请求模型"""
    identity_id: str = Field(..., description="身份ID")


class IdentityCareerUpdate(BaseModel):
    """更新身份职业关联的请求模型"""
    current_stage: Optional[int] = Field(None, ge=1)
    stage_progress: Optional[int] = Field(None, ge=0, le=100)
    reached_current_stage_at: Optional[str] = None
    started_at: Optional[str] = None


class IdentityCareerDetail(BaseModel):
    """身份职业详情模型（包含职业信息）"""
    id: str
    identity_id: str
    career_id: str
    career_name: str = Field(..., description="职业名称")
    career_type: str
    current_stage: int
    stage_name: Optional[str] = Field(None, description="当前阶段名称")
    stage_description: Optional[str] = Field(None, description="当前阶段描述")
    stage_progress: int
    max_stage: int = Field(..., description="该职业的最大阶段")
    started_at: Optional[str] = None
    reached_current_stage_at: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IdentityCareerResponse(IdentityCareerBase):
    """身份职业关联响应模型"""
    id: str
    identity_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===== IdentityKnowledge 相关 =====

class IdentityKnowledgeBase(BaseModel):
    """身份认知关系基础模型"""
    knower_character_id: str = Field(..., description="知道此身份的角色ID")
    knowledge_level: str = Field(..., description="认知程度: full(完全知晓)/partial(部分知晓)/suspected(怀疑)")
    since_when: Optional[str] = Field(None, description="何时开始知道（小说时间线）")
    discovered_how: Optional[str] = Field(None, description="如何发现的")
    is_secret: bool = Field(True, description="是否为秘密（true=需要保密，false=可以公开）")

    @field_validator('knowledge_level')
    @classmethod
    def validate_knowledge_level(cls, v: str) -> str:
        """验证认知程度"""
        valid_levels = {'full', 'partial', 'suspected'}
        if v not in valid_levels:
            raise ValueError(f'knowledge_level must be one of {valid_levels}')
        return v


class IdentityKnowledgeCreate(IdentityKnowledgeBase):
    """创建身份认知关系的请求模型"""
    identity_id: str = Field(..., description="身份ID")


class IdentityKnowledgeUpdate(BaseModel):
    """更新身份认知关系的请求模型"""
    knowledge_level: Optional[str] = None
    since_when: Optional[str] = None
    discovered_how: Optional[str] = None
    is_secret: Optional[bool] = None


class IdentityKnowledgeResponse(IdentityKnowledgeBase):
    """身份认知关系响应模型"""
    id: str
    identity_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IdentityKnowledgeWithKnower(IdentityKnowledgeResponse):
    """带认知者信息的认知关系响应模型"""
    knower_name: str = Field(..., description="认知者角色名称")


# 更新前向引用
IdentityDetailResponse.model_rebuild()
