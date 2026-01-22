"""身份数据模型"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Identity(Base):
    """身份表 - 角色的多重身份系统"""
    __tablename__ = "identities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True, comment="项目ID")
    character_id = Column(String(36), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True, comment="角色ID")

    # 基本信息
    name = Column(String(100), nullable=False, comment="身份名称/别名")
    identity_type = Column(String(50), nullable=False, default="real", comment="身份类型: real(真实)/public(公开)/secret(秘密)/disguise(伪装)")
    is_primary = Column(Boolean, default=False, comment="是否为主身份")

    # 身份详细描述
    appearance = Column(Text, comment="外貌描述")
    personality = Column(Text, comment="性格表现")
    background = Column(Text, comment="身份背景")
    voice_style = Column(Text, comment="说话风格")

    # 状态管理
    status = Column(String(50), default="active", comment="状态: active(活跃)/inactive(未激活)/burned(已暴露)")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    __table_args__ = (
        Index('idx_identity_type', 'identity_type'),
        Index('idx_status', 'status'),
        Index('idx_character_identity', 'character_id', 'identity_type'),
    )

    def __repr__(self):
        return f"<Identity(id={self.id}, name={self.name}, type={self.identity_type})>"
