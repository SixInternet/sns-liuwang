import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { resolveErrorMessage } from '../lib/error'
import { useToast } from '../context/ToastContext'
import type {
  CollectionRun,
  CollectionRunListResponse,
  CollectionProgress,
  ProgressTimelineResponse,
} from '../types'

const POLL_INTERVAL_MS = 2000

const ACTIVE_RUN_STATUSES = new Set([
  'in_progress',
  'agent_pending',
  'pending_agent',
])

const RUN_STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-700 border-gray-200',
  in_progress: 'bg-blue-100 text-blue-800 border-blue-200',
  agent_pending: 'bg-blue-100 text-blue-800 border-blue-200',
  pending_agent: 'bg-blue-100 text-blue-800 border-blue-200',
  completed: 'bg-green-100 text-green-800 border-green-200',
  failed: 'bg-red-100 text-red-800 border-red-200',
  cancelled: 'bg-yellow-100 text-yellow-800 border-yellow-200',
}

const RUN_STATUS_LABELS: Record<string, string> = {
  pending: '待执行',
  in_progress: '执行中',
  agent_pending: '等待智能体',
  pending_agent: '等待智能体',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
}

const STEP_PHASE_ICONS: Record<string, string> = {
  planned: '○',
  running: '●',
  done: '✓',
}

function formatTime(iso: string | null | undefined): string {
  if (!iso) return '-'
  try {
    return new Intl.DateTimeFormat('zh-CN', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(new Date(iso))
  } catch {
    return iso
  }
}

function ProgressBar({ pct }: { pct: number }) {
  const clamped = Math.max(0, Math.min(100, pct))
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
      <div
        className="h-full rounded-full bg-gray-900 transition-all duration-500"
        style={{ width: `${clamped}%` }}
      />
    </div>
  )
}

function StepPhaseIcon({ phase }: { phase?: string | null }) {
  const icon = STEP_PHASE_ICONS[phase ?? 'running'] ?? '●'
  const isRunning = phase === 'running'
  return (
    <span
      className={`inline-flex h-5 w-5 shrink-0 items-center justify-center text-xs font-bold ${
        isRunning ? 'text-blue-600 animate-pulse' : 'text-gray-500'
      }`}
      title={phase ?? 'running'}
    >
      {icon}
    </span>
  )
}

function CaptchaCard({
  runId,
  onAction,
}: {
  runId: string
  onAction: (runId: string, action: 'resolve' | 'cancel') => void
}) {
  const [busy, setBusy] = useState<'resolve' | 'cancel' | null>(null)

  const handleClick = async (action: 'resolve' | 'cancel') => {
    setBusy(action)
    onAction(runId, action)
    setBusy(null)
  }

  return (
    <div className="mt-3 rounded-xl border border-yellow-300 bg-yellow-50 p-4">
      <div className="mb-2 flex items-center gap-2">
        <span className="text-lg">⚠️</span>
        <span className="text-sm font-semibold text-yellow-800">
          CAPTCHA 验证码拦截
        </span>
      </div>
      <p className="mb-3 text-xs text-yellow-700">
        采集任务遇到验证码，请在浏览器中手动处理后点击「已解决」。
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => handleClick('resolve')}
          disabled={!!busy}
          className="rounded-lg bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
        >
          {busy === 'resolve' ? '处理中…' : '✅ 已解决'}
        </button>
        <button
          type="button"
          onClick={() => handleClick('cancel')}
          disabled={!!busy}
          className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
        >
          {busy === 'cancel' ? '处理中…' : '❌ 取消任务'}
        </button>
      </div>
    </div>
  )
}

function TimelineView({
  items,
  sourcesCreated,
  maxSources,
  latestPct,
  showCaptcha,
  runId,
  onCaptchaAction,
}: {
  items: CollectionProgress[]
  sourcesCreated: number
  maxSources: number
  latestPct: number
  showCaptcha: boolean
  runId: string
  onCaptchaAction: (runId: string, action: 'resolve' | 'cancel') => void
}) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between text-xs text-gray-600">
        <span>已采集 {sourcesCreated}/{maxSources} 条</span>
        <span>{latestPct}%</span>
      </div>
      <ProgressBar pct={latestPct} />

      <ul className="mt-1 flex flex-col gap-2 border-l-2 border-gray-200 pl-3">
        {items.map((item) => {
          const isRunning = item.step_phase === 'running'
          return (
            <li
              key={item.id}
              className={`relative text-sm ${
                isRunning ? 'font-medium text-blue-800' : 'text-gray-700'
              }`}
            >
              <div className="flex items-start gap-2">
                <StepPhaseIcon phase={item.step_phase} />
                <div className="min-w-0 flex-1">
                  <p>{item.step}</p>
                  <div className="mt-0.5 flex flex-wrap gap-x-2 text-xs text-gray-400">
                    <span>{formatTime(item.created_at)}</span>
                    {item.progress_type !== 'progress' ? (
                      <span className="uppercase">{item.progress_type}</span>
                    ) : null}
                    {item.sources_collected != null ? (
                      <span>{item.sources_collected}/{item.max_sources ?? maxSources}</span>
                    ) : null}
                  </div>
                  {item.detail ? (
                    <p className="mt-1 text-xs text-gray-500 line-clamp-2">{item.detail}</p>
                  ) : null}
                </div>
              </div>
            </li>
          )
        })}
      </ul>

      {showCaptcha ? (
        <CaptchaCard runId={runId} onAction={onCaptchaAction} />
      ) : null}
    </div>
  )
}

