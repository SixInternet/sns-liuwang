"""DeepSeek 精炼服务 — 将 Markdown 内容拆分为信息卡片"""

import json
import re
from datetime import datetime, timezone
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source
from app.models.info_card import InfoCard

from app.config import get_settings

_settings = get_settings()

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = _settings.deepseek_api_key or ""
DEEPSEEK_MODEL = _settings.deepseek_model or "deepseek-chat"

PROXY_URL = "http://Clash:etDCi7tM@192.168.6.1:7890"

SYSTEM_PROMPT = """你是一个信息精炼助手。将用户提供的 Markdown 内容精炼为若干条独立的信息卡片。

每条卡片包含：
- title: 简短的信息标题（不超过15个字）
- summary: 精炼后的关键内容摘要（不超过80字）
- category: 分类，从以下选择：技术/生活/工作/学习/社交/娱乐/健康/其他

要求：
1. 每张卡片聚焦一个独立的信息点
2. 保持客观，不要添加原文没有的信息或主观评价
3. 如果内容包含多个不同主题，拆分为多张卡片
4. 以 JSON 数组格式输出，例如：
[{"title": "标题", "summary": "摘要内容", "category": "技术"}]
5. 只输出 JSON 数组，不要包含其他文字、Markdown 代码块或注释"""


def _parse_card_json(raw: str) -> list[dict]:
    """从 DeepSeek 响应中解析 JSON 卡片数组"""
    raw = raw.strip()

    # 移除 Markdown 代码块包裹
    lines = raw.split("\n")
    clean_lines = []
    in_code = False
    for line in lines:
        if line.startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            clean_lines.append(line)
    raw = "\n".join(clean_lines).strip()

    # 直接解析
    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            for key in ("cards", "items", "data"):
                if key in result and isinstance(result[key], list):
                    return result[key]
        return [result] if isinstance(result, dict) else []
    except json.JSONDecodeError:
        pass

    # 尝试从文本中提取 JSON 数组
    match = re.search(r'\[[\s\S]*?\]', raw)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return []


async def _call_deepseek(content: str) -> list[dict]:
    """调用 DeepSeek API，返回卡片数据列表"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"请精炼以下内容：\n\n{content}"},
    ]

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4096,
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error = None
    for proxy in [None, PROXY_URL]:
        try:
            client_kwargs = {"timeout": 60.0}
            if proxy:
                client_kwargs["proxy"] = proxy
            async with httpx.AsyncClient(**client_kwargs) as client:
                resp = await client.post(
                    DEEPSEEK_API_URL, json=payload, headers=headers
                )
                resp.raise_for_status()
                data = resp.json()
                raw_content = data["choices"][0]["message"]["content"]
                return _parse_card_json(raw_content)
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"DeepSeek API 调用失败: {last_error}")


async def refine_source(db: AsyncSession, source_id: UUID) -> list[InfoCard]:
    """对 Source 进行精炼，生成 InfoCard

    流程：
    1. 读取 Source.content_markdown
    2. 调用 DeepSeek API 拆分为卡片
    3. 批量创建 InfoCard
    4. 更新 Source 状态为 refined
    """
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        raise ValueError(f"Source {source_id} 不存在")

    if not source.content_markdown:
        raise ValueError("Source 没有 content_markdown，无法精炼")

    # 调用 DeepSeek
    cards_data = await _call_deepseek(source.content_markdown)

    if not cards_data:
        raise ValueError("DeepSeek 未返回有效卡片数据")

    # 批量创建 InfoCard
    created_cards = []
    user_id_str = str(source.user_id) if source.user_id else ""

    for card_info in cards_data:
        card = InfoCard(
            title=card_info.get("title", "未命名")[:200],
            summary=card_info.get("summary", ""),
            source_url=source.url or "",
            status="pending",
            source_id=source_id,
            collector=source.collector,
        )
        db.add(card)
        created_cards.append(card)

    # 更新 Source 状态
    source.status = "refined"
    source.refined_at = datetime.now(timezone.utc)

    await db.commit()

    # Refresh
    for card in created_cards:
        await db.refresh(card)
    await db.refresh(source)

    return created_cards
