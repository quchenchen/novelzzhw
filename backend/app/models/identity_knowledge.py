"""身份认知关系数据模型"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.sql import func
from app.database import Base
import uuid


class IdentityKnowledge(Base):
    """身份认知关系表 - 记录谁知道了哪个角色的哪个身份"""
    __tablename__ = "identity_knowledge"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    identity_id = Column(String(36), ForeignKey("identities.id", ondelete="CASCADE"), nullable=False, index=True, comment="身份ID")
    knower_character_id = Column(String(36), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True, comment="知道此身份的角色ID")

    # 认知程度
    knowledge_level = Column(String(50), nullable=False, comment="认知程度: full(完全知晓)/partial(部分知晓)/suspected(怀疑)")

    # 认知来源
    since_when = Column(String(100), comment="何时开始知道（小说时间线）")
    discovered_how = Column(Text, comment="如何发现的")
    is_secret = Column(Boolean, default=True, comment="是否为秘密（true=需要保密，false=可以公开）")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    __table_args__ = (
        Index('idx_knowledge_level', 'knowledge_level'),
        Index('idx_identity_knower', 'identity_id', 'knower_character_id', unique=True),
        Index('idx_knower_character', 'knower_character_id'),
    )

    def __repr__(self):
        return f"<IdentityKnowledge(identity_id={self.identity_id}, knower={self.knower_character_id}, level={self.knowledge_level})>"
