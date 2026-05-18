"""采集进度 Schema — Sub-Agent 进度汇报与人工验证交互"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProgressReport(BaseModel):
    """Sub-agent 汇报进度"""
    collection_run_id: UUID
    step: str = Field(..., max_length=200)
    progress_pct: int = Field(..., ge=0, le=100)
    estimated_remaining: int = Field(0, ge=0)
    progress_type: str = Field("progress", pattern="^(progress|captcha|error|done)$")
    detail: str | None = None


class ProgressResponse(BaseModel):
    id: UUID
    collection_run_id: UUID
    step: str
    progress_pct: int
    estimated_remaining: int
    progress_type: str
    detail: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProgressList(BaseModel):
    items: list[ProgressResponse]
    total: int


class IngestRequest(BaseModel):
    """Sub-agent 提交采集内容"""
    collection_run_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    url: str | None = None
    content_raw: str | None = None
