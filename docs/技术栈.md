# SNS 六网空间 — 技术栈

> 日期：2026-05-12 | 编制：六网

---

## 一、总览

```
┌──────────────────────────────────────────────┐
│          React PWA 前端（移动优先）             │
│  framer-motion 卡片流 / Tailwind CSS 界面       │
└──────────────────┬───────────────────────────┘
                   │ REST API / WebSocket
┌──────────────────▼───────────────────────────┐
│          Python FastAPI 后端                    │
│  SQLAlchemy 2.0 + asyncpg / httpx / APScheduler│
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│          PostgreSQL                            │
│  常规表 + JSONB + tsvector 全文检索             │
└──────────────────────────────────────────────┘
```

## 二、后端

| 维度 | 选型 | 理由 |
|------|------|------|
| 语言 | **Python 3.12+** | 三端采集系统（DroidRun、Agent S）同为 Python，同语言集成零摩擦；核心工作为 AI API 调用（I/O bound），非计算密集 |
| Web 框架 | **FastAPI** | 异步原生支持，Pydantic 天然匹配卡片数据结构，自动生成 OpenAPI 文档 |
| ORM | **SQLAlchemy 2.0 + asyncpg** | 异步 PostgreSQL 连接，查询语法成熟稳定 |
| API 客户端 | **httpx** | async HTTP，调 DeepSeek/GLM-5V API |
| 任务调度 | **APScheduler** | 定时采集任务调度，与 OpenClaw cron 互补 |
| 数据验证 | **Pydantic v2** | FastAPI 内置，卡片数据结构定义 |

## 三、数据库

| 维度 | 选型 | 理由 |
|------|------|------|
| 数据库 | **PostgreSQL 16+** | 方案文档指定，稳定可靠 |
| 全文检索 | **PostgreSQL tsvector** | 原生支持，无需额外引入 ElasticSearch |
| 灵活字段 | **JSONB** | 卡片数据结构可能迭代，JSONB 提供灵活性 |
| 异步驱动 | **asyncpg** | Python 异步生态最成熟的 PG 驱动 |
| 迁移工具 | **Alembic** | SQLAlchemy 官方迁移工具，配合 ORM 使用 |

## 四、前端

| 维度 | 选型 | 理由 |
|------|------|------|
| 框架 | **React 18 + TypeScript + Vite** | 生态最大，类型安全，和旧项目技术栈一致 |
| 卡片滑动 | **framer-motion** | 手势动画库，完美实现 Tinder 式卡片堆叠效果 |
| UI 样式 | **Tailwind CSS 4** | 快速搭界面，移动优先 PWA 不需要重型 UI 框架 |
| PWA | **vite-plugin-pwa** | 一行配置生成 Service Worker，离线可用 |
| HTTP 请求 | **ky** | 轻量 fetch 封装，比 axios 更小更现代 |
| 状态管理 | **React Query / TanStack Query** | 与服务端数据同步缓存 |

## 五、选型原则

1. **开发效率优先** — 单人项目，迭代速度是第一约束
2. **生态对齐** — 三端采集系统全为 Python，后端同语言减少集成摩擦
3. **够用就好** — 性能瓶颈在 AI API 延迟，不在语言和框架速度，不过度设计
4. **渐进增强** — 未来需要性能优化时，仅替换局部瓶颈（如 Rust 微服务），不动整体架构
