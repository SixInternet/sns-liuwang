"""AI Sub-Agent 采集任务 Prompt 模板"""

import json
from typing import Any

from app.models.topic import Topic


def build_sub_agent_prompt(
    topic: Topic,
    collected_urls: list[str],
    api_base: str,
    cdp_info: dict[str, Any],
    run_id: str,
) -> str:
    """构建 Sub-Agent 采集任务的完整 Prompt"""

    keywords = []
    if topic.keywords:
        try:
            keywords = json.loads(topic.keywords)
        except (json.JSONDecodeError, TypeError):
            keywords = [topic.keywords]

    search_sources_info = []
    for src in (topic.search_sources or []):
        search_sources_info.append(f"- {src.title}: {src.base_url} (域名: {src.domain})")

    base_url = f"http://{cdp_info.get('host', 'localhost')}:{cdp_info.get('port', 9333)}"

    prompt = f"""你是一个 AI 信息采集代理。你的任务是采集关于「{topic.name}」的信息。

## 任务信息
- 主题名称: {topic.name}
- 主题描述: {topic.description or '无描述'}
- 关键词: {', '.join(keywords) if keywords else topic.name}
- 采集深度: 最多浏览 {topic.search_depth} 个页面
- 任务 ID: {run_id}
- 总超时: 900 秒

## 搜索源
{chr(10).join(search_sources_info) if search_sources_info else '- 无指定搜索源，使用通用搜索'}

## 浏览器控制
浏览器在 Windows 端 (10.1.0.60:9333)，agent-browser 已安装。
由于每条 exec 是新进程，connect 不能跨命令保留，每步都要链式操作。

采集页面完整 HTML（核心操作）：
```
agent-browser connect {base_url} && agent-browser open "https://目标网址" && sleep 3 && agent-browser eval "document.documentElement.outerHTML" 2>&1
```

每条 exec 设 timeout=30。

浏览搜索结果（用 snapshot 看页面结构）：
```
agent-browser connect {base_url} && agent-browser snapshot -i 2>&1
```

点击元素：
```
agent-browser connect {base_url} && agent-browser click @e3 2>&1
```

## 采集策略
1. 打开搜索源 URL（搜索词直接拼在 URL 里），用 snapshot 看结果
2. 挑与主题相关的链接，对比已采集列表跳过重复
3. 打开每个新链接 → 用 eval 获取完整 outerHTML → 提交 ingest
4. **不要自己总结** 提交的 content_raw 必须是 eval 返回的完整 HTML

## 进度汇报
exec: curl -s -X POST {api_base}/api/v1/collector/progress -H "Content-Type: application/json" -d '{{"collection_run_id":"{run_id}","step":"步骤描述","progress_pct":N,"estimated_remaining":M,"progress_type":"progress","detail":"详情"}}'
timeout=5

进度参考：连接 5% → 搜索完成 15% → 浏览结果页 20-40% → 每篇文章加 10%

## CAPTCHA / 人工验证
如果遇到验证码：
exec: curl -s -X POST {api_base}/api/v1/collector/progress -H "Content-Type: application/json" -d '{{"collection_run_id":"{run_id}","step":"等待人工验证","progress_pct":0,"estimated_remaining":300,"progress_type":"captcha","detail":"需要人工验证"}}'
timeout=5
然后每 10 秒查：curl -s {api_base}/api/v1/collector/progress/{run_id}?latest=1

## 提交内容（重要：必须提交完整 outerHTML，不能总结）
exec: curl -s -X POST {api_base}/api/v1/collector/ingest -H "Content-Type: application/json" -d '{{"collection_run_id":"{run_id}","title":"文章标题","url":"文章URL","content_raw":"完整的 outerHTML 内容，DOM 全部保留，不要删减"}}'
timeout=10

content_raw 字段必须放 eval 返回的完整 outerHTML。

## 完成任务
exec: curl -s -X POST {api_base}/api/v1/collector/progress -H "Content-Type: application/json" -d '{{"collection_run_id":"{run_id}","step":"采集完成","progress_pct":100,"estimated_remaining":0,"progress_type":"done","detail":"采集任务已完成"}}'
timeout=5

## 去重列表
{chr(10).join('- ' + u for u in collected_urls[:50]) if collected_urls else '暂无已采集链接'}

## 注意事项
- exec timeout: 浏览器操作 30s，curl 5-10s
- 遇到错误汇报 type="error"
- 只采集相关有用内容，跳过广告
- 不要用自己的语言总结，直接提交 outerHTML
- 动作要快
"""

    return prompt
