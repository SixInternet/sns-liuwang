import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import {
  getStoredToken,
  setStoredToken,
  clearStoredToken,
  apiUrl,
  setOnAuthExpired,
  clearOnAuthExpired,
} from '../lib/api'
import type { AuthState, TokenResponse, UserResponse } from '../types/auth'

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<void>
  register: (username: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

async function authFetch<T>(endpoint: string, body: Record<string, string>): Promise<T> {
  const token = getStoredToken()
  const res = await fetch(apiUrl(endpoint), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(err.detail || '请求失败')
  }
  return res.json()
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(() => {
    const token = getStoredToken()
    return {
      token,
      username: null,
      isAuthenticated: !!token,
    }
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // 注册 token 过期回调（ky 拦截器触发）
    setOnAuthExpired(() => {
      clearStoredToken()
      setState({ token: null, username: null, isAuthenticated: false })
    })

    const token = getStoredToken()
    if (token) {
      verifyAuth(token)
    }

    return () => clearOnAuthExpired()
  }, [])

  async function verifyAuth(token: string) {
    try {
      const res = await fetch(apiUrl('auth/me'), {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const user: UserResponse = await res.json()
        setState({ token, username: user.username, isAuthenticated: true })
        return
      }

      // token 过期，尝试刷新
      const refreshRes = await fetch(apiUrl('auth/refresh'), {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (refreshRes.ok) {
        const data: TokenResponse = await refreshRes.json()
        setStoredToken(data.access_token)
        // 用新 token 重新验证身份
        const meRes = await fetch(apiUrl('auth/me'), {
          headers: { Authorization: `Bearer ${data.access_token}` },
        })
        if (meRes.ok) {
          const user: UserResponse = await meRes.json()
          setState({ token: data.access_token, username: user.username, isAuthenticated: true })
          return
        }
      }

      // 全失败
      clearStoredToken()
      setState({ token: null, username: null, isAuthenticated: false })
    } catch {
      clearStoredToken()
      setState({ token: null, username: null, isAuthenticated: false })
    }
  }

  const handleAuth = useCallback(async (endpoint: string, username: string, password: string) => {
    setLoading(true)
    try {
      const res = await authFetch<TokenResponse>(`auth/${endpoint}`, { username, password })
      setStoredToken(res.access_token)
      setState({
        token: res.access_token,
        username: res.username,
        isAuthenticated: true,
      })
    } finally {
      setLoading(false)
    }
  }, [])

  const login = useCallback((u: string, p: string) => handleAuth('login', u, p), [handleAuth])
  const register = useCallback((u: string, p: string) => handleAuth('register', u, p), [handleAuth])

  const logout = useCallback(() => {
    clearStoredToken()
    setState({ token: null, username: null, isAuthenticated: false })
  }, [])

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
