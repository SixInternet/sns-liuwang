import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api } from '../lib/api'
import { resolveErrorMessage } from '../lib/error'
import { useToast } from '../context/ToastContext'
import type { SearchSource, SearchSourceListResponse } from '../types'

type CreateSearchSourceModalProps = {
  open: boolean
  submitting: boolean
  onClose: () => void
  onSubmit: (payload: { title: string; base_url: string }) => Promise<void>
}

function CreateSearchSourceModal({ open, submitting, onClose, onSubmit }: CreateSearchSourceModalProps) {
  const [title, setTitle] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [localError, setLocalError] = useState('')

  useEffect(() => {
    if (!open) { setTitle(''); setBaseUrl(''); setLocalError('') }
  }, [open])

  if (!open) return null

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLocalError('')
    const t = title.trim()
    const u = baseUrl.trim()
    if (!t) { setLocalError('请填写标题'); return }
    if (!u) { setLocalError('请填写 Base URL'); return }
    if (t === u) { setLocalError('标题和 Base URL 不能相同'); return }
    try {
      await onSubmit({ title: t, base_url: u })
    } catch (err: unknown) {
      setLocalError(await resolveErrorMessage(err))
    }
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-end justify-center bg-black/40 p-4 sm:items-center"
      role="dialog" aria-modal="true" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl" onMouseDown={(e) => e.stopPropagation()}>
        <h3 className="mb-4 text-lg font-semibold text-gray-900">添加搜索源</h3>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {localError && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{localError}</div>}
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">标题</span>
            <input value={title} onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
              placeholder="必填" autoComplete="off" />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">Base URL</span>
            <input type="url" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
              placeholder="https://" autoComplete="off" />
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

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '-'
  try { return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'short' }).format(new Date(iso)) }
  catch { return iso }
}

export function SearchSourcesPage() {
  const toast = useToast()
  const [sources, setSources] = useState<SearchSource[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [createSubmitting, setCreateSubmitting] = useState(false)

  const loadSources = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get('search-sources/').json<SearchSourceListResponse>()
      setSources(data.items)
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
      setSources([])
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => { loadSources() }, [loadSources])

  const handleDelete = useCallback(async (sourceId: string) => {
    if (!window.confirm('确定删除此搜索源？')) return
    try {
      await api.delete(`search-sources/${sourceId}`)
      toast.success('搜索源已删除')
      setSources((prev) => prev.filter((s) => s.id !== sourceId))
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    }
  }, [toast])

  const handleCreate = useCallback(async (payload: { title: string; base_url: string }) => {
    setCreateSubmitting(true)
    try {
      await api.post('search-sources/', { json: payload })
      toast.success('搜索源添加成功')
      setModalOpen(false)
      await loadSources()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    } finally {
      setCreateSubmitting(false)
    }
  }, [toast, loadSources])

  return (
    <div className="relative pb-24">
      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-gray-800">搜索源</h2>
        <button onClick={() => loadSources()} disabled={loading}
          className="shrink-0 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50">
          {loading ? '刷新中…' : '刷新'}
        </button>
      </div>

      {!loading && sources.length > 0 && (
        <p className="mb-3 text-xs text-gray-400">共 {sources.length} 个搜索源</p>
      )}

      {loading && sources.length === 0 ? (
        <div className="py-8 text-center text-sm text-gray-400">加载中…</div>
      ) : !loading && sources.length === 0 ? (
        <div className="py-8 text-center text-sm text-gray-500">暂无搜索源，点击右下角「+」添加</div>
      ) : (
        <ul className="flex flex-col gap-3">
          {sources.map((source) => (
            <li key={source.id} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-semibold text-gray-900">{source.title}</div>
                  <a href={source.base_url} target="_blank" rel="noopener noreferrer"
                    className="mt-0.5 block truncate text-xs text-blue-600 underline decoration-blue-300 underline-offset-2 hover:text-blue-800">
                    {source.base_url}
                  </a>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span className="whitespace-nowrap text-xs text-gray-400">{fmtDate(source.created_at)}</span>
                  <button onClick={() => handleDelete(source.id)}
                    className="rounded-lg border border-red-200 bg-white px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50">删除</button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      <button onClick={() => setModalOpen(true)} aria-label="添加搜索源"
        className="fixed bottom-6 right-4 z-[90] flex h-14 w-14 items-center justify-center rounded-full bg-gray-900 text-3xl leading-none text-white shadow-lg hover:bg-gray-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-900">
        +
      </button>

      <CreateSearchSourceModal open={modalOpen} submitting={createSubmitting}
        onClose={() => !createSubmitting && setModalOpen(false)} onSubmit={handleCreate} />
    </div>
  )
}
