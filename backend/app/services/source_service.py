"""信息来源（Source）业务逻辑服务"""

import hashlib
from datetime import datetime, timezone
from uuid import UUID

import httpx
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source
from app.models.info_card import InfoCard
from app.preprocessor import preprocess_bytes
from app.schemas.source import SourceCreate

# 代理配置
PROXY_URL = "http://Clash:etDCi7tM@192.168.6.1:7890"


async def _fetch_url_content(url: str) -> str | None:
    """尝试获取 URL 内容，直接获取失败则通过代理重试"""
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception:
        pass

    try:
        async with httpx.AsyncClient(
            timeout=15.0, follow_redirects=True, proxies=PROXY_URL
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception:
        return None


async def create_source(
    db: AsyncSession, source_data: SourceCreate, user_id: UUID
) -> Source:
    """创建信息来源。

    支持三种模式：
    1. 提供 content_raw → 直接用 preprocess_bytes 转换
    2. 提供 url（无 content_raw）→ 先获取 URL 内容，再转换
    3. 相同 user + 相同 url 视为重复 → 更新现有记录并记录差异
    """
    # 检查重复：相同 user + 相同 url
    if source_data.url:
        result = await db.execute(
            select(Source).where(
                Source.user_id == user_id, Source.url == source_data.url
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            # 更新现有记录
            if source_data.content_raw:
                # 用新的 content_raw 重新预处理
                new_markdown = preprocess_bytes(
                    source_data.content_raw.encode("utf-8"),
                    filename="document.html",
                )
                new_hash = hashlib.sha256(
                    source_data.content_raw.encode("utf-8")
                ).hexdigest()

                # 如果 hash 不同，说明内容有更新
                if existing.content_hash != new_hash:
                    diff_entry = (
                        f"[{datetime.now(timezone.utc).isoformat()}] "
                        f"内容更新：{existing.title} → {source_data.title}\n"
                    )
                    if existing.diff_log:
                        existing.diff_log += diff_entry
                    else:
                        existing.diff_log = diff_entry

                    existing.content_raw = source_data.content_raw
                    existing.content_markdown = new_markdown
                    existing.content_hash = new_hash
                    existing.title = source_data.title
                    existing.collector = source_data.collector or existing.collector
                    existing.collected_at = datetime.now(timezone.utc)

                await db.commit()
                await db.refresh(existing)
                return existing
            else:
                # 无新内容，只更新标题/采集器
                existing.title = source_data.title
                existing.collector = source_data.collector or existing.collector
                await db.commit()
                await db.refresh(existing)
                return existing

    content_raw = source_data.content_raw
    url_content = None

    # 如果有 url 但没有 content_raw，尝试获取 URL 内容
    if source_data.url and not content_raw:
        url_content = await _fetch_url_content(source_data.url)
        if url_content and len(url_content.strip()) > 0:
            content_raw = url_content

    # 尝试预处理内容
    content_markdown = None
    content_hash = None

    if content_raw and len(content_raw.strip()) > 0:
        raw_bytes = content_raw.encode("utf-8")
        if source_data.url and not source_data.content_raw:
            # URL 获取的内容标记为 HTML 格式
            content_markdown = preprocess_bytes(raw_bytes, filename="document.html")
        else:
            content_markdown = preprocess_bytes(raw_bytes, filename="document.html")
        content_hash = hashlib.sha256(raw_bytes).hexdigest()
    elif source_data.url:
        # URL 获取失败且无 content_raw
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="无法获取 URL 内容")

    source = Source(
        title=source_data.title,
        url=source_data.url,
        content_raw=content_raw,
        content_markdown=content_markdown,
        content_hash=content_hash,
        status="pending",
        collector=source_data.collector,
        user_id=user_id,
        collected_at=datetime.now(timezone.utc),
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def list_sources(
    db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 20
) -> tuple[list[Source], int]:
    """获取当前用户的信息来源列表，包含关联卡片数量。"""
    # 总数
    count_q = await db.execute(
        select(func.count()).select_from(Source).where(Source.user_id == user_id)
    )
    total = count_q.scalar() or 0

    # 分页查询
    result = await db.execute(
        select(Source)
        .where(Source.user_id == user_id)
        .order_by(desc(Source.collected_at))
        .offset(skip)
        .limit(limit)
    )
    sources = list(result.scalars().all())

    # 为每个 source 计算 card_count
    for s in sources:
        cnt_q = await db.execute(
            select(func.count())
            .select_from(InfoCard)
            .where(InfoCard.source_id == s.id)
        )
        s.card_count = cnt_q.scalar() or 0

    return sources, total


async def get_source(db: AsyncSession, source_id: UUID) -> Source | None:
    """根据 ID 获取信息来源"""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if source:
        cnt_q = await db.execute(
            select(func.count())
            .select_from(InfoCard)
            .where(InfoCard.source_id == source.id)
        )
        source.card_count = cnt_q.scalar() or 0
    return source


async def update_source_status(
    db: AsyncSession, source_id: UUID, status: str
) -> Source | None:
    """更新信息来源状态"""
    source = await get_source(db, source_id)
    if source is None:
        return None
    source.status = status
    if status == "refined":
        source.refined_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(source)
    return source


async def delete_source(db: AsyncSession, source_id: UUID) -> bool:
    """删除信息来源"""
    source = await get_source(db, source_id)
    if source is None:
        return False
    await db.delete(source)
    await db.commit()
    return True
