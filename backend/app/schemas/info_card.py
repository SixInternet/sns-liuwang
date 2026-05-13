"""信息卡片 Pydantic 模式 — 请求/响应数据校验"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# 与 ORM 注释及前端 CardItem 保持一致
_CARD_STATUS_VALUES = Literal['pending', 'liked', 'disliked', 'valuable', 'valueless']


class CardCreate(BaseModel):
    """创建卡片请求体"""

    title: str = Field(..., min_length=1, max_length=500, description="卡片标题")
    summary: str | None = Field(None, description="内容摘要")
    source_url: str | None = Field(None, description="来源链接")
    source_context: str | None = Field(None, description="原文段落范围")
    category: str | None = Field(None, description="四项分类: 喜欢有价值/喜欢无价值/不喜欢有价值/不喜欢无价值")
    source_id: UUID | None = Field(None, description="关联原始信息源")
    collector: str | None = Field(None, description="采集来源: 手机/桌面/网页")
    raw_screenshot_url: str | None = Field(None, description="原始截图链接")


class CardResponse(BaseModel):
    """卡片响应体"""

    id: UUID
    title: str
    summary: str | None
    source_url: str | None
    source_context: str | None
    category: str | None
    status: str
    collected_at: datetime
    source_id: UUID | None
    collector: str | None
    raw_screenshot_url: str | None

    model_config = {"from_attributes": True}


class CardList(BaseModel):
    """卡片列表响应体"""

    items: list[CardResponse]
    total: int = Field(..., description="总数")


class CardStatusUpdate(BaseModel):
    """更新卡片状态请求体"""

    status: _CARD_STATUS_VALUES = Field(..., description="新状态: pending/liked/disliked/valuable/valueless")


class CardUpdate(BaseModel):
    """更新卡片内容请求体"""

    title: str | None = Field(None, min_length=1, max_length=500, description="卡片标题")
    summary: str | None = Field(None, description="内容摘要")
    category: str | None = Field(None, description="分类")
