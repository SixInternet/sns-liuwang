import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class SearchSource(Base):
    __tablename__ = "search_sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False, comment="起始页面URL")
    domain: Mapped[str] = mapped_column(String(255), nullable=False, comment="自动从base_url提取域名")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active",
        comment="active/needs_intervention/disabled",
    )
    auth_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="none",
        comment="none/logged_in/session_ok/session_expired/captcha_blocked",
    )
    auth_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(),
    )

    topics = relationship(
        "Topic",
        secondary="topic_search_sources",
        back_populates="search_sources",
    )
