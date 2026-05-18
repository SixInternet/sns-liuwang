import json
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TopicCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    keywords: list[str] | None = None
    search_depth: int = Field(5, ge=1, le=100)
    schedule_type: str = Field("daily", pattern="^(daily|weekly|custom)$")
    schedule_times: list[str] | None = None
    auto_refine: bool = False
    search_source_ids: list[UUID] = Field(default_factory=list)
    created_via: str | None = None


class TopicResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    keywords: list[str] | None
    search_depth: int
    enabled: bool
    schedule_type: str
    schedule_times: list[str] | None
    auto_refine: bool
    last_collected_at: datetime | None
    card_count: int
    created_via: str | None
    user_id: UUID
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}

    @field_validator("keywords", mode="before")
    @classmethod
    def parse_keywords_json(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("schedule_times", mode="before")
    @classmethod
    def parse_schedule_times_json(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class TopicList(BaseModel):
    items: list[TopicResponse]
    total: int


class TopicUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    keywords: list[str] | None = None
    search_depth: int | None = Field(None, ge=1, le=100)
    enabled: bool | None = None
    schedule_type: str | None = Field(None, pattern="^(daily|weekly|custom)$")
    schedule_times: list[str] | None = None
    auto_refine: bool | None = None
    search_source_ids: list[UUID] | None = None
