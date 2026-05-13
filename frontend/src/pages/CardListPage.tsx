import { useCallback, useEffect, useState } from 'react'
import { api } from '../lib/api'
import { resolveErrorMessage } from '../lib/error'
import { useToast } from '../context/ToastContext'
import type { InfoCard } from '../types'
import { CardItem } from '../components/CardItem'
import { CardSkeleton, DeckSkeleton } from '../components/Skeleton'
import { CardSwipeDeck } from '../components/CardSwipeDeck'
import { SwipeStats } from '../components/SwipeStats'
import { CreateCardModal } from '../components/CreateCardModal'

interface CardListResponse {
  items: InfoCard[]
  total: number
}

type ViewMode = 'list' | 'swipe'

export function CardListPage() {
  const toast = useToast()
  const [cards, setCards] = useState<InfoCard[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [createSubmitting, setCreateSubmitting] = useState(false)
  const [updatingId, setUpdatingId] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('list')

  const loadCards = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get('cards/').json<CardListResponse>()
      setCards(data.items)
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
      setCards([])
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    loadCards()
  }, [loadCards])

  const handleStatusChange = async (id: string, status: InfoCard['status']) => {
    setUpdatingId(id)
    try {
      await api.patch(`cards/${id}/status`, { json: { status } }).json<InfoCard>()
      await loadCards()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    } finally {
      setUpdatingId(null)
    }
  }

  const handleCardUpdate = async (id: string, data: { title?: string; summary?: string }) => {
    setUpdatingId(id)
    try {
      await api.patch(`cards/${id}`, { json: data })
      await loadCards()
      toast.success('卡片已更新')
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    } finally {
      setUpdatingId(null)
    }
  }

  const handleCreate = async (payload: { title: string; summary: string; source_url: string }) => {
    setCreateSubmitting(true)
    try {
      await api.post('cards/', {
        json: {
          title: payload.title,
          summary: payload.summary,
          source_url: payload.source_url,
        },
      })
      toast.success('卡片创建成功')
      setModalOpen(false)
      await loadCards()
    } catch (err: unknown) {
      toast.error(await resolveErrorMessage(err))
    } finally {
      setCreateSubmitting(false)
    }
  }

  return (
    <div className="relative pb-24">
      {/* Header + mode toggle */}
      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-gray-800">卡片</h2>

        <div className="flex items-center gap-2">
          {/* View mode toggle */}
          <div className="flex overflow-hidden rounded-lg border border-gray-300 text-sm">
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 transition-colors ${viewMode === 'list' ? 'bg-gray-900 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
            >
              📋 列表
            </button>
            <button
              type="button"
              onClick={() => setViewMode('swipe')}
              className={`px-3 py-1.5 transition-colors ${viewMode === 'swipe' ? 'bg-gray-900 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
            >
              🃏 滑动
            </button>
          </div>

          <button
            type="button"
            onClick={() => loadCards()}
            disabled={loading}
            className="shrink-0 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {loading ? '刷新中…' : '刷新'}
          </button>
        </div>
      </div>

      {/* Card count */}
      {!loading && cards.length > 0 && (
        <p className="mb-3 text-xs text-gray-400">
          共 {cards.length} 张卡片
          {viewMode === 'swipe'
            ? `（待处理 ${cards.filter((c) => c.status === 'pending').length} 张）`
            : ''}
        </p>
      )}

      {/* Content area */}
      {loading && cards.length === 0 ? (
        viewMode === 'swipe' ? <DeckSkeleton /> : (
          <ul className="flex flex-col gap-4">
            {[1,2,3].map(i => <li key={i}><CardSkeleton /></li>)}
          </ul>
        )
      ) : !loading && cards.length === 0 ? (
        <p className="text-center text-sm text-gray-500">暂无卡片，点击右下角「+」添加</p>
      ) : viewMode === 'swipe' ? (
        <>
          <CardSwipeDeck
            cards={cards}
            onStatusChange={handleStatusChange}
            loading={loading}
          />
          <SwipeStats cards={cards} />
        </>
      ) : (
        <ul className="flex flex-col gap-4">
          {cards.map((card) => (
            <li key={card.id}>
              <CardItem card={card} busy={updatingId === card.id} onStatusChange={handleStatusChange} onCardUpdate={handleCardUpdate} />
            </li>
          ))}
        </ul>
      )}

      <button
        type="button"
        onClick={() => setModalOpen(true)}
        aria-label="新建卡片"
        className="fixed bottom-6 right-4 z-[90] flex h-14 w-14 items-center justify-center rounded-full bg-gray-900 text-3xl leading-none text-white shadow-lg hover:bg-gray-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-900"
      >
        +
      </button>

      <CreateCardModal
        open={modalOpen}
        submitting={createSubmitting}
        onClose={() => !createSubmitting && setModalOpen(false)}
        onSubmit={handleCreate}
      />
    </div>
  )
}
