"""浏览器适配器 — DEPRECATED: 已迁移到 BrowserOS MCP (mcporter + browseros.*) 控制。

此文件仅保留向后兼容，新采集流程使用 collection_prompt.py 中的 BrowserOS MCP 指令。
参见 agent_session.py 中的 spawn_collection 函数。
"""

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

    # opendevbrowser connect --host --cdp-port
    def _is_remote(self) -> bool:
        return bool(self.cdp_host and self.cdp_host not in ("localhost", "127.0.0.1", ""))

    def _agent_cmd(self) -> list[str]:
        if self.profile:
            return ["npx", "opendevbrowser", "launch", "--profile", self.profile]
        elif self._is_remote():
            return ["npx", "opendevbrowser", "connect", "--host", self.cdp_host, "--cdp-port", str(self.cdp_port)]
        else:
            return ["npx", "opendevbrowser", "launch", "--no-extension", "--cdp", str(self.cdp_port)]

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
        # opendevbrowser 的 screenshot 可能输出到 stdout
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


