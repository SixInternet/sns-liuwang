import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Boolean, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

# 多对多关联表：Topic <-> SearchSource
topic_search_sources = Table(
    "topic_search_sources",
    Base.metadata,
    Column("topic_id", ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
    Column("search_source_id", ForeignKey("search_sources.id", ondelete="CASCADE"), primary_key=True),
)


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="JSON列表，如 '[\"光子芯片\",\"光计算\"]'",
    )
    search_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=5, comment="每次最多浏览页面数")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_refine: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="采集后自动精炼为卡片")
    schedule_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="daily",
        comment="daily/weekly/custom",
    )
    schedule_times: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="JSON时间数组如 '[\"08:00\",\"14:00\",\"20:00\"]'",
    )
    last_collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    card_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_via: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(),
    )

    search_sources = relationship(
        "SearchSource",
        secondary=topic_search_sources,
        back_populates="topics",
    )
