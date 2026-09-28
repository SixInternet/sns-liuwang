import uuid
from datetime import datetime

from sqlalchemy import Boolean, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InfoCard(Base):
    __tablename__ = "info_cards"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String, nullable=False, comment="卡片标题")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="内容摘要")
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True, comment="来源链接")
    source_context: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="原文段落范围"
    )
    category: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="四项分类: 喜欢有价值/喜欢无价值/不喜欢有价值/不喜欢无价值"
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="pending", comment="状态: pending/liked/disliked/valuable/valueless"
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        comment="收集时间",
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sources.id"), nullable=True, comment="关联原始信息源"
    )
    collector: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="采集来源: 手机/桌面/网页"
    )
    raw_screenshot_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="原始截图链接"
    )
    memory_synced: Mapped[bool] = mapped_column(default=False, comment="是否已同步到记忆中")

    source = relationship("Source", back_populates="cards")
