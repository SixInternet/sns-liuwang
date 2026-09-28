"""采集进度记录 — 主会话采集每步汇报的进度与 CAPTCHA 状态"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CollectionProgress(Base):
    __tablename__ = "collection_progress"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    collection_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("collection_runs.id", ondelete="CASCADE"), nullable=False,
    )
    step: Mapped[str] = mapped_column(String(200), nullable=False, comment="当前步骤描述")
    progress_pct: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="0-100 进度百分比",
    )
    estimated_remaining: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="预计剩余秒数",
    )
    progress_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="progress",
        comment="progress / captcha / resolved / error / done",
    )
    step_phase: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default="running",
        comment="planned / running / done",
    )
    sources_collected: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=0, comment="当前已 ingest 数",
    )
    max_sources: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=10, comment="本轮上限",
    )
    detail: Mapped[str | None] = mapped_column(Text, nullable=True, comment="详细描述")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now,
    )

    collection_run = relationship("CollectionRun", backref="progress_entries")
