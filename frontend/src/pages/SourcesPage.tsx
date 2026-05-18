import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api } from '../lib/api'
import { resolveErrorMessage } from '../lib/error'
import { useToast } from '../context/ToastContext'
import { SourceSkeleton } from '../components/Skeleton'
import type { Source, SourcesGroupedResponse } from '../types'

const PAGE_SIZE = 5

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-700 border-gray-200',
  refined: 'bg-green-100 text-green-800 border-green-200',
  failed: 'bg-red-100 text-red-800 border-red-200',
}

const STATUS_LABELS: Record<string, string> = {
  pending: '待处理',
  refined: '已精炼',
  failed: '失败',
}

function formatTime(iso: string): string {
  try { return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(iso)) }
  catch { return iso }
}

function truncateText(text: string, max: number): string {
  if (text.length <= max) return text
  return text.slice(0, max) + '…'
}

/* ── 创建来源弹窗 ─────────────────────── */

type CreateSourcePayload = {
  title: string
  url?: string
  content_raw?: string
  collector?: string
}

type CreateSourceModalProps = {
  open: boolean
  submitting: boolean
  onClose: () => void
  onSubmit: (payload: CreateSourcePayload) => Promise<void>
}

function CreateSourceModal({ open, submitting, onClose, onSubmit }: CreateSourceModalProps) {
  const [title, setTitle] = useState('')
  const [url, setUrl] = useState('')
  const [contentRaw, setContentRaw] = useState('')
  const [collector, setCollector] = useState('')
  const [mode, setMode] = useState<'url' | 'manual'>('url')
  const [localError, setLocalError] = useState('')

  useEffect(() => {
    if (!open) { setTitle(''); setUrl(''); setContentRaw(''); setCollector(''); setMode('url'); setLocalError('') }
  }, [open])

  if (!open) return null

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLocalError('')
    const trimmedTitle = title.trim()
    if (!trimmedTitle) { setLocalError('请填写标题'); return }
    const payload: CreateSourcePayload = { title: trimmedTitle }
    if (mode === 'url') {
      const trimmedUrl = url.trim()
      if (!trimmedUrl) { setLocalError('URL 模式下请填写链接'); return }
      payload.url = trimmedUrl
    } else {
      const trimmedContent = contentRaw.trim()
      if (!trimmedContent) { setLocalError('手动模式下请填写内容'); return }
      payload.content_raw = trimmedContent
    }
    const trimmedCollector = collector.trim()
    if (trimmedCollector) payload.collector = trimmedCollector
    try { await onSubmit(payload) } catch (err: unknown) { setLocalError(await resolveErrorMessage(err)) }
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-end justify-center bg-black/40 p-4 sm:items-center"
      role="dialog" aria-modal="true" aria-labelledby="create-source-title"
      onMouseDown={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl" onMouseDown={(e) => e.stopPropagation()}>
        <h3 id="create-source-title" className="mb-4 text-lg font-semibold text-gray-900">添加信息来源</h3>
        <div className="mb-4 flex overflow-hidden rounded-lg border border-gray-300 text-sm">
          <button type="button" onClick={() => setMode('url')}
            className={`flex-1 px-3 py-1.5 transition-colors ${mode === 'url' ? 'bg-gray-900 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}>URL 模式</button>
          <button type="button" onClick={() => setMode('manual')}
            className={`flex-1 px-3 py-1.5 transition-colors ${mode === 'manual' ? 'bg-gray-900 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}>手动模式</button>
        </div>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {localError && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{localError}</div>}
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">标题</span>
            <input value={title} onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
              placeholder="必填" autoComplete="off" />
          </label>
          {mode === 'url' ? (
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-gray-700">链接</span>
              <input type="url" value={url} onChange={(e) => setUrl(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
                placeholder="https://" autoComplete="off" />
            </label>
          ) : (
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-gray-700">内容</span>
              <textarea value={contentRaw} onChange={(e) => setContentRaw(e.target.value)} rows={6}
                className="w-full resize-y rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
                placeholder="手动输入原始内容" />
            </label>
          )}
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">采集者</span>
            <input value={collector} onChange={(e) => setCollector(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
              placeholder="选填" autoComplete="off" />
          </label>
          <div className="mt-2 flex justify-end gap-2">
            <button type="button" onClick={onClose} disabled={submitting}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50">取消</button>
            <button type="submit" disabled={submitting}
              className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50">
              {submitting ? '提交中…' : '添加'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

/* ── 查看来源弹窗 ─────────────────────── */

function ViewSourceModal({ source, onClose }: { source: Source | null; onClose: () => void }) {
  if (!source) return null
  return (
    <div className="fixed inset-0 z-[100] flex items-end justify-center bg-black/40 p-4 sm:items-center"
      role="dialog" aria-modal="true"
      onMouseDown={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <div className="flex max-h-[80vh] w-full max-w-2xl flex-col rounded-2xl bg-white shadow-xl"
        onMouseDown={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-lg font-semibold text-gray-900">{source.title}</h3>
            {source.url && (
              <a href={source.url} target="_blank" rel="noopener noreferrer"
                className="mt-0.5 block truncate text-sm text-blue-600 underline decoration-blue-300 underline-offset-2 hover:text-blue-800">{source.url}</a>
            )}
          </div>
          <button type="button" onClick={onClose}
            className="ml-4 shrink-0 rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50">关闭</button>
        </div>
        <div className="overflow-y-auto px-6 py-4">
          {source.content_markdown ? (
            <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 p-4 text-sm leading-relaxed text-gray-800">{source.content_markdown}</pre>
          ) : <p className="py-8 text-center text-sm text-gray-400">暂无内容</p>}
          {source.diff_log && (
            <details className="mt-4">
              <summary className="cursor-pointer text-sm font-medium text-gray-600 hover:text-gray-800">变更记录</summary>
              <pre className="mt-2 whitespace-pre-wrap rounded-lg bg-amber-50 p-3 text-xs leading-relaxed text-amber-800">{source.diff_log}</pre>
            </details>
          )}
          <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 border-t border-gray-100 pt-3 text-xs text-gray-500">
            {source.collector && <span>采集者：{source.collector}</span>}
            <span>状态：{STATUS_LABELS[source.status] ?? source.status}</span>
            <span>卡片数：{source.card_count}</span>
            <span>采集于：{formatTime(source.collected_at)}</span>
            {source.refined_at && <span>精炼于：{formatTime(source.refined_at)}</span>}
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── 分组内 Source 条目 ─────────────────── */

function SourceItem({
  source, groupId, refiningId,
  onRefine, onView, onDelete,
}: {
  source: Source
  groupId: string
  refiningId: string | null
  onRefine: (id: string) => void
  onView: (s: Source) => void
  onDelete: (id: string, groupId: string) => void
}) {
  const isBusy = refiningId === source.id
  return (
    <li className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2.5">
      <div className="mb-1 flex items-start justify-between gap-2">
        <h4 className="min-w-0 flex-1 text-sm font-medium text-gray-900">{source.title}</h4>
        <span className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] leading-tight ${STATUS_COLORS[source.status] ?? 'bg-gray-100 text-gray-600 border-gray-200'}`}>
          {STATUS_LABELS[source.status] ?? source.status}
        </span>
      </div>
      {source.url && (
        <a href={source.url} target="_blank" rel="noopener noreferrer"
          className="mb-1 block truncate text-xs text-blue-600 underline decoration-blue-300 underline-offset-2 hover:text-blue-800">{source.url}</a>
      )}
      {source.content_markdown && (
        <p className="mb-1 whitespace-pre-wrap text-xs leading-relaxed text-gray-500">{truncateText(source.content_markdown, 80)}</p>
      )}
      <div className="flex flex-wrap items-center gap-x-3 text-[10px] text-gray-400">
        {source.collector && <span>采集者：{source.collector}</span>}
        <span>{source.card_count} 卡片</span>
        <span>{formatTime(source.collected_at)}</span>
      </div>
      <div className="mt-2 flex flex-wrap gap-1.5 border-t border-gray-100 pt-2">
        <button type="button" disabled={isBusy || source.status === 'refined'} onClick={() => onRefine(source.id)}
          className={`rounded-lg px-2 py-1 text-[11px] font-medium transition-colors ${
            source.status === 'refined'
              ? 'border border-green-200 bg-green-50 text-green-700'
              : 'border border-gray-200 bg-white text-gray-700 hover:bg-gray-100'
          } disabled:opacity-50`}>
          {isBusy ? '精炼中…' : source.status === 'refined' ? '已精炼' : '精炼'}
        </button>
        <button type="button" onClick={() => onView(source)}
          className="rounded-lg border border-gray-200 bg-white px-2 py-1 text-[11px] font-medium text-gray-700 hover:bg-gray-50">查看</button>
        <button type="button" disabled={isBusy} onClick={() => onDelete(source.id, groupId)}
          className="rounded-lg border border-red-200 bg-white px-2 py-1 text-[11px] font-medium text-red-600 hover:bg-red-50 disabled:opacity-50">删除</button>
      </div>
    </li>
  )
}

/* ── 分页控件 ──────────────────────────── */

function Pagination({ page, totalPages, onChange }: { page: number; totalPages: number; onChange: (p: number) => void }) {
  if (totalPages <= 1) return null
  return (
    <div className="mt-3 flex items-center justify-center gap-3 text-xs">
      <button onClick={() => onChange(page - 1)} disabled={page <= 1}
        className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40">上一页</button>
      <span className="text-gray-500">第 {page} / {totalPages} 页</span>
      <button onClick={() => onChange(page + 1)} disabled={page >= totalPages}
        className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40">下一页</button>
    </div>
  )
}

/* ── 主页面 ────────────────────────────── */

interface GroupState {
  expanded: boolean
  page: number
  allSources: Source[]
}

export function SourcesPage() {
  const toast = useToast()
  const [loading, setLoading] = useState(true)
  const [groupKeys, setGroupKeys] = useState<string[]>([])
  const [groupMap, setGroupMap] = useState<Record<string, { title: string; base_url: string; domain: string; total: number }>>({})
  const [uncatTotal, setUncatTotal] = useState(0)
  const [groupStates, setGroupStates] = useState<Record<string, GroupState>>({})
  const [uncatState, setUncatState] = useState<GroupState>({ expanded: false, page: 1, allSources: [] })
  const [modalOpen, setModalOpen] = useState(false)
  const [createSubmitting, setCreateSubmitting] = useState(false)
  const [refiningId, setRefiningId] = useState<string | null>(null)
  const [viewSource, setViewSource] = useState<Source | null>(null)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page_size: '100' })
      if (dateFrom) params.set('date_from', dateFrom)
      if (dateTo) params.set('date_to', dateTo)
      const data = await api.get(`sources/grouped?${params}`).json<SourcesGroupedResponse>()

      const keys: string[] = []
      const map: Record<string, { title: string; base_url: string; domain: string; total: number }> = {}
      const newStates: Record<string, GroupState> = {}

      for (const g of data.groups) {
        const key = g.search_source.id
        keys.push(key)
        map[key] = {
          title: g.search_source.title,
          base_url: g.search_source.base_url,
          domain: g.search_source.domain,
          total: g.total,
        }
        newStates[key] = {
          expanded: false,
          page: 1,
          allSources: g.sources,
        }
      }

      setGroupKeys(keys)
      setGroupMap(map)
      setGroupStates(newStates)
      setUncatTotal(data.uncategorized?.total ?? 0)
      setUncatState({ expanded: false, page: 1, allSources: data.uncategorized?.sources ?? [] })
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
      setGroupKeys([])
      setGroupMap({})
    } finally {
      setLoading(false)
    }
  }, [toast, dateFrom, dateTo])

  useEffect(() => { loadData() }, [loadData])

  const toggleGroup = (key: string) => {
    setGroupStates(prev => {
      const cur = prev[key]
      return { ...prev, [key]: { ...cur, expanded: !cur?.expanded, page: cur?.page ?? 1, allSources: cur?.allSources ?? [] } }
    })
  }

  const setGroupPage = (key: string, page: number) => {
    setGroupStates(prev => {
      const cur = prev[key]
      return { ...prev, [key]: { ...cur, page, expanded: true } }
    })
  }

  const toggleUncat = () => setUncatState(prev => ({ ...prev, expanded: !prev.expanded }))
  const setUncatPage = (page: number) => setUncatState(prev => ({ ...prev, page, expanded: true }))

  const handleRefine = async (id: string) => {
    setRefiningId(id)
    try {
      await api.post(`sources/${id}/refine`)
      toast.success('精炼成功')
      await loadData()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    } finally { setRefiningId(null) }
  }

  const handleDelete = async (id: string, _groupId: string) => {
    if (!window.confirm('确定删除此信息来源？')) return
    try {
      await api.delete(`sources/${id}`)
      toast.success('来源已删除')
      await loadData()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    }
  }

  const handleCreate = async (payload: CreateSourcePayload) => {
    setCreateSubmitting(true)
    try {
      await api.post('sources/', { json: payload })
      toast.success('来源添加成功')
      setModalOpen(false)
      await loadData()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    } finally { setCreateSubmitting(false) }
  }

  const renderGroup = (
    key: string,
    title: string,
    subtitle: string,
    total: number,
    state: GroupState,
    onToggle: () => void,
    onPageChange: (p: number) => void,
    dashed = false,
  ) => {
    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
    const start = (state.page - 1) * PAGE_SIZE
    const visibleSources = state.allSources.slice(start, start + PAGE_SIZE)

    return (
      <div className={`overflow-hidden rounded-xl border bg-white shadow-sm ${dashed ? 'border-dashed border-gray-300 bg-gray-50' : 'border-gray-200'}`}>
        <button onClick={onToggle}
          className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-gray-50 transition-colors">
          <div className="min-w-0 flex-1">
            <span className={`text-sm font-semibold ${dashed ? 'text-gray-600' : 'text-gray-900'}`}>{title}</span>
            <span className="ml-2 text-xs text-gray-400">{subtitle}</span>
          </div>
          <div className="ml-3 flex shrink-0 items-center gap-3">
            <span className="text-xs text-gray-400">{total} 条</span>
            <span className={`text-gray-400 transition-transform duration-200 ${state.expanded ? 'rotate-180' : ''}`}>▼</span>
          </div>
        </button>
        {state.expanded && (
          <div className="border-t border-gray-100 px-4 pb-4 pt-3">
            {visibleSources.length === 0 ? (
              <p className="py-4 text-center text-xs text-gray-400">暂无来源</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {visibleSources.map(s => (
                  <SourceItem key={s.id} source={s} groupId={key} refiningId={refiningId}
                    onRefine={handleRefine} onView={setViewSource} onDelete={handleDelete} />
                ))}
              </ul>
            )}
            <Pagination page={state.page} totalPages={totalPages} onChange={onPageChange} />
          </div>
        )}
      </div>
    )
  }

  const totalSources = groupKeys.reduce((acc, k) => acc + (groupMap[k]?.total ?? 0), 0) + uncatTotal

  return (
    <div className="relative pb-24">
      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-gray-800">信息来源</h2>
        <button onClick={() => loadData()} disabled={loading}
          className="shrink-0 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50">
          {loading ? '刷新中…' : '刷新'}
        </button>
      </div>

      <div className="mb-4 flex flex-wrap items-end gap-2 rounded-xl border border-gray-200 bg-white p-3 shadow-sm">
        <label className="flex flex-col gap-0.5">
          <span className="text-xs text-gray-500">开始日期</span>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
            className="rounded-lg border border-gray-300 px-2 py-1.5 text-xs outline-none ring-blue-500 focus:border-transparent focus:ring-2" />
        </label>
        <label className="flex flex-col gap-0.5">
          <span className="text-xs text-gray-500">结束日期</span>
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
            className="rounded-lg border border-gray-300 px-2 py-1.5 text-xs outline-none ring-blue-500 focus:border-transparent focus:ring-2" />
        </label>
        <button onClick={() => loadData()} disabled={loading}
          className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50">筛选</button>
        <button onClick={() => { setDateFrom(''); setDateTo('') }} disabled={loading}
          className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-500 hover:bg-gray-50 disabled:opacity-50">重置</button>
      </div>

      {!loading && totalSources > 0 && (
        <p className="mb-3 text-xs text-gray-400">
          共 {groupKeys.length} 个搜索源分组，{totalSources} 条来源
        </p>
      )}

      {loading && groupKeys.length === 0 ? (
        <div className="space-y-4">{Array.from({ length: 3 }).map((_, i) => <SourceSkeleton key={i} />)}</div>
      ) : !loading && totalSources === 0 ? (
        <div className="py-8 text-center">
          <p className="mb-4 text-sm text-gray-500">暂无信息来源，点击右下角「+」添加</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {groupKeys.map(key => {
            const meta = groupMap[key]
            if (!meta) return null
            const state = groupStates[key]
            return renderGroup(
              key, meta.title, meta.base_url, meta.total,
              state ?? { expanded: false, page: 1, allSources: [] },
              () => toggleGroup(key),
              (p) => setGroupPage(key, p),
            )
          })}

          {uncatTotal > 0 && renderGroup(
            '__uncat__', '未分类', '', uncatTotal,
            uncatState,
            toggleUncat,
            setUncatPage,
            true,
          )}
        </div>
      )}

      <button type="button" onClick={() => setModalOpen(true)} aria-label="添加信息来源"
        className="fixed bottom-6 right-4 z-[90] flex h-14 w-14 items-center justify-center rounded-full bg-gray-900 text-3xl leading-none text-white shadow-lg hover:bg-gray-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-900">
        +
      </button>

      <CreateSourceModal open={modalOpen} submitting={createSubmitting}
        onClose={() => !createSubmitting && setModalOpen(false)} onSubmit={handleCreate} />
      <ViewSourceModal source={viewSource} onClose={() => setViewSource(null)} />
    </div>
  )
}
