import { useState } from 'react'
import type { InfoCard } from '../types'

const STATUS_ACTIONS = [
  { status: 'liked' as const, label: '喜欢' },
  { status: 'disliked' as const, label: '不喜欢' },
  { status: 'valuable' as const, label: '有价值' },
  { status: 'valueless' as const, label: '无价值' },
  { status: 'pending' as const, label: '待处理' },
] as const

function formatCollectedAt(iso: string): string {
  try {
    return new Intl.DateTimeFormat('zh-CN', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(new Date(iso))
  } catch {
    return iso
  }
}

function statusBadgeClasses(status: string): string {
  switch (status) {
    case 'liked':
      return 'bg-rose-100 text-rose-800 border-rose-200'
    case 'disliked':
      return 'bg-slate-200 text-slate-800 border-slate-300'
    case 'valuable':
      return 'bg-amber-100 text-amber-900 border-amber-200'
    case 'valueless':
      return 'bg-zinc-200 text-zinc-700 border-zinc-300'
    case 'pending':
      return 'bg-gray-100 text-gray-700 border-gray-200'
    default:
      return 'bg-gray-100 text-gray-600 border-gray-200'
  }
}

function statusLabelCn(status: string): string {
  return STATUS_ACTIONS.find((x) => x.status === status)?.label ?? status
}

type CardItemProps = {
  card: InfoCard
  busy: boolean
  onStatusChange: (id: string, status: InfoCard['status']) => Promise<void>
  onCardUpdate?: (id: string, data: { title?: string; summary?: string }) => Promise<void>
}

export function CardItem({ card, busy, onStatusChange, onCardUpdate }: CardItemProps) {
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(card.title)
  const [editSummary, setEditSummary] = useState(card.summary ?? '')

  function startEditing() {
    setEditTitle(card.title)
    setEditSummary(card.summary ?? '')
    setEditing(true)
  }

  function cancelEditing() {
    setEditing(false)
  }

  async function saveEditing() {
    if (!onCardUpdate) return
    const data: { title?: string; summary?: string } = {}
    if (editTitle !== card.title) data.title = editTitle
    if (editSummary !== (card.summary ?? '')) data.summary = editSummary
    if (Object.keys(data).length === 0) {
      setEditing(false)
      return
    }
    await onCardUpdate(card.id, data)
    setEditing(false)
  }

  return (
    <article className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        {editing ? (
          <input
            type="text"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            className="min-w-0 flex-1 rounded-md border border-gray-300 px-2 py-1 text-base font-semibold leading-snug text-gray-900 focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
          />
        ) : (
          <h2 className="min-w-0 flex-1 text-base font-semibold leading-snug text-gray-900">
            {card.title}
          </h2>
        )}
        {!editing && (
          <span
            className={`inline-flex shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusBadgeClasses(card.status)}`}
          >
            {statusLabelCn(card.status)}
          </span>
        )}
      </div>

      {editing ? (
        <textarea
          value={editSummary}
          onChange={(e) => setEditSummary(e.target.value)}
          rows={3}
          className="mb-3 w-full rounded-md border border-gray-300 px-2 py-1 text-sm leading-relaxed text-gray-600 focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
        />
      ) : card.summary ? (
        <p className="mb-3 text-sm leading-relaxed text-gray-600">{card.summary}</p>
      ) : (
        <p className="mb-3 text-sm italic text-gray-400">暂无摘要</p>
      )}

      {card.source_url ? (
        <a
          href={card.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mb-3 block truncate text-sm text-blue-600 underline decoration-blue-300 underline-offset-2 hover:text-blue-800"
        >
          {card.source_url}
        </a>
      ) : (
        <p className="mb-3 text-sm text-gray-400">暂无来源链接</p>
      )}

      <p className="mb-3 text-xs text-gray-500">采集：{formatCollectedAt(card.collected_at)}</p>

      {editing ? (
        <div className="flex flex-wrap gap-2 border-t border-gray-100 pt-3">
          <button
            type="button"
            disabled={busy}
            onClick={saveEditing}
            className="rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {busy ? '保存中…' : '保存'}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={cancelEditing}
            className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-60"
          >
            取消
          </button>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-2 border-t border-gray-100 pt-3">
            {STATUS_ACTIONS.map(({ status, label }) => {
              const active = card.status === status
              return (
                <button
                  key={status}
                  type="button"
                  disabled={busy}
                  onClick={() => onStatusChange(card.id, status)}
                  className={[
                    'rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
                    active
                      ? 'bg-gray-900 text-white ring-2 ring-gray-900 ring-offset-1'
                      : 'border border-gray-200 bg-gray-50 text-gray-700 hover:bg-gray-100',
                    busy ? 'cursor-not-allowed opacity-60' : '',
                  ].join(' ')}
                >
                  {label}
                </button>
              )
            })}
            {onCardUpdate && (
              <button
                type="button"
                disabled={busy}
                onClick={startEditing}
                className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-60"
              >
                编辑
              </button>
            )}
          </div>
        </>
      )}
    </article>
  )
}
