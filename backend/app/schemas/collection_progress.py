"""采集进度 Schema — 主会话进度汇报与人工验证交互"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProgressReport(BaseModel):
    """主会话汇报进度"""
    collection_run_id: UUID
    step: str = Field(..., max_length=200)
    progress_pct: int = Field(..., ge=0, le=100)
    estimated_remaining: int = Field(0, ge=0)
    progress_type: str = Field(
        "progress",
        pattern="^(progress|captcha|resolved|error|done)$",
    )
    step_phase: str | None = Field(
        None,
        pattern="^(planned|running|done)$",
    )
    sources_collected: int | None = Field(None, ge=0)
    max_sources: int | None = Field(None, ge=1)
    detail: str | None = None


class ProgressResponse(BaseModel):
    id: UUID
    collection_run_id: UUID
    step: str
    progress_pct: int
    estimated_remaining: int
    progress_type: str
    step_phase: str | None = None
    sources_collected: int | None = None
    max_sources: int | None = None
    detail: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProgressList(BaseModel):
    items: list[ProgressResponse]
    total: int


class ProgressTimelineResponse(BaseModel):
    """完整时间线响应"""
    items: list[ProgressResponse]
    total: int
    sources_created: int = 0
    max_sources: int = 10


class ProgressReportResponse(BaseModel):
    ok: bool = True
    id: str
    sources_created: int = 0
    max_sources: int = 10


class IngestRequest(BaseModel):
    """主会话提交采集内容（DOM HTML）"""
    collection_run_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    url: str | None = None
    content_html: str = Field(..., min_length=1)
    content_raw: str | None = Field(None, deprecated="请使用 content_html")
