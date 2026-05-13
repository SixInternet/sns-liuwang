import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export function LoginPage() {
  const { login, register, loading } = useAuth()
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    setError('')
    try {
      if (isLogin) {
        await login(username, password)
      } else {
        await register(username, password)
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : '操作失败，请稍后重试'
      setError(message)
    }
  }

  const switchMode = () => {
    setIsLogin(!isLogin)
    setError('')
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-sm">
        <h1 className="text-2xl font-bold text-center text-gray-800 mb-6">
          {isLogin ? '登录' : '注册'}
        </h1>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 text-sm rounded-lg">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <input
            type="text"
            placeholder="用户名"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-400 focus:outline-none"
          />
          <input
            type="password"
            placeholder="密码"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-400 focus:outline-none"
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !username || !password}
            className="w-full py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 transition"
          >
            {loading ? '处理中...' : isLogin ? '登录' : '注册'}
          </button>
        </div>

        <p className="text-center text-sm text-gray-500 mt-6">
          {isLogin ? (
            <>
              没有账号？
              <button
                onClick={switchMode}
                className="text-red-500 ml-1 hover:underline"
              >
                注册
              </button>
            </>
          ) : (
            <>
              已有账号？
              <button
                onClick={switchMode}
                className="text-red-500 ml-1 hover:underline"
              >
                登录
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  )
}
