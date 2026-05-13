import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react'

/* ──────────────────────────────────────────────
 * Types
 * ────────────────────────────────────────────── */

type ToastType = 'success' | 'error' | 'info'

interface ToastItem {
  id: string
  message: string
  type: ToastType
}

interface ToastContextValue {
  show: (message: string, type?: ToastType) => void
  success: (message: string) => void
  error: (message: string) => void
  info: (message: string) => void
}

/* ──────────────────────────────────────────────
 * Context
 * ────────────────────────────────────────────── */

const ToastContext = createContext<ToastContextValue | null>(null)

let toastId = 0

/* ──────────────────────────────────────────────
 * Individual Toast Item
 * ────────────────────────────────────────────── */

function ToastItem({ toast, onDone }: { toast: ToastItem; onDone: (id: string) => void }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true))

    const timer = setTimeout(() => {
      setVisible(false)
      setTimeout(() => onDone(toast.id), 300)
    }, 3000)

    return () => clearTimeout(timer)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const bgMap: Record<ToastType, string> = {
    success: 'bg-green-600',
    error: 'bg-red-600',
    info: 'bg-gray-800',
  }

  const iconMap: Record<ToastType, string> = {
    success: '✓',
    error: '✕',
    info: 'ℹ',
  }

  return (
    <div
      className={[
        'flex items-center gap-2 rounded-xl px-4 py-3 text-sm text-white shadow-lg transition-all duration-300',
        bgMap[toast.type],
        visible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0',
      ].join(' ')}
    >
      <span className="shrink-0 font-bold">{iconMap[toast.type]}</span>
      <span className="flex-1">{toast.message}</span>
    </div>
  )
}

/* ──────────────────────────────────────────────
 * Provider
 * ────────────────────────────────────────────── */

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const show = useCallback((message: string, type: ToastType = 'info') => {
    const id = `toast-${++toastId}`
    setToasts((prev) => [...prev, { id, message, type }])
  }, [])

  const value: ToastContextValue = {
    show,
    success: (msg: string) => show(msg, 'success'),
    error: (msg: string) => show(msg, 'error'),
    info: (msg: string) => show(msg, 'info'),
  }

  return (
    <ToastContext.Provider value={value}>
      {children}

      {/* Toast container – fixed bottom center, above FAB */}
      <div className="fixed bottom-24 left-1/2 z-[200] flex w-full max-w-sm -translate-x-1/2 flex-col gap-2 px-4">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onDone={removeToast} />
        ))}
      </div>
    </ToastContext.Provider>
  )
}

/* ──────────────────────────────────────────────
 * Hook
 * ────────────────────────────────────────────── */

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
