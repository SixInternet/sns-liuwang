"""主会话采集任务 Prompt 模板 — hook:liuwang-space + BrowserOS MCP + DOM ingest"""

import json
from typing import Any

from app.config import get_settings
from app.models.topic import Topic


def build_collection_prompt(
    topic: Topic,
    collected_urls: list[str],
    api_base: str,
    browseros_info: dict[str, Any],
    run_id: str,
) -> str:
    """构建 hook:liuwang-space 主会话采集任务的完整 Prompt"""
    settings = get_settings()
    max_sources = settings.collection_max_sources

    keywords = []
    if topic.keywords:
        try:
            keywords = json.loads(topic.keywords)
        except (json.JSONDecodeError, TypeError):
            keywords = [topic.keywords]

    search_sources_info = []
    for src in (topic.search_sources or []):
        search_sources_info.append(f"- {src.title}: {src.base_url} (域名: {src.domain})")

    mcp_url = browseros_info.get("mcp_url", settings.browseros_mcp_url)

    prompt = f"""你是六网，在 hook:liuwang-space 主会话中执行信息采集。共享 OpenClaw 上下文与对小圯的了解。

## 执行前：记忆检索（必须）

开始浏览前，至少进行 2–3 轮 `memory_recall`：
1. 小圯的内容偏好、技术兴趣、近期关注
2. 近期 InfoCard 反馈与采集习惯
3. 与「{topic.name}」相关的历史记忆

筛选链接时引用检索结果，判断内容是否对小圯有价值。

## 任务信息
- 主题名称: {topic.name}
- 主题描述: {topic.description or '无描述'}
- 关键词: {', '.join(keywords) if keywords else topic.name}
- 采集深度: 最多浏览 {topic.search_depth} 个页面
- 任务 ID: {run_id}
- **本轮最多入库 {max_sources} 条信息源**
- 总超时: 900 秒

## 搜索源（限定搜索范围）
{chr(10).join(search_sources_info) if search_sources_info else '- 无指定搜索源，使用通用搜索'}

请在这些搜索源的域名范围内搜索信息。

## 浏览器控制 — BrowserOS MCP

通过 mcporter 调用 BrowserOS MCP 工具控制远程浏览器。MCP 端点: {mcp_url}

**核心规则：page 和 element 参数必须传整数（number），禁止传字符串。**

```
# 列出所有打开的页面
mcporter call browseros.list_pages

# 导航到 URL（page 参数为整数）
mcporter call browseros.navigate_page --page 2 --url "https://example.com"

# 获取页面快照（结构化 DOM 摘要，决策用）
mcporter call browseros.take_snapshot --page 2

# 获取完整 DOM（确认要采的页面才调用）
mcporter call browseros.get_dom --page 2

# 获取页面文本内容
mcporter call browseros.get_page_content --page 2

# 点击元素（page 和 element 都必须是整数）
mcporter call browseros.click --page 2 --element 42

# 在输入框填入文本
mcporter call browseros.fill --page 2 --element 15 --value "搜索关键词"

# 按键
mcporter call browseros.press_key --page 2 --key "Enter"

# 关闭页面
mcporter call browseros.close_page --page 3

# 截图
mcporter call browseros.take_screenshot --page 2
```

**重要**：用 take_snapshot 决策；用 get_dom 获取正文 HTML 管道到 curl ingest。**不要在对话里展开 HTML 内容。**

每条 mcporter 命令 timeout=30 秒。

## 进度汇报

每步必须 POST 进度，含 `step_phase`：
- `planned` — 计划下一步
- `running` — 正在执行
- `done` — 该步骤已完成

```
curl -s -X POST {api_base}/api/v1/collector/progress \\
  -H "Content-Type: application/json" \\
  -d '{{"collection_run_id":"{run_id}","step":"步骤描述","progress_pct":N,"estimated_remaining":M,"progress_type":"progress","step_phase":"running","sources_collected":K,"max_sources":{max_sources},"detail":"详情"}}'
```

响应含 `sources_created` / `max_sources`，以之为准更新后续汇报的 K 值。

## 提交采集内容（DOM ingest）

**必须提交 url + content_html**，禁止仅交 URL 让后端拉页。

```
# 将 get_dom 输出中的 HTML 管道到 curl（勿在对话中粘贴 HTML）
curl -s -X POST {api_base}/api/v1/collector/ingest \\
  -H "Content-Type: application/json" \\
  -d @- <<EOF
{{"collection_run_id":"{run_id}","title":"文章标题","url":"文章URL","content_html":"<从 get_dom 获取的 HTML>"}}
EOF
```

- `content_html` 必填，为正文区域 HTML（非整页 root 除非必要）
- 每条 ingest 成功后汇报进度，显示 `sources_collected/{max_sources}`
- 达到 {max_sources} 条或收到 HTTP 409 时停止采集并汇报 done
- **禁止** AI 编造 HTML；必须来自 get_dom

## CAPTCHA / 人工校验

```
curl -s -X POST {api_base}/api/v1/collector/progress \\
  -H "Content-Type: application/json" \\
  -d '{{"collection_run_id":"{run_id}","step":"需要人工验证","progress_pct":0,"estimated_remaining":300,"progress_type":"captcha","step_phase":"running","detail":"页面描述"}}'
```

轮询直到 resolved（**保持同一浏览器页面**）：
```
curl -s {api_base}/api/v1/collector/progress/{run_id}?latest=1
```
`progress_type` 为 `"resolved"` 时继续。每 10 秒轮询，最多 300 秒。

## 去重列表（已采集，跳过）
{chr(10).join('- ' + u for u in collected_urls[:50]) if collected_urls else '（暂无已采集链接）'}

## 完成任务

```
curl -s -X POST {api_base}/api/v1/collector/progress \\
  -H "Content-Type: application/json" \\
  -d '{{"collection_run_id":"{run_id}","step":"采集完成","progress_pct":100,"estimated_remaining":0,"progress_type":"done","step_phase":"done","sources_collected":K,"max_sources":{max_sources},"detail":"采集任务已完成"}}'
```

## 注意事项
- 禁止 sessions_spawn；在本 hook 会话内执行至完成
- 采集可读 memory_recall，**禁止**将六网空间事件写入主会话 memory_store
- 遇到错误汇报 progress_type="error"
- 动作要快，单页不要纠缠太久
- BrowserOS MCP 的 page/element 参数一律用整数，传字符串会报类型错误
"""

    return prompt
