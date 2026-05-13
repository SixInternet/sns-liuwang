import type { InfoCard } from '../types'

interface SwipeStatsProps {
  cards: InfoCard[]
}

const QUADRANTS: {
  key: string
  statusFilter: (c: InfoCard) => boolean
  label: string
  bgClass: string
}[] = [
  {
    key: 'liked-valuable',
    statusFilter: (c) => c.status === 'liked' || c.status === 'valuable',
    label: '知识偏好',
    bgClass: 'bg-rose-50 border-rose-200',
  },
  {
    key: 'liked-valueless',
    statusFilter: (c) => c.status === 'liked' || c.status === 'valueless',
    label: '喜好参考',
    bgClass: 'bg-amber-50 border-amber-200',
  },
  {
    key: 'disliked-valuable',
    statusFilter: (c) => c.status === 'disliked' || c.status === 'valuable',
    label: '弱点方向',
    bgClass: 'bg-sky-50 border-sky-200',
  },
  {
    key: 'disliked-valueless',
    statusFilter: (c) => c.status === 'disliked' || c.status === 'valueless',
    label: '垃圾信息',
    bgClass: 'bg-zinc-50 border-zinc-200',
  },
]

const STATUS_LABELS: Record<string, string> = {
  liked: '喜欢',
  disliked: '不喜欢',
  valuable: '有价值',
  valueless: '无价值',
  pending: '待处理',
}

export function SwipeStats({ cards }: SwipeStatsProps) {
  const total = cards.length
  const pending = cards.filter((c) => c.status === 'pending').length

  // Count each status
  const statusCounts: Record<string, number> = {}
  for (const c of cards) {
    statusCounts[c.status] = (statusCounts[c.status] ?? 0) + 1
  }

  return (
    <div className="mt-6 space-y-4">
      {/* Summary bar */}
      <div className="flex items-center justify-between text-sm text-gray-600">
        <span>总计 <strong>{total}</strong> 张卡片</span>
        <span>待处理 <strong>{pending}</strong> 张</span>
      </div>

      {/* Status breakdown */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(STATUS_LABELS).map(([status, label]) => {
          const count = statusCounts[status] ?? 0
          const cls = status === 'pending' ? 'bg-gray-200 text-gray-700' : 'bg-white text-gray-800'
          return (
            <span
              key={status}
              className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${cls}`}
            >
              {label}
              <span className="rounded-full bg-gray-800/10 px-1.5 text-[11px] font-bold">
                {count}
              </span>
            </span>
          )
        })}
      </div>

      {/* 4-quadrant cards */}
      <div className="grid grid-cols-2 gap-3">
        {QUADRANTS.map((q) => {
          const count = cards.filter(q.statusFilter).length
          return (
            <div
              key={q.key}
              className={`rounded-xl border p-3 ${q.bgClass}`}
            >
              <p className="text-xs font-medium text-gray-700">{q.label}</p>
              <p className="mt-1 text-2xl font-bold text-gray-900">{count}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
