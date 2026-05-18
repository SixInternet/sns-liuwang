"""截图筛选器 — 通过 GLM-5V (mcporter) 分析网页截图"""

import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class Screener:
    def __init__(self, mcporter_base: str = "mcporter"):
        self.mcporter_base = mcporter_base

    async def _call_vision(
        self, image_path: str, prompt: str, timeout: int = 60
    ) -> dict | None:
        args = [
            self.mcporter_base,
            "vision",
            "--image", image_path,
            "--prompt", prompt,
            "--format", "json",
        ]
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            logger.error("mcporter vision 调用超时 (%ds)", timeout)
            return None

        output = stdout.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            error = stderr.decode("utf-8", errors="replace")
            logger.error("mcporter vision 失败: %s", error or output)
            return None

        try:
            return json.loads(output)
        except json.JSONDecodeError:
            logger.warning("mcporter 返回非 JSON 内容，尝试原始文本解析")
            return {"raw": output}

    async def analyze_search_results(
        self, screenshot_path: str, keywords: list[str]
    ) -> list[dict]:
        prompt = (
            "分析这张搜索结果页面的截图。"
            f"搜索关键词为: {', '.join(keywords)}\n"
            "请返回一个 JSON 数组，每个元素包含:\n"
            '- "title": 搜索结果标题\n'
            '- "url": 搜索结果链接（如可见）\n'
            '- "reason": 为什么这个结果值得点击阅读\n'
            "只返回与关键词高度相关、内容质量高的结果。"
            "如果无法识别任何结果，返回空数组 []。"
        )
        result = await self._call_vision(screenshot_path, prompt)
        if result is None:
            return []
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "raw" in result:
            return []
        return result.get("results", [])

    async def detect_page_anomaly(self, screenshot_path: str) -> dict | None:
        prompt = (
            "检查这张网页截图是否存在以下异常情况:\n"
            "1. 登录框/注册弹窗遮挡主要内容\n"
            "2. 验证码 (CAPTCHA) 检测\n"
            "3. 机器人检测/人机验证页面\n"
            "4. 403/404/503 等错误页面\n"
            "5. 付费墙/订阅提示遮挡内容\n"
            "6. 地区限制提示\n"
            "如果检测到异常，返回 JSON: "
            '{"anomaly": true, "type": "类型", "description": "描述"}\n'
            "如果页面正常，返回: "
            '{"anomaly": false}'
        )
        result = await self._call_vision(screenshot_path, prompt)
        if result is None:
            return {"anomaly": True, "type": "unknown", "description": "截图分析失败"}
        if isinstance(result, dict) and result.get("anomaly"):
            return result
        return None

    async def extract_page_summary(
        self, screenshot_path: str, content: str
    ) -> dict:
        prompt = (
            "基于以下网页截图和文本内容，提取关键信息摘要。\n"
            "返回 JSON:\n"
            '- "title": 文章/页面标题\n'
            '- "summary": 100-200字的中文摘要\n'
            '- "key_points": 关键要点列表（字符串数组）\n'
            '- "topics": 涉及的主题标签（字符串数组）\n\n'
            f"页面文本内容:\n{content[:3000]}"
        )
        result = await self._call_vision(screenshot_path, prompt, timeout=90)
        if result is None:
            return {
                "title": "",
                "summary": "摘要提取失败",
                "key_points": [],
                "topics": [],
            }
        return result
