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

    # 时间线状态管理
    exposed_at_chapter = Column(
        Integer,
        nullable=True,
        comment="身份在第几章暴露（用于时间线状态计算，生成第N章时，若N<exposed_at_chapter则状态为active）"
    )

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    __table_args__ = (
        Index('idx_identity_type', 'identity_type'),
        Index('idx_status', 'status'),
        Index('idx_character_identity', 'character_id', 'identity_type'),
    )

    def get_status_at_chapter(self, target_chapter: int) -> str:
        """
        根据目标章节号计算身份当时的状态

        时间线感知逻辑：
        1. 如果身份从未暴露（exposed_at_chapter为None），返回当前状态
        2. 如果目标章节号 >= 暴露章节号，返回"burned"（已暴露）
        3. 如果目标章节号 < 暴露章节号，返回"active"（当时未暴露）

        Args:
            target_chapter: 目标章节号

        Returns:
            身份在该章节时间点的状态
        """
        if self.exposed_at_chapter is None:
            # 从未暴露过，返回当前状态
            return self.status
        if target_chapter >= self.exposed_at_chapter:
            # 目标章节在暴露之后或等于暴露章节
            return "burned"
        # 目标章节在暴露之前，当时未暴露
        return "active"

    def is_exposed_at_chapter(self, target_chapter: int) -> bool:
        """
        判断身份在目标章节是否已暴露

        Args:
            target_chapter: 目标章节号

        Returns:
            True表示已暴露，False表示未暴露
        """
        if self.exposed_at_chapter is None:
            # 如果当前状态是burned，认为在所有章节都已暴露
            return self.status == "burned"
        return target_chapter >= self.exposed_at_chapter

    def __repr__(self):
        return f"<Identity(id={self.id}, name={self.name}, type={self.identity_type})>"
