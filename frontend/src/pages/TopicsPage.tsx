import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api } from '../lib/api'
import { resolveErrorMessage } from '../lib/error'
import { useToast } from '../context/ToastContext'
import { SourceSkeleton } from '../components/Skeleton'
import type { TopicItem, TopicListResponse, TopicCreateRequest, SearchSource, SearchSourceListResponse } from '../types'

const SCHEDULE_TYPES = [
  { value: 'manual', label: '手动' },
  { value: 'interval', label: '定时间隔' },
  { value: 'cron', label: 'Cron 表达式' },
]

const SEARCH_DEPTHS = [
  { value: 1, label: '浅层' },
  { value: 2, label: '标准' },
  { value: 3, label: '深层' },
]

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

type TopicModalProps = {
  open: boolean
  submitting: boolean
  initial?: TopicItem | null
  searchSources: SearchSource[]
  onClose: () => void
  onSubmit: (payload: TopicCreateRequest) => Promise<void>
}

function TopicModal({
  open,
  submitting,
  initial,
  searchSources,
  onClose,
  onSubmit,
}: TopicModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [keywordsInput, setKeywordsInput] = useState('')
  const [searchDepth, setSearchDepth] = useState(2)
  const [scheduleType, setScheduleType] = useState('manual')
  const [scheduleTimesInput, setScheduleTimesInput] = useState('')
  const [autoRefine, setAutoRefine] = useState(false)
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([])
  const [localError, setLocalError] = useState('')

  useEffect(() => {
    if (!open) {
      setName('')
      setDescription('')
      setKeywordsInput('')
      setSearchDepth(2)
      setScheduleType('manual')
      setScheduleTimesInput('')
      setAutoRefine(false)
      setSelectedSourceIds([])
      setLocalError('')
    }
  }, [open])

  useEffect(() => {
    if (open && initial) {
      setName(initial.name ?? '')
      setDescription(initial.description ?? '')
      setKeywordsInput(
        Array.isArray(initial.keywords) ? initial.keywords.join(', ') : '',
      )
      setSearchDepth(initial.search_depth ?? 2)
      setScheduleType(initial.schedule_type ?? 'manual')
      setScheduleTimesInput(
        Array.isArray(initial.schedule_times) ? initial.schedule_times.join(', ') : '',
      )
      setAutoRefine(initial.auto_refine ?? false)
      setSelectedSourceIds(
        initial.search_sources?.map((s) => s.id) ?? [],
      )
    }
  }, [open, initial])

  if (!open) return null

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLocalError('')
    const trimmedName = name.trim()
    if (!trimmedName) {
      setLocalError('请填写主题名称')
      return
    }

    const keywords = keywordsInput.trim()
      ? keywordsInput.trim().split(/[,，]/).map((k) => k.trim()).filter(Boolean)
      : undefined

    const scheduleTimes = scheduleTimesInput.trim()
      ? scheduleTimesInput.trim().split(/[,，]/).map((t) => t.trim()).filter(Boolean)
      : undefined

    const payload: TopicCreateRequest = {
      name: trimmedName,
      description: description.trim() || undefined,
      keywords,
      search_depth: searchDepth,
      schedule_type: scheduleType !== 'manual' ? scheduleType : undefined,
      schedule_times: scheduleType !== 'manual' ? scheduleTimes : undefined,
      auto_refine: autoRefine,
      search_source_ids: selectedSourceIds.length > 0 ? selectedSourceIds : undefined,
    }

    try {
      await onSubmit(payload)
    } catch (err: unknown) {
      setLocalError(await resolveErrorMessage(err))
    }
  }

  const toggleSource = (id: string) => {
    setSelectedSourceIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-end justify-center bg-black/40 p-4 sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="topic-modal-title"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        className="w-full max-w-md max-h-[85vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-xl"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3
          id="topic-modal-title"
          className="mb-4 text-lg font-semibold text-gray-900"
        >
          {initial ? '编辑主题' : '创建主题'}
        </h3>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {localError ? (
            <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
              {localError}
            </div>
          ) : null}

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">
              名称
            </span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
              placeholder="必填"
              autoComplete="off"
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">
              描述
            </span>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full resize-y rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
              placeholder="选填"
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">
              关键词（逗号分隔）
            </span>
            <input
              value={keywordsInput}
              onChange={(e) => setKeywordsInput(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
              placeholder="关键词1, 关键词2"
              autoComplete="off"
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">
              搜索深度
            </span>
            <select
              value={searchDepth}
              onChange={(e) => setSearchDepth(Number(e.target.value))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
            >
              {SEARCH_DEPTHS.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">
              调度类型
            </span>
            <select
              value={scheduleType}
              onChange={(e) => setScheduleType(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
            >
              {SCHEDULE_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>

          {scheduleType !== 'manual' ? (
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-gray-700">
                调度时间（逗号分隔，如 08:00, 14:00）
              </span>
              <input
                value={scheduleTimesInput}
                onChange={(e) => setScheduleTimesInput(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
                placeholder={scheduleType === 'cron' ? '0 */6 * * *' : '08:00, 14:00'}
                autoComplete="off"
              />
            </label>
          ) : null}

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={autoRefine}
              onChange={(e) => setAutoRefine(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-gray-500"
            />
            <span className="text-sm font-medium text-gray-700">
              自动精炼
            </span>
          </label>

          <div className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">
              关联搜索源
            </span>
            {searchSources.length === 0 ? (
              <p className="text-xs text-gray-400">暂无搜索源</p>
            ) : (
              <div className="flex flex-col gap-1.5 max-h-32 overflow-y-auto">
                {searchSources.map((ss) => (
                  <label key={ss.id} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={selectedSourceIds.includes(ss.id)}
                      onChange={() => toggleSource(ss.id)}
                      className="h-4 w-4 rounded border-gray-300 text-gray-900 focus:ring-gray-500"
                    />
                    <span className="text-sm text-gray-700">{ss.title}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

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
              {submitting ? '提交中…' : initial ? '保存' : '创建'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export function TopicsPage() {
  const toast = useToast()
  const [topics, setTopics] = useState<TopicItem[]>([])
  const [searchSources, setSearchSources] = useState<SearchSource[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingTopic, setEditingTopic] = useState<TopicItem | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [collectingId, setCollectingId] = useState<string | null>(null)

  const loadTopics = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get('topics/').json<TopicListResponse>()
      setTopics(data.items)
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
      setTopics([])
    } finally {
      setLoading(false)
    }
  }, [toast])

  const loadSearchSources = useCallback(async () => {
    try {
      const data = await api.get('search-sources/').json<SearchSourceListResponse>()
      setSearchSources(data.items)
    } catch {
      // silent — search source list is auxiliary
    }
  }, [])

  useEffect(() => {
    loadTopics()
    loadSearchSources()
  }, [loadTopics, loadSearchSources])

  const handleSyncScheduler = async () => {
    try {
      await api.post('scheduler/sync')
    } catch {
      // best-effort
    }
  }

  const handleCreate = async (payload: TopicCreateRequest) => {
    setSubmitting(true)
    try {
      await api.post('topics/', { json: payload })
      toast.success('主题创建成功')
      setModalOpen(false)
      await loadTopics()
      await handleSyncScheduler()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdate = async (payload: TopicCreateRequest) => {
    if (!editingTopic) return
    setSubmitting(true)
    try {
      await api.put(`topics/${editingTopic.id}`, { json: payload })
      toast.success('主题已更新')
      setEditingTopic(null)
      await loadTopics()
      await handleSyncScheduler()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('确定删除此主题？')) return
    try {
      await api.delete(`topics/${id}`)
      toast.success('主题已删除')
      setTopics((prev) => prev.filter((t) => t.id !== id))
      await handleSyncScheduler()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    }
  }

  const handleCollectNow = async (id: string) => {
    setCollectingId(id)
    try {
      await api.post('scheduler/sync', { json: { topic_id: id } })
      toast.success('已触发采集')
      await handleSyncScheduler()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    } finally {
      setCollectingId(null)
    }
  }

  const handleToggleEnabled = async (topic: TopicItem) => {
    const next = !topic.enabled
    try {
      await api.put(`topics/${topic.id}`, { json: { enabled: next } })
      setTopics((prev) =>
        prev.map((t) => (t.id === topic.id ? { ...t, enabled: next } : t)),
      )
      toast.success(next ? '主题已启用' : '主题已禁用')
      await handleSyncScheduler()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    }
  }

  const openEditModal = (topic: TopicItem) => {
    setEditingTopic(topic)
  }

  const closeModal = () => {
    if (!submitting) {
      setModalOpen(false)
      setEditingTopic(null)
    }
  }

  return (
    <div className="relative pb-24">
      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-gray-800">主题</h2>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => loadTopics()}
            disabled={loading}
            className="shrink-0 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {loading ? '刷新中…' : '刷新'}
          </button>
        </div>
      </div>

      {!loading && topics.length > 0 && (
        <p className="mb-3 text-xs text-gray-400">
          共 {topics.length} 个主题
        </p>
      )}

      {loading && topics.length === 0 ? (
        <ul className="flex flex-col gap-4">
          {[1, 2, 3].map((i) => (
            <li key={i}><SourceSkeleton /></li>
          ))}
        </ul>
      ) : !loading && topics.length === 0 ? (
        <div className="text-center">
          <p className="mb-4 text-sm text-gray-500">
            暂无主题，点击右下角「+」创建
          </p>
        </div>
      ) : (
        <ul className="flex flex-col gap-4">
          {topics.map((topic) => {
            const isCollecting = collectingId === topic.id
            return (
              <li key={topic.id}>
                <article className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                  <div className="mb-2 flex flex-wrap items-start justify-between gap-2">
                    <h3 className="min-w-0 flex-1 text-base font-semibold leading-snug text-gray-900">
                      {topic.name}
                    </h3>
                    <button
                      type="button"
                      onClick={() => handleToggleEnabled(topic)}
                      className={`inline-flex shrink-0 cursor-pointer rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors ${
                        topic.enabled
                          ? 'bg-green-100 text-green-800 border-green-200 hover:bg-green-200'
                          : 'bg-gray-100 text-gray-600 border-gray-200 hover:bg-gray-200'
                      }`}
                    >
                      {topic.enabled ? '已启用' : '已禁用'}
                    </button>
                  </div>

                  {topic.description ? (
                    <p className="mb-2 whitespace-pre-wrap text-sm leading-relaxed text-gray-600">
                      {topic.description.length > 100
                        ? topic.description.slice(0, 100) + '…'
                        : topic.description}
                    </p>
                  ) : null}

                  {Array.isArray(topic.keywords) && topic.keywords.length > 0 ? (
                    <div className="mb-3 flex flex-wrap gap-1.5">
                      {topic.keywords.map((kw, idx) => (
                        <span
                          key={idx}
                          className="inline-flex rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-600/20"
                        >
                          {kw}
                        </span>
                      ))}
                    </div>
                  ) : null}

                  <div className="mb-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                    {topic.schedule_type ? (
                      <span>
                        调度：{SCHEDULE_TYPES.find((t) => t.value === topic.schedule_type)?.label ?? topic.schedule_type}
                      </span>
                    ) : null}
                    {Array.isArray(topic.schedule_times) && topic.schedule_times.length > 0 ? (
                      <span>时间：{topic.schedule_times.join(', ')}</span>
                    ) : null}
                    {topic.search_sources && topic.search_sources.length > 0 ? (
                      <span>搜索源：{topic.search_sources.length} 个</span>
                    ) : null}
                    <span>创建于：{formatTime(topic.created_at)}</span>
                  </div>

                  <div className="flex flex-wrap gap-2 border-t border-gray-100 pt-3">
                    <button
                      type="button"
                      onClick={() => handleCollectNow(topic.id)}
                      disabled={isCollecting}
                      className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {isCollecting ? '采集中…' : '立即采集'}
                    </button>
                    <button
                      type="button"
                      onClick={() => openEditModal(topic)}
                      className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
                    >
                      编辑
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(topic.id)}
                      className="rounded-lg border border-red-200 bg-white px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
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
        aria-label="创建主题"
        className="fixed bottom-6 right-4 z-[90] flex h-14 w-14 items-center justify-center rounded-full bg-gray-900 text-3xl leading-none text-white shadow-lg hover:bg-gray-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-900"
      >
        +
      </button>

      <TopicModal
        open={modalOpen}
        submitting={submitting}
        initial={null}
        searchSources={searchSources}
        onClose={closeModal}
        onSubmit={handleCreate}
      />

      <TopicModal
        open={!!editingTopic}
        submitting={submitting}
        initial={editingTopic}
        searchSources={searchSources}
        onClose={closeModal}
        onSubmit={handleUpdate}
      />
    </div>
  )
}
