from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

_SOURCE_STATUS_VALUES = Literal["active", "needs_intervention", "disabled"]


class SearchSourceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    base_url: str = Field(..., min_length=1)
    auth_notes: str | None = None


class SearchSourceResponse(BaseModel):
    id: UUID
    title: str
    base_url: str
    domain: str
    status: str
    auth_status: str
    auth_notes: str | None
    last_verified_at: datetime | None
    last_error: str | None
    user_id: UUID
    created_at: datetime
    updated_at: datetime | None
    topics_count: int = 0
    topic_id: UUID | None = None

    model_config = {"from_attributes": True}


class SearchSourceList(BaseModel):
    items: list[SearchSourceResponse]
    total: int


class SearchSourceStatusUpdate(BaseModel):
    status: _SOURCE_STATUS_VALUES
