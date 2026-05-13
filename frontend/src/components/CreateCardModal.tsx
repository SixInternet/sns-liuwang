import { useEffect, useState, type FormEvent } from 'react'
import { resolveErrorMessage } from '../lib/error'

type CreateCardModalProps = {
  open: boolean
  submitting: boolean
  onClose: () => void
  onSubmit: (payload: { title: string; summary: string; source_url: string }) => Promise<void>
}

export function CreateCardModal({
  open,
  submitting,
  onClose,
  onSubmit,
}: CreateCardModalProps) {
  const [title, setTitle] = useState('')
  const [summary, setSummary] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [localError, setLocalError] = useState('')

  useEffect(() => {
    if (!open) {
      setTitle('')
      setSummary('')
      setSourceUrl('')
      setLocalError('')
    }
  }, [open])

  if (!open) return null

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLocalError('')
    const trimmed = title.trim()
    if (!trimmed) {
      setLocalError('请填写标题')
      return
    }
    try {
      await onSubmit({
        title: trimmed,
        summary: summary.trim() || '',
        source_url: sourceUrl.trim() || '',
      })
    } catch (err: unknown) {
      setLocalError(await resolveErrorMessage(err))
    }
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-end justify-center bg-black/40 p-4 sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-card-title"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="create-card-title" className="mb-4 text-lg font-semibold text-gray-900">
          新建卡片
        </h3>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {localError ? (
            <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{localError}</div>
          ) : null}

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">标题</span>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
              placeholder="必填"
              autoComplete="off"
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">摘要</span>
            <textarea
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              rows={3}
              className="w-full resize-y rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
              placeholder="选填"
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">来源链接</span>
            <input
              type="url"
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none ring-blue-500 focus:border-transparent focus:ring-2"
              placeholder="https://"
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
              {submitting ? '提交中…' : '创建'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
