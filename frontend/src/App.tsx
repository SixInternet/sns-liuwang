import { useState } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import { CardListPage } from './pages/CardListPage'
import { CollectionMonitorPage } from './pages/CollectionMonitorPage'
import { LoginPage } from './pages/LoginPage'
import { SearchSourcesPage } from './pages/SearchSourcesPage'
import { SourcesPage } from './pages/SourcesPage'
import { TopicsPage } from './pages/TopicsPage'

type Tab = 'sources' | 'cards' | 'search-sources' | 'topics' | 'collection'

const TAB_CONFIG: { key: Tab; label: string }[] = [
  { key: 'sources', label: '📦 信息来源' },
  { key: 'cards', label: '📋 卡片' },
  { key: 'search-sources', label: '📡 搜索源' },
  { key: 'topics', label: '🎯 主题' },
  { key: 'collection', label: '📊 采集' },
]

function AuthenticatedApp() {
  const { isAuthenticated, username, logout } = useAuth()
  const [activeTab, setActiveTab] = useState<Tab>('sources')

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm px-3 sm:px-6 py-3 flex items-center justify-between">
        <h1 className="text-base sm:text-lg font-bold text-gray-800">六网空间</h1>
        <div className="flex items-center gap-2 sm:gap-4">
          <span className="hidden sm:inline text-sm text-gray-600">{username}</span>
          <button
            onClick={logout}
            className="text-xs sm:text-sm text-red-500 hover:underline whitespace-nowrap"
          >
            退出
          </button>
        </div>
      </header>
      <nav className="flex gap-0 border-b border-gray-200 bg-white px-3 sm:px-6 overflow-x-auto">
        {TAB_CONFIG.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-1.5 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === key
                ? 'border-gray-900 text-gray-900'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {label}
          </button>
        ))}
      </nav>
      <main className="mx-auto max-w-2xl px-3 sm:px-4 py-4 sm:py-6">
        {activeTab === 'sources' && <SourcesPage />}
        {activeTab === 'cards' && <CardListPage />}
        {activeTab === 'search-sources' && <SearchSourcesPage />}
        {activeTab === 'topics' && <TopicsPage />}
        {activeTab === 'collection' && <CollectionMonitorPage />}
      </main>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <AuthenticatedApp />
      </ToastProvider>
    </AuthProvider>
  )
}

export default App
