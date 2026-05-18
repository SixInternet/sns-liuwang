"""浏览器适配器 — 通过 agent-browser-stealth CLI 控制无头浏览器"""

import asyncio
import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BrowserResult:
    success: bool = False
    output: str = ""
    error: str = ""
    screenshot_path: str | None = None
    extra: dict | None = None


class BrowserAdapter:
    def __init__(
        self,
        cdp_host: str | None = None,
        cdp_port: int | None = None,
        profile: str | None = None,
    ):
        from app.config import get_settings
        _cfg = get_settings()
        cdp_host = cdp_host or _cfg.cdp_host
        cdp_port = cdp_port or _cfg.cdp_port
        self.cdp_host = cdp_host
        self.cdp_port = cdp_port
        self.profile = profile

    def _is_remote(self) -> bool:
        return bool(self.cdp_host and self.cdp_host not in ("localhost", "127.0.0.1", ""))

    def _agent_cmd(self) -> list[str]:
        if self.profile:
            return ["npx", "agent-browser-stealth", "--profile", self.profile]
        elif self._is_remote():
            return ["npx", "agent-browser-stealth", "connect", f"http://{self.cdp_host}:{self.cdp_port}"]
        else:
            return ["npx", "agent-browser-stealth", "--cdp", str(self.cdp_port)]

    async def _run(self, cmd_args: list[str], timeout: int = 30) -> BrowserResult:
        args = self._agent_cmd() + cmd_args
        logger.debug("执行: %s", " ".join(args))
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return BrowserResult(success=False, error=f"操作超时 ({timeout}s)")

        output = stdout.decode("utf-8", errors="replace")
        error = stderr.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            return BrowserResult(success=False, error=error or output)
        return BrowserResult(success=True, output=output, error=error)

    async def _run_chain(self, commands: list[list[str]], timeout: int = 60) -> BrowserResult:
        """在远程模式下，将多个命令链式执行，保留 daemon 页面状态
        返回最后一个命令的结果（extract 的内容在 output 中）"""
        import shlex
        base = self._agent_cmd()
        chain = " && ".join(
            " ".join(shlex.quote(w) for w in base + cmd)
            for cmd in commands
        )
        logger.debug("链式执行 %d 条命令", len(commands))
        proc = await asyncio.create_subprocess_exec(
            "bash", "-c", chain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return BrowserResult(success=False, error=f"链式操作超时 ({timeout}s)")

        output = stdout.decode("utf-8", errors="replace")
        error = stderr.decode("utf-8", errors="replace")
        ok = proc.returncode == 0
        # 提取最后一个命令的实际输出（去掉 "✓ Done" 标记行）
        lines = [l for l in output.split("\n") if l.strip() and "Done" not in l]
        content = "\n".join(lines) if lines else output
        return BrowserResult(success=ok, output=content, error=error)

    async def open_url(self, url: str, wait_ms: int = 3000) -> BrowserResult:
        if self._is_remote():
            return await self._run_chain([
                ["open", url],
                ["wait", str(wait_ms)],
            ])
        result = await self._run(["open", url])
        if not result.success:
            return result
        return await self._run(["wait", str(wait_ms)])

    async def snapshot(self) -> BrowserResult:
        return await self._run(["snapshot"])

    async def screenshot(self, output_path: str | None = None) -> BrowserResult:
        if output_path is None:
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.close()
            output_path = tmp.name
        # agent-browser-stealth 的 screenshot 可能输出到 stdout
        args = self._agent_cmd() + ["screenshot"]
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return BrowserResult(success=False, error=f"截图超时")
        if proc.returncode != 0:
            err = stderr.decode("utf-8", errors="replace")
            return BrowserResult(success=False, error=err or "截图失败")
        # 写 stdout 到文件（PNG 数据在 stdout 里）
        if len(stdout) > 100:
            with open(output_path, "wb") as f:
                f.write(stdout)
        else:
            # 尝试用 --screenshot-dir 环境变量
            with open(output_path, "wb") as f:
                f.write(stdout)
        if Path(output_path).stat().st_size > 100:
            return BrowserResult(success=True, screenshot_path=output_path)
        return BrowserResult(success=False, error=f"截图文件过小: {Path(output_path).stat().st_size} bytes")

    async def click(self, selector: str) -> BrowserResult:
        return await self._run(["click", selector])

    async def fill(self, selector: str, text: str) -> BrowserResult:
        return await self._run(["fill", selector, text])

    async def press(self, key: str) -> BrowserResult:
        return await self._run(["press", key])

    async def get_text(self, selector: str) -> BrowserResult:
        return await self._run(["get", "text", selector])

    async def extract_content(self) -> BrowserResult:
        return await self._run(["extract"])

    async def search_and_get_results(
        self, url: str, keyword: str, wait_ms: int = 5000
    ) -> BrowserResult:
        if self._is_remote():
            return await self._run_chain([
                ["open", url],
                ["wait", "2000"],
                ["fill", "@search", keyword],
                ["press", "Enter"],
                ["wait", str(wait_ms)],
            ])

        open_result = await self.open_url(url, wait_ms=2000)
        if not open_result.success:
            return open_result

        fill_result = await self.fill("@search", keyword)
        if not fill_result.success:
            return fill_result
        await self.press("Enter")
        return await self._run(["wait", str(wait_ms)])

    async def detect_anomaly(self, screenshot_path: str) -> BrowserResult:
        if not Path(screenshot_path).exists():
            return BrowserResult(
                success=False, error=f"截图文件不存在: {screenshot_path}"
            )
        return BrowserResult(
            success=True,
            output="",
            screenshot_path=screenshot_path,
        )

    async def evaluate_links(
        self, screenshot_path: str, keyword: str
    ) -> BrowserResult:
        if not Path(screenshot_path).exists():
            return BrowserResult(
                success=False, error=f"截图文件不存在: {screenshot_path}"
            )
        return BrowserResult(
            success=True,
            output="",
            screenshot_path=screenshot_path,
        )

    # ── CDP 原生操作（远程模式用） ──

    async def _cdp_request(self, msg: dict) -> dict:
        """发送 CDP 请求，返回结果"""
        import json as _json
        import websockets
        url = f"ws://{self.cdp_host}:{self.cdp_port}/devtools/browser/"
        async with websockets.connect(url, max_size=2**20) as ws:
            await ws.send(_json.dumps(msg))
            resp = await ws.recv()
            return _json.loads(resp)

    async def _cdp_get_page_content(self, url: str, wait_after_load: int = 3) -> BrowserResult:
        """通过 CDP 原生协议打开页面并获取内容
        返回: output=Markdown 文本, extra={"title": ..., "html": ..., "links": [...]}"""
        import json as _json
        import websockets
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                new_page = await client.put(f"http://{self.cdp_host}:{self.cdp_port}/json/new")
                if new_page.status_code != 200:
                    return BrowserResult(success=False, error=f"创建页面失败: {new_page.status_code}")
                page_info = new_page.json()
                page_ws = page_info.get("webSocketDebuggerUrl", "")
                if not page_ws:
                    return BrowserResult(success=False, error="无法获取页面 WebSocket URL")

            async with websockets.connect(page_ws, max_size=2**22) as ws:
                msg_id = 0

                async def cdp_req(method: str, params: dict | None = None) -> dict:
                    nonlocal msg_id
                    msg_id += 1
                    msg = {"id": msg_id, "method": method}
                    if params:
                        msg["params"] = params
                    await ws.send(_json.dumps(msg))
                    while True:
                        resp = _json.loads(await ws.recv())
                        if resp.get("id") == msg_id:
                            return resp

                await cdp_req("Page.enable")

                nav_result = await cdp_req("Page.navigate", {"url": url})
                if "error" in nav_result:
                    return BrowserResult(success=False, error=f"导航失败: {nav_result['error']}")

                await asyncio.sleep(wait_after_load)

                # 获取页面标题
                js_title = await cdp_req("Runtime.evaluate", {
                    "expression": "document.title || ''",
                    "returnByValue": True,
                })
                title = js_title.get("result", {}).get("result", {}).get("value", "") or ""

                # 获取完整 HTML
                js_html = await cdp_req("Runtime.evaluate", {
                    "expression": "document.documentElement.outerHTML",
                    "returnByValue": True,
                })
                html = js_html.get("result", {}).get("result", {}).get("value", "") or ""

                # 获取页面链接
                js_links = await cdp_req("Runtime.evaluate", {
                    "expression": "Array.from(document.querySelectorAll('a')).map(a => a.href).filter(h => h.startsWith('http')).join('\\n')",
                    "returnByValue": True,
                })
                links_str = js_links.get("result", {}).get("result", {}).get("value", "") or ""

            # 关闭页面
            try:
                page_id = page_info.get("id", "")
                if page_id:
                    async with httpx.AsyncClient() as client:
                        await client.delete(f"http://{self.cdp_host}:{self.cdp_port}/json/close/{page_id}")
            except Exception:
                pass

            if not html.strip():
                return BrowserResult(success=False, error="页面无内容")

            # 用 MarkItDown 将 HTML 转为 Markdown
            import tempfile
            from pathlib import Path
            from markitdown import MarkItDown
            tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
            tmp.write(html)
            tmp.close()
            try:
                md_result = MarkItDown().convert_local(tmp.name, url=url)
                markdown = md_result.text_content or ""
            except Exception:
                markdown = ""
            finally:
                Path(tmp.name).unlink(missing_ok=True)

            # 合并链接到 markdown 末尾
            links_list = [l.strip() for l in links_str.split("\n") if l.strip().startswith("http")]

            extra = {
                "title": title,
                "html": html,
                "links": links_list,
            }
            result = BrowserResult(success=bool(markdown.strip()), output=markdown.strip())
            result.extra = extra
            return result

        except Exception as e:
            return BrowserResult(success=False, error=f"CDP 操作失败: {e}")
