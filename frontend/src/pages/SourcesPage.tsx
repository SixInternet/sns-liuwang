import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api } from '../lib/api'
import { resolveErrorMessage } from '../lib/error'
import { useToast } from '../context/ToastContext'
import { SourceSkeleton } from '../components/Skeleton'
import type { Source, SourceListResponse } from '../types'

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
  try {
    return new Intl.DateTimeFormat('zh-CN', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(new Date(iso))
  } catch {
    return iso
  }
}

function truncateText(text: string, max: number): string {
  if (text.length <= max) return text
  return text.slice(0, max) + '…'
}

type CreateSourceModalProps = {
  open: boolean
  submitting: boolean
  onClose: () => void
  onSubmit: (payload: {
    title: string
    url?: string
    content_raw?: string
    collector?: string
  }) => Promise<void>
}

function CreateSourceModal({
  open,
  submitting,
  onClose,
  onSubmit,
}: CreateSourceModalProps) {
  const [title, setTitle] = useState('')
  const [url, setUrl] = useState('')
  const [contentRaw, setContentRaw] = useState('')
  const [collector, setCollector] = useState('')
  const [mode, setMode] = useState<'url' | 'manual'>('url')
  const [localError, setLocalError] = useState('')

  useEffect(() => {
    if (!open) {
      setTitle('')
      setUrl('')
      setContentRaw('')
      setCollector('')
      setMode('url')
      setLocalError('')
    }
  }, [open])

  if (!open) return null

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLocalError('')
    const trimmedTitle = title.trim()
    if (!trimmedTitle) {
      setLocalError('请填写标题')
      return
    }
    const payload: {
      title: string
      url?: string
      content_raw?: string
      collector?: string
    } = {
      title: trimmedTitle,
    }
    if (mode === 'url') {
      const trimmedUrl = url.trim()
      if (!trimmedUrl) {
        setLocalError('URL 模式下请填写链接')
        return
      }
      payload.url = trimmedUrl
    } else {
      const trimmedContent = contentRaw.trim()
      if (!trimmedContent) {
        setLocalError('手动模式下请填写内容')
        return
      }
      payload.content_raw = trimmedContent
    }
    const trimmedCollector = collector.trim()
    if (trimmedCollector) {
      payload.collector = trimmedCollector
    }
    try {
      await onSubmit(payload)
    } catch (err: unknown) {
      setLocalError(await resolveErrorMessage(err))
    }
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-end justify-center bg-black/40 p-4 sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-source-title"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3
          id="create-source-title"
          className="mb-4 text-lg font-semibold text-gray-900"
        >
          添加信息来源
        </h3>

        {/* Mode toggle */}
        <div className="mb-4 flex overflow-hidden rounded-lg border border-gray-300 text-sm">
          <button
            type="button"
            onClick={() => setMode('url')}
            className={`flex-1 px-3 py-1.5 transition-colors ${
              mode === 'url'
                ? 'bg-gray-900 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            URL 模式
          </button>
          <button
            type="button"
            onClick={() => setMode('manual')}
            className={`flex-1 px-3 py-1.5 transition-colors ${
              mode === 'manual'
                ? 'bg-gray-900 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            手动模式
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {localError ? (
            <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
              {localError}
            </div>
          ) : null}

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">
              标题
            </span>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
              placeholder="必填"
              autoComplete="off"
            />
          </label>

          {mode === 'url' ? (
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-gray-700">
                链接
              </span>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
                placeholder="https://"
                autoComplete="off"
              />
            </label>
          ) : (
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-gray-700">
                内容
              </span>
              <textarea
                value={contentRaw}
                onChange={(e) => setContentRaw(e.target.value)}
                rows={6}
                className="w-full resize-y rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
                placeholder="手动输入原始内容"
              />
            </label>
          )}

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">
              采集者
            </span>
            <input
              value={collector}
              onChange={(e) => setCollector(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
              placeholder="选填"
              autoComplete="off"
            />
          </label>

          <div className="mt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
            >
              {submitting ? '提交中…' : '添加'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function ViewSourceModal({ source, onClose }: { source: Source | null; onClose: () => void }) {
  if (!source) return null

  return (
    <div
      className="fixed inset-0 z-[100] flex items-end justify-center bg-black/40 p-4 sm:items-center"
      role="dialog"
      aria-modal="true"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        className="flex max-h-[80vh] w-full max-w-2xl flex-col rounded-2xl bg-white shadow-xl"
        onMouseDown={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-lg font-semibold text-gray-900">
              {source.title}
            </h3>
            {source.url ? (
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-0.5 block truncate text-sm text-blue-600 underline decoration-blue-300 underline-offset-2 hover:text-blue-800"
              >
                {source.url}
              </a>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="ml-4 shrink-0 rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
          >
            关闭
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto px-6 py-4">
          {source.content_markdown ? (
            <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 p-4 text-sm leading-relaxed text-gray-800">
              {source.content_markdown}
            </pre>
          ) : (
            <p className="py-8 text-center text-sm text-gray-400">暂无内容</p>
          )}

          {source.diff_log ? (
            <details className="mt-4">
              <summary className="cursor-pointer text-sm font-medium text-gray-600 hover:text-gray-800">
                变更记录
              </summary>
              <pre className="mt-2 whitespace-pre-wrap rounded-lg bg-amber-50 p-3 text-xs leading-relaxed text-amber-800">
                {source.diff_log}
              </pre>
            </details>
          ) : null}

          <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 border-t border-gray-100 pt-3 text-xs text-gray-500">
            {source.collector ? <span>采集者：{source.collector}</span> : null}
            <span>状态：{STATUS_LABELS[source.status] ?? source.status}</span>
            <span>卡片数：{source.card_count}</span>
            <span>采集于：{formatTime(source.collected_at)}</span>
            {source.refined_at ? (
              <span>精炼于：{formatTime(source.refined_at)}</span>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  )
}

export function SourcesPage() {
  const toast = useToast()
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [createSubmitting, setCreateSubmitting] = useState(false)
  const [refiningId, setRefiningId] = useState<string | null>(null)
  const [viewSource, setViewSource] = useState<Source | null>(null)

  const loadSources = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get('sources/').json<SourceListResponse>()
      setSources(data.items)
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
      setSources([])
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    loadSources()
  }, [loadSources])

  const handleRefine = async (id: string) => {
    setRefiningId(id)
    try {
      await api.post(`sources/${id}/refine`)
      toast.success('精炼成功')
      await loadSources()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    } finally {
      setRefiningId(null)
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('确定删除此信息来源？')) return
    try {
      await api.delete(`sources/${id}`)
      toast.success('来源已删除')
      setSources((prev) => prev.filter((s) => s.id !== id))
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    }
  }

  const handleCreate = async (payload: {
    title: string
    url?: string
    content_raw?: string
    collector?: string
  }) => {
    setCreateSubmitting(true)
    try {
      await api.post('sources/', { json: payload })
      toast.success('来源添加成功')
      setModalOpen(false)
      await loadSources()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    } finally {
      setCreateSubmitting(false)
    }
  }

  return (
    <div className="relative pb-24">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-gray-800">信息来源</h2>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => loadSources()}
            disabled={loading}
            className="shrink-0 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {loading ? '刷新中…' : '刷新'}
          </button>
        </div>
      </div>

      {/* Source count */}
      {!loading && sources.length > 0 && (
        <p className="mb-3 text-xs text-gray-400">
          共 {sources.length} 个来源
          （待处理 {sources.filter((s) => s.status === 'pending').length} 个）
        </p>
      )}

      {loading && sources.length === 0 ? (
        <ul className="flex flex-col gap-4">
          {[1,2,3].map(i => <li key={i}><SourceSkeleton /></li>)}
        </ul>
      ) : !loading && sources.length === 0 ? (
        <div className="text-center">
          <p className="mb-4 text-sm text-gray-500">
            暂无信息来源，点击右下角「+」添加
          </p>
        </div>
      ) : (
        <ul className="flex flex-col gap-4">
          {sources.map((source) => {
            const isBusy = refiningId === source.id
            return (
              <li key={source.id}>
                <article className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                  {/* Title row */}
                  <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
                    <h3 className="min-w-0 flex-1 text-base font-semibold leading-snug text-gray-900">
                      {source.title}
                    </h3>
                    <span
                      className={`inline-flex shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-medium ${
                        STATUS_COLORS[source.status] ?? 'bg-gray-100 text-gray-600 border-gray-200'
                      }`}
                    >
                      {STATUS_LABELS[source.status] ?? source.status}
                    </span>
                  </div>

                  {/* URL */}
                  {source.url ? (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mb-2 block truncate text-sm text-blue-600 underline decoration-blue-300 underline-offset-2 hover:text-blue-800"
                    >
                      {source.url}
                    </a>
                  ) : null}

                  {/* Content preview */}
                  {source.content_markdown ? (
                    <p className="mb-2 whitespace-pre-wrap text-sm leading-relaxed text-gray-600">
                      {truncateText(source.content_markdown, 100)}
                    </p>
                  ) : null}

                  {/* Meta row */}
                  <div className="mb-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                    {source.collector ? (
                      <span>采集者：{source.collector}</span>
                    ) : null}
                    <span>卡片数：{source.card_count}</span>
                    <span>采集于：{formatTime(source.collected_at)}</span>
                    {source.refined_at ? (
                      <span>精炼于：{formatTime(source.refined_at)}</span>
                    ) : null}
                  </div>

                  {/* Actions */}
                  <div className="flex flex-wrap gap-2 border-t border-gray-100 pt-3">
                    <button
                      type="button"
                      disabled={isBusy || source.status === 'refined'}
                      onClick={() => handleRefine(source.id)}
                      className={[
                        'rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
                        source.status === 'refined'
                          ? 'border border-green-200 bg-green-50 text-green-700'
                          : 'border border-gray-200 bg-gray-50 text-gray-700 hover:bg-gray-100',
                        isBusy ? 'cursor-not-allowed opacity-60' : '',
                      ].join(' ')}
                    >
                      {isBusy ? '精炼中…' : source.status === 'refined' ? '已精炼' : '精炼'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setViewSource(source)}
                      className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
                    >
                      查看
                    </button>
                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => handleDelete(source.id)}
                      className="rounded-lg border border-red-200 bg-white px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      删除
                    </button>
                  </div>
                </article>
              </li>
            )
          })}
        </ul>
      )}

      <button
        type="button"
        onClick={() => setModalOpen(true)}
        aria-label="添加信息来源"
        className="fixed bottom-6 right-4 z-[90] flex h-14 w-14 items-center justify-center rounded-full bg-gray-900 text-3xl leading-none text-white shadow-lg hover:bg-gray-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-900"
      >
        +
      </button>

      <CreateSourceModal
        open={modalOpen}
        submitting={createSubmitting}
        onClose={() => !createSubmitting && setModalOpen(false)}
        onSubmit={handleCreate}
      />

      <ViewSourceModal
        source={viewSource}
        onClose={() => setViewSource(null)}
      />
    </div>
  )
}
