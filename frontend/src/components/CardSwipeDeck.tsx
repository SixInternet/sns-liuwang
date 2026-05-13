import { useState, useCallback } from 'react'
import {
  motion,
  AnimatePresence,
  useMotionValue,
  useTransform,
  type MotionValue,
  type PanInfo,
} from 'framer-motion'
import type { InfoCard } from '../types'

const SWIPE_THRESHOLD = 100

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

type SwipeDir = 'liked' | 'disliked' | 'valuable' | 'valueless'

const SWIPE_OVERRIDES: Record<string, string> = {
  liked: 'liked',
  disliked: 'disliked',
  valuable: 'valuable',
  valueless: 'valueless',
}

function directionFromPan(info: PanInfo): SwipeDir | null {
  const { x, y } = info.offset
  const absX = Math.abs(x)
  const absY = Math.abs(y)

  if (absX > SWIPE_THRESHOLD && absX > absY) {
    return x > 0 ? 'liked' : 'disliked'
  }
  if (absY > SWIPE_THRESHOLD) {
    return y > 0 ? 'valuable' : 'valueless'
  }
  return null
}

function getDirLabel(dir: string): string {
  switch (dir) {
    case 'liked': return '❤️ 喜欢'
    case 'disliked': return '✖️ 不喜欢'
    case 'valuable': return '💡 有价值'
    case 'valueless': return '➖ 无价值'
    default: return ''
  }
}

function getDirBg(dir: string): string {
  switch (dir) {
    case 'liked': return 'bg-green-500'
    case 'disliked': return 'bg-red-500'
    case 'valuable': return 'bg-amber-500'
    case 'valueless': return 'bg-gray-500'
    default: return ''
  }
}

/** Live direction from motion values (lower threshold for label visibility) */
function currentDir(xv: number, yv: number): string {
  const absX = Math.abs(xv)
  const absY = Math.abs(yv)
  const t = SWIPE_THRESHOLD * 0.3

  if (absX > t && absX > absY) return xv > 0 ? 'liked' : 'disliked'
  if (absY > t) return yv > 0 ? 'valuable' : 'valueless'
  return ''
}

/* ------------------------------------------------------------------ */
/* OverlayLabel — must be called as a component (hooks used inside)    */
/* ------------------------------------------------------------------ */

function OverlayLabel({
  x,
  y,
}: {
  x: MotionValue<number>
  y: MotionValue<number>
}) {
  const opacity = useTransform([x, y], ([xv, yv]: number[]) => {
    const m = Math.max(Math.abs(xv), Math.abs(yv))
    return Math.min(m / SWIPE_THRESHOLD, 1)
  })
  const dir = useTransform([x, y], ([xv, yv]: number[]) => currentDir(xv, yv))
  const dirRaw = dir.get() as string
  if (!dirRaw) return null

  return (
    <motion.div
      className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center"
      style={{ opacity }}
    >
      <span
        className={`rounded-xl px-6 py-3 text-2xl font-bold text-white shadow-lg ${getDirBg(dirRaw)}`}
      >
        {getDirLabel(dirRaw)}
      </span>
    </motion.div>
  )
}

/* ------------------------------------------------------------------ */
/* CardSwipeDeck                                                       */
/* ------------------------------------------------------------------ */

interface CardSwipeDeckProps {
  cards: InfoCard[]
  onStatusChange: (id: string, status: InfoCard['status']) => Promise<void>
  loading: boolean
}

