"""采集编排器 — 协调 BrowserAdapter 与 Screener 完成一轮信息采集"""

import json
import logging
import re
from dataclasses import dataclass
from urllib.parse import urljoin

from app.collector.browser_adapter import BrowserAdapter
from app.collector.screener import Screener
from app.models.search_source import SearchSource
from app.models.topic import Topic

logger = logging.getLogger(__name__)


@dataclass
class CollectResult:
    success: bool
    urls_scanned: int = 0
    urls_collected: int = 0
    error: str | None = None
    anomaly_detected: bool = False
    anomaly_type: str | None = None
    collected_sources: list[dict] | None = None  # [{url, title, content_raw}]


def _parse_keywords(topic: "Topic") -> list[str]:
    kw = topic.keywords
    if isinstance(kw, str):
        try:
            kw = json.loads(kw)
        except (json.JSONDecodeError, TypeError):
            kw = []
    return kw if isinstance(kw, list) else []


def _extract_urls(text: str, base_url: str) -> list[str]:
    """从页面文本中提取 URL 链接
    优先从 --- LINKS --- 标记节提取（通过 CDP JS 获取的 a.href），
    兜底从全文正则提取。"""
    # 优先从 LINKS 标记节提取
    if "--- LINKS ---" in text:
        links_section = text.split("--- LINKS ---", 1)[-1].strip()
        urls = [l.strip() for l in links_section.split("\n") if l.strip().startswith("http")]
        if urls:
            return list(dict.fromkeys(urls))
    # 兜底：全文正则
    urls = re.findall(r'https?://[^\s"\'<>)]+', text)
    return list(dict.fromkeys(urls))


class Collector:
    def __init__(self, browser: BrowserAdapter, screener: Screener):
        self.browser = browser
        self.screener = screener

    async def collect_topic(
        self,
        topic: "Topic",
        source: "SearchSource",
        depth: int = 5,
    ) -> CollectResult:
        keywords = _parse_keywords(topic)
        if not keywords:
            return CollectResult(
                success=False,
                error=f"Topic {topic.id} 没有关键词配置",
            )

        keyword = " ".join(keywords[:3])

        # 统一由 agent_session 通过 hook:liuwang-space 主会话 + opendevbrowser 采集
        logger.warning("collect_topic() 已在 CDP 协议代码移除后禁用，请使用 agent_session.spawn_collection()")
        return CollectResult(
            success=False,
            error="collect_topic() 已禁用，请通过 agent_session.spawn_collection() 配合 hook 主会话 + opendevbrowser 采集",
        )

    async def check_captcha(self, screenshot_path: str) -> bool:
        anomaly = await self.screener.detect_page_anomaly(screenshot_path)
        if anomaly and anomaly.get("type") in ("captcha", "robot_detection"):
            return True
        return False
