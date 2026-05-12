"""信息卡片模型 — 收集的信息条目"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InfoCard(Base):
    """信息卡片表，存储收集到的各类信息条目"""

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
        DateTime, nullable=False, server_default="now()", comment="收集时间"
    )
    source_id: Mapped[str | None] = mapped_column(String, nullable=True, comment="关联原始信息源")
    collector: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="采集来源: 手机/桌面/网页"
    )
    raw_screenshot_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="原始截图链接"
    )
