import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("topics.id"), nullable=True)
    search_source_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("search_sources.id"), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued",
        comment="queued/in_progress/completed/partial/failed",
    )
    urls_scanned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    urls_collected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sources_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cards_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_info: Mapped[str | None] = mapped_column(Text, nullable=True, comment="JSON")
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    topic = relationship("Topic")
    search_source = relationship("SearchSource")
