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

        # 远程模式：链式执行，保留页面状态
        if self.browser._is_remote():
            return await self._collect_remote(keyword, source, depth)

        # 本地模式：逐命令执行（保持原有逻辑）
        return await self._collect_local(keyword, source, depth)

    async def _collect_remote(
        self, keyword: str, source: "SearchSource", depth: int
    ) -> CollectResult:
        """远程 CDP 模式：通过 CDP 原生协议获取页面内容"""
        # 第一步：在百度直接搜索关键词（URL 参数方式，避免交互）
        import urllib.parse
        search_url = f"https://www.baidu.com/s?wd={urllib.parse.quote(keyword)}"
        search_result = await self.browser._cdp_get_page_content(search_url, wait_after_load=5)

        if not search_result.success:
            return CollectResult(success=False, error=f"搜索失败: {search_result.error}")

        # 从页面链接中提取目标 URL
        links = (search_result.extra or {}).get("links", [])
        if not links:
            return CollectResult(
                success=True, urls_scanned=0, urls_collected=0,
                error="未在搜索结果中找到链接",
            )

        # 用 _extract_urls 从 Markdown 文本中正则兜底
        urls = _extract_urls(search_result.output, source.base_url)
        urls = urls[:depth]
        logger.info("找到 %d 个链接", len(urls))

        # 第二步：遍历每个链接提取内容
        urls_scanned = 0
        urls_collected = 0
        collected = []
        for url in urls:
            urls_scanned += 1
            link_result = await self.browser._cdp_get_page_content(url, wait_after_load=4)
            if link_result.success and link_result.output.strip():
                urls_collected += 1
                extra = link_result.extra or {}
                title = extra.get("title", "") or url
                html = extra.get("html", "")
                collected.append({
                    "url": url,
                    "title": title,
                    "content_raw": html,
                    "content_markdown": link_result.output,
                })
                logger.info("采集 [%s]: title=%s markdown=%d chars html=%d chars",
                           url, title, len(link_result.output), len(html))
            else:
                logger.warning("提取失败 %s: %s", url, link_result.error or "空内容")

        return CollectResult(
            success=True,
            urls_scanned=urls_scanned,
            urls_collected=urls_collected,
            collected_sources=collected,
        )

    async def _collect_local(
        self, keyword: str, source: "SearchSource", depth: int
    ) -> CollectResult:
        """本地 CDP 模式：逐命令执行"""
        search_result = await self.browser.search_and_get_results(
            url=source.base_url,
            keyword=keyword,
            wait_ms=5000,
        )
        if not search_result.success:
            return CollectResult(
                success=False,
                error=f"搜索失败: {search_result.error}",
            )

        screenshot = await self.browser.screenshot()
        if not screenshot.success or not screenshot.screenshot_path:
            return CollectResult(
                success=False,
                error=f"截图失败: {screenshot.error}",
            )

        anomaly = await self.screener.detect_page_anomaly(
            screenshot.screenshot_path
        )
        if anomaly:
            logger.warning(
                "检测到页面异常 [%s]: %s", anomaly.get("type"), anomaly.get("description")
            )
            return CollectResult(
                success=False,
                error=anomaly.get("description", "页面异常"),
                anomaly_detected=True,
                anomaly_type=anomaly.get("type"),
            )

        links = await self.screener.analyze_search_results(
            screenshot.screenshot_path, keywords
        )
        urls_collected = 0
        urls_scanned = 0

        for link in links[:depth]:
            url = link.get("url", "")
            if not url:
                continue
            urls_scanned += 1

            open_result = await self.browser.open_url(url, wait_ms=3000)
            if not open_result.success:
                logger.warning("打开页面失败 %s: %s", url, open_result.error)
                continue

            content = await self.browser.extract_content()
            if content.success and content.output.strip():
                urls_collected += 1
            else:
                logger.warning("提取内容失败 %s: %s", url, content.error)

        return CollectResult(
            success=True,
            urls_scanned=urls_scanned,
            urls_collected=urls_collected,
        )

    async def check_captcha(self, screenshot_path: str) -> bool:
        anomaly = await self.screener.detect_page_anomaly(screenshot_path)
        if anomaly and anomaly.get("type") in ("captcha", "robot_detection"):
            return True
        return False
