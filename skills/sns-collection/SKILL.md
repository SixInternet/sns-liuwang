---
name: sns-collection
description: SNS 信息采集 SOP：hook:liuwang-space 主会话内 CDP 连接、浏览筛选、DOM ingest、进度回传与 CAPTCHA 续跑
metadata:
  openclaw:
    requires:
      bins: ["curl", "opendevbrowser"]
---

# sns-collection

SNS 后端触发 `[COLLECTION_TASK]` 后，在 **hook:liuwang-space 主会话**内执行信息采集。禁止 `sessions_spawn`。

## 前置

1. 从任务消息读取 `Run ID`、`Topic`、API base、CDP host/port
2. `memory_recall` 至少 2–3 轮（偏好、技术兴趣、近期反馈）
3. 确认 `opendevbrowser` 可用

## 标准流程

### 1. 连接浏览器

```bash
opendevbrowser connect --host <cdp_host> --cdp-port <cdp_port> --output-format json
```

汇报进度（planned → running）：

```bash
curl -s -X POST <api_base>/api/v1/collector/progress \
  -H "Content-Type: application/json" \
  -d '{"collection_run_id":"<run_id>","step":"连接远程浏览器","progress_pct":5,"progress_type":"progress","step_phase":"running","sources_collected":0,"max_sources":10}'
```

### 2. 搜索与浏览

- 在搜索源域名内构造搜索 URL，`goto` 打开
- `snapshot` 浏览结果，结合 memory 筛选值得采集的链接
- 每步汇报 `step_phase`: `planned`（计划）→ `running`（执行中）→ `done`（完成）

### 3. 采集单条（DOM ingest）

```bash
# 1. snapshot 定位正文 ref
opendevbrowser snapshot --session-id <sid> --output-format json

# 2. 取正文 outerHTML（勿在对话中展开）
HTML=$(opendevbrowser dom-get-html --session-id <sid> --ref <ref> --output-format json | jq -r '.html')

# 3. ingest
curl -s -X POST <api_base>/api/v1/collector/ingest \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg rid "<run_id>" --arg title "标题" --arg url "https://..." --arg html "$HTML" \
    '{collection_run_id:$rid,title:$title,url:$url,content_html:$html}')"
```

- 响应含 `sources_created` / `max_sources`
- 达到 10 条或 HTTP 409 → 停止采集

### 4. CAPTCHA 续跑

```bash
# 上报
curl -s -X POST <api_base>/api/v1/collector/progress \
  -H "Content-Type: application/json" \
  -d '{"collection_run_id":"<run_id>","step":"需要人工验证","progress_pct":0,"progress_type":"captcha","step_phase":"running","detail":"描述"}'

# 轮询（每 10s，最多 300s）— 保持同一 browser session
curl -s "<api_base>/api/v1/collector/progress/<run_id>?latest=1"
# progress_type == "resolved" 时继续
```

用户在前端点「已解决」后写入 `resolved` 记录。

### 5. 完成

```bash
curl -s -X POST <api_base>/api/v1/collector/progress \
  -H "Content-Type: application/json" \
  -d '{"collection_run_id":"<run_id>","step":"采集完成","progress_pct":100,"progress_type":"done","step_phase":"done","sources_collected":N,"max_sources":10}'
```

## 约束

| 项 | 规则 |
|----|------|
| 上限 | 最多 10 条信息源 |
| HTML | content_html 来自 dom-get-html，禁止 AI 编造 |
| 体积 | content_html 约 2MB 上限，超限 413 |
| 记忆 | 可读 memory_recall；禁止将六网空间事件写入主会话 memory_store |
| 超时 | 总任务 900s；单条 opendevbrowser 命令 30s |

## 辅助脚本

```bash
sns-collection progress <api_base> <run_id> '<json>'
sns-collection ingest <api_base> '<json>'
sns-collection poll-resolved <api_base> <run_id>
```
