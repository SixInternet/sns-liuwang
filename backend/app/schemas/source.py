"""信息来源（Source）Pydantic 模式 — 请求/响应数据校验"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SourceCreate(BaseModel):
    """创建信息来源请求体"""

    title: str
    url: str | None = None
    content_raw: str | None = None
    collector: str | None = None  # 网页/手机/桌面/手动


class SourceResponse(BaseModel):
    """信息来源响应体"""

    id: UUID
    title: str
    url: str | None
    content_markdown: str | None
    content_hash: str | None
    diff_log: str | None
    status: str  # pending/refined/failed
    collector: str | None
    collected_at: datetime
    refined_at: datetime | None
    card_count: int = 0  # computed field, not in DB

    model_config = {"from_attributes": True}


class SourceList(BaseModel):
    """信息来源列表响应体"""

    items: list[SourceResponse]
    total: int


class SourceUpdateStatus(BaseModel):
    """更新信息来源状态请求体"""

    status: str  # pending/refined/failed
