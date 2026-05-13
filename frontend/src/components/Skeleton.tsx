/** 加载骨架屏 — 通用占位动画 */

function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div
      className={[
        'animate-pulse rounded-lg bg-gray-200',
        className ?? '',
      ].join(' ')}
    />
  )
}

/** Card skeleton – matches the shape of CardItem / CardSwipeDeck */
export function CardSkeleton() {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      {/* Title + badge */}
      <div className="mb-3 flex items-start justify-between gap-2">
        <SkeletonBlock className="h-5 w-3/5" />
        <SkeletonBlock className="h-5 w-14 shrink-0 rounded-full" />
      </div>
      {/* Summary lines */}
      <SkeletonBlock className="mb-2 h-4 w-full" />
      <SkeletonBlock className="mb-3 h-4 w-4/5" />
      {/* Source URL line */}
      <SkeletonBlock className="mb-3 h-4 w-2/5" />
      {/* Date */}
      <SkeletonBlock className="mb-3 h-3 w-1/4" />
      {/* Action buttons */}
      <div className="flex gap-2 border-t border-gray-100 pt-3">
        <SkeletonBlock className="h-7 w-14 rounded-lg" />
        <SkeletonBlock className="h-7 w-14 rounded-lg" />
        <SkeletonBlock className="h-7 w-14 rounded-lg" />
        <SkeletonBlock className="h-7 w-14 rounded-lg" />
        <SkeletonBlock className="h-7 w-14 rounded-lg" />
      </div>
    </div>
  )
}

/** Source card skeleton – matches Source card layout */
export function SourceSkeleton() {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      {/* Title + badge */}
      <div className="mb-3 flex items-start justify-between gap-2">
        <SkeletonBlock className="h-5 w-2/5" />
        <SkeletonBlock className="h-5 w-14 shrink-0 rounded-full" />
      </div>
      {/* URL line */}
      <SkeletonBlock className="mb-2 h-4 w-3/5" />
      {/* Content preview lines */}
      <SkeletonBlock className="mb-1 h-4 w-full" />
      <SkeletonBlock className="mb-2 h-4 w-3/4" />
      {/* Meta row */}
      <div className="mb-3 flex gap-4">
        <SkeletonBlock className="h-3 w-16" />
        <SkeletonBlock className="h-3 w-16" />
        <SkeletonBlock className="h-3 w-24" />
      </div>
      {/* Actions */}
      <div className="flex gap-2 border-t border-gray-100 pt-3">
        <SkeletonBlock className="h-7 w-14 rounded-lg" />
        <SkeletonBlock className="h-7 w-14 rounded-lg" />
        <SkeletonBlock className="h-7 w-14 rounded-lg" />
      </div>
    </div>
  )
}

/** Deck/stack skeleton – for swipe mode */
export function DeckSkeleton() {
  return (
    <div className="flex flex-col items-center">
      <div className="relative mx-auto h-[420px] w-full max-w-md">
        {/* Behind card */}
        <div className="absolute inset-0 scale-[0.95] translate-y-2 rounded-xl border border-gray-200 bg-white p-4 shadow-sm opacity-60">
          <SkeletonBlock className="h-5 w-3/5" />
        </div>
        {/* Front card */}
        <div className="absolute inset-0 rounded-xl border border-gray-200 bg-white p-5 shadow-md">
          <SkeletonBlock className="mb-3 h-6 w-4/5" />
          <SkeletonBlock className="mb-2 h-4 w-full" />
          <SkeletonBlock className="mb-2 h-4 w-full" />
          <SkeletonBlock className="mb-2 h-4 w-3/4" />
          <SkeletonBlock className="mb-3 h-4 w-1/3" />
          <SkeletonBlock className="h-3 w-1/4" />
        </div>
      </div>
      {/* Progress hint */}
      <SkeletonBlock className="mt-4 h-4 w-16" />
      <SkeletonBlock className="mt-2 h-3 w-64" />
    </div>
  )
}
