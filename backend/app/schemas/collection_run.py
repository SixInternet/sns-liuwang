from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CollectionRunResponse(BaseModel):
    id: UUID
    topic_id: UUID | None
    topic_name: str | None = None
    search_source_id: UUID | None
    status: str
    urls_scanned: int
    urls_collected: int
    sources_created: int
    cards_created: int
    error_info: str | None
    user_id: UUID
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class CollectionRunList(BaseModel):
    items: list[CollectionRunResponse]
    total: int