export function CardSwipeDeck({ cards, onStatusChange, loading }: CardSwipeDeckProps) {
  const pendingCards = cards.filter((c) => c.status === 'pending')
  const [processedIds, setProcessedIds] = useState<Set<string>>(new Set())
  const [isProcessing, setIsProcessing] = useState(false)

  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const rotate = useTransform(x, (v: number) => v / 20)
  const [exitX, setExitX] = useState(0)
  const [exitY, setExitY] = useState(0)

  // Use a local Set to track processed card IDs, so data refreshes (loadCards)
  // don't cause index-based position to shift and skip cards
  const remainingCards = pendingCards.filter((c) => !processedIds.has(c.id))
  const activeCard = remainingCards[0] ?? null
  const hasMore = remainingCards.length > 1
  const completedCount = processedIds.size
  const totalToProcess = completedCount + remainingCards.length

  const handleDragEnd = useCallback(
    async (_: unknown, info: PanInfo) => {
      if (isProcessing || !activeCard) return
      const dir = directionFromPan(info)
      if (!dir) return

      setIsProcessing(true)
      setExitX(info.offset.x)
      setExitY(info.offset.y)

      // Mark as processed locally FIRST, then call API in background
      setProcessedIds((prev) => new Set(prev).add(activeCard.id))

      // Reset motion values immediately
      x.set(0)
      y.set(0)
      setExitX(0)
      setExitY(0)
      setIsProcessing(false)

      // Fire-and-forget API call — don't await so UI stays responsive
      onStatusChange(activeCard.id, SWIPE_OVERRIDES[dir]).catch(() => {})
    },
    [isProcessing, activeCard, onStatusChange, x, y],
  )

  /* Loading state */
  if (loading && !activeCard) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-sm text-gray-500">加载中…</p>
      </div>
    )
  }

  /* Empty state */
  if (!activeCard) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 bg-gray-50 py-20">
        <p className="mb-3 text-4xl">🎉</p>
        <p className="text-lg font-medium text-gray-600">全部卡片已处理</p>
        <p className="mt-1 text-sm text-gray-400">所有待处理卡片都已完成标注</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center">
      {/* Card stack */}
      <div className="relative mx-auto h-[380px] sm:h-[420px] w-full max-w-md">
        {/* Behind card */}
        {hasMore && (
          <div
            key={remainingCards[1].id}
            className="pointer-events-none absolute inset-0 scale-[0.95] translate-y-2 rounded-xl border border-gray-200 bg-white p-4 shadow-sm opacity-60"
          >
            <p className="line-clamp-2 text-base font-semibold text-gray-900">
              {remainingCards[1].title}
            </p>
          </div>
        )}

        {/* Front card */}
        <AnimatePresence mode="popLayout">
          <motion.div
            key={activeCard.id}
            className="absolute inset-0"
            style={{ x, y, rotate }}
            drag
            dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
            dragElastic={0.9}
            onDragEnd={handleDragEnd}
            initial={{ scale: 1, opacity: 1 }}
            exit={{
              x: exitX * 3,
              y: exitY * 3,
              opacity: 0,
              scale: 0.8,
              transition: { duration: 0.25 },
            }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          >
            <div className="relative h-full select-none rounded-xl border border-gray-200 bg-white p-5 shadow-md">
              <OverlayLabel x={x} y={y} />

              <h2 className="mb-3 text-lg font-semibold leading-snug text-gray-900">
                {activeCard.title}
              </h2>

              {activeCard.summary ? (
                <p className="mb-3 line-clamp-4 text-sm leading-relaxed text-gray-600">
                  {activeCard.summary}
                </p>
              ) : (
                <p className="mb-3 text-sm italic text-gray-400">暂无摘要</p>
              )}

              {activeCard.source_url ? (
                <a
                  href={activeCard.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mb-3 block truncate text-sm text-blue-600 underline decoration-blue-300 underline-offset-2 hover:text-blue-800"
                  onClick={(e) => e.stopPropagation()}
                >
                  {activeCard.source_url}
                </a>
              ) : (
                <p className="mb-3 text-sm text-gray-400">暂无来源链接</p>
              )}

              <p className="mb-2 text-xs text-gray-500">
                采集：{formatCollectedAt(activeCard.collected_at)}
              </p>

              {activeCard.category && (
                <span className="inline-block rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                  {activeCard.category}
                </span>
              )}

              {isProcessing && (
                <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-white/70">
                  <span className="text-sm text-gray-600">处理中…</span>
                </div>
              )}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Progress & hints */}
      <p className="mt-4 text-sm text-gray-500">
        {completedCount + 1} / {totalToProcess}
      </p>
      <p className="mt-2 text-center text-xs text-gray-400">
        左滑不喜欢 · 右滑喜欢 · 上滑无价值 · 下滑有价值
      </p>
    </div>
  )
}