export function CollectionMonitorPage() {
  const toast = useToast()
  const [runs, setRuns] = useState<CollectionRun[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [timelineMap, setTimelineMap] = useState<Record<string, ProgressTimelineResponse>>({})
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const loadRuns = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get('collection-runs/').json<CollectionRunListResponse>()
      setRuns(data.items)
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
      setRuns([])
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    loadRuns()
  }, [loadRuns])

  const fetchTimeline = useCallback(async (runId: string) => {
    try {
      const data = await api
        .get(`collector/progress/${runId}`)
        .json<ProgressTimelineResponse>()
      setTimelineMap((prev) => ({ ...prev, [runId]: data }))
    } catch {
      // silent — progress may not exist yet
    }
  }, [])

  useEffect(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }

    const activeRunIds = runs
      .filter((r) => ACTIVE_RUN_STATUSES.has(r.status))
      .map((r) => r.id)

    if (activeRunIds.length === 0) return

    const poll = () => {
      for (const id of activeRunIds) {
        fetchTimeline(id)
      }
    }

    poll()
    pollRef.current = setInterval(poll, POLL_INTERVAL_MS)

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [runs, fetchTimeline])

  useEffect(() => {
    if (!expandedId) return
    fetchTimeline(expandedId)
  }, [expandedId, fetchTimeline])

  const handleCaptchaAction = async (runId: string, action: 'resolve' | 'cancel') => {
    try {
      await api.post(`collector/progress/${runId}/${action}`)
      toast.success(action === 'resolve' ? '已标记解决' : '任务已取消')
      await fetchTimeline(runId)
      await loadRuns()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    }
  }

  const handleTriggerCollection = async () => {
    try {
      await api.post('scheduler/sync')
      toast.success('已触发采集调度')
      await loadRuns()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    }
  }

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id))
  }

  return (
    <div className="relative pb-24">
      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-gray-800">采集监控</h2>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleTriggerCollection}
            className="shrink-0 rounded-lg bg-gray-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-800"
          >
            触发采集
          </button>
          <button
            type="button"
            onClick={() => loadRuns()}
            disabled={loading}
            className="shrink-0 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {loading ? '刷新中…' : '刷新'}
          </button>
        </div>
      </div>

      {!loading && runs.length > 0 && (
        <p className="mb-3 text-xs text-gray-400">
          共 {runs.length} 条记录
        </p>
      )}

      {loading && runs.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-sm text-gray-400">加载中…</p>
        </div>
      ) : !loading && runs.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-sm text-gray-500">暂无采集记录</p>
        </div>
      ) : (
        <ul className="flex flex-col gap-3">
          {runs.map((run) => {
            const isExpanded = expandedId === run.id
            const timeline = timelineMap[run.id]
            const isActive = ACTIVE_RUN_STATUSES.has(run.status)
            const items = timeline?.items ?? []
            const latest = items.length > 0 ? items[items.length - 1] : null
            const latestPct = latest?.progress_pct ?? 0
            const sourcesCreated = timeline?.sources_created ?? 0
            const maxSources = timeline?.max_sources ?? 10
            const showCaptcha = latest?.progress_type === 'captcha'

            return (
              <li key={run.id}>
                <article className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
                  <button
                    type="button"
                    onClick={() => toggleExpand(run.id)}
                    className="w-full p-4 text-left flex items-start justify-between gap-2 hover:bg-gray-50 transition-colors"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <h3 className="text-sm font-semibold text-gray-900">
                          {run.topic_name ?? '未知主题'}
                        </h3>
                        <span
                          className={`inline-flex shrink-0 rounded-full border px-2 py-0.5 text-xs font-medium ${
                            RUN_STATUS_COLORS[run.status] ?? 'bg-gray-100 text-gray-600 border-gray-200'
                          }`}
                        >
                          {RUN_STATUS_LABELS[run.status] ?? run.status}
                        </span>
                        {isActive && timeline ? (
                          <span className="text-xs text-gray-500">
                            {sourcesCreated}/{maxSources}
                          </span>
                        ) : null}
                      </div>
                      <div className="flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-gray-500">
                        <span>开始：{formatTime(run.started_at)}</span>
                        <span>结束：{formatTime(run.finished_at)}</span>
                      </div>
                    </div>
                    <span className="shrink-0 text-gray-400 text-lg">
                      {isExpanded ? '▾' : '▸'}
                    </span>
                  </button>

                  {isExpanded ? (
                    <div className="border-t border-gray-100 px-4 py-4">
                      {items.length > 0 ? (
                        <TimelineView
                          items={items}
                          sourcesCreated={sourcesCreated}
                          maxSources={maxSources}
                          latestPct={latestPct}
                          showCaptcha={!!showCaptcha && isActive}
                          runId={run.id}
                          onCaptchaAction={handleCaptchaAction}
                        />
                      ) : isActive ? (
                        <p className="text-sm text-gray-400">等待进度数据…</p>
                      ) : run.status === 'completed' ? (
                        <p className="text-sm text-gray-500">
                          采集已完成，请到「信息来源」查看新记录。
                        </p>
                      ) : (
                        <p className="text-sm text-gray-400">无进度详情</p>
                      )}
                    </div>
                  ) : null}
                </article>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
