"""身份职业关联数据模型"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base
import uuid


class IdentityCareer(Base):
    """身份职业关联表 - 身份与职业的关联关系"""
    __tablename__ = "identity_careers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    identity_id = Column(String(36), ForeignKey("identities.id", ondelete="CASCADE"), nullable=False, index=True, comment="身份ID")
    career_id = Column(String(36), ForeignKey("careers.id", ondelete="CASCADE"), nullable=False, index=True, comment="职业ID")

    # 职业类型
    career_type = Column(String(50), nullable=False, comment="职业类型: main(主职业)/sub(副职业)")

    # 阶段进度
    current_stage = Column(Integer, nullable=False, default=1, comment="当前阶段（对应职业中的数值）")
    stage_progress = Column(Integer, default=0, comment="阶段内进度（0-100）")

    # 时间记录
    started_at = Column(String(100), comment="开始修炼时间（小说时间线）")
    reached_current_stage_at = Column(String(100), comment="到达当前阶段时间")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    __table_args__ = (
        Index('idx_identity_career_type', 'career_type'),
        Index('idx_identity_career', 'identity_id', 'career_id', unique=True),
    )

    def __repr__(self):
        return f"<IdentityCareer(identity_id={self.identity_id}, career_id={self.career_id}, type={self.career_type})>"
