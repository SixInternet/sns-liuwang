import ky from 'ky'

const TOKEN_KEY = 'sns_token'

/**
 * API 根地址（不含 /api/v1）。
 * - 优先 `VITE_API_BASE`（适合生产或自定义域名）
 * - 否则与当前页面同主机、8001 端口（局域网用 IP 打开前端时也能打到同一台机器上的后端）
 */
export function getApiBase(): string {
  const fromEnv = import.meta.env.VITE_API_BASE?.trim()
  if (fromEnv) {
    return fromEnv.replace(/\/$/, '')
  }
  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location
    return `${protocol}//${hostname}:8001`
  }
  return 'http://localhost:8001'
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setStoredToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearStoredToken() {
  localStorage.removeItem(TOKEN_KEY)
}

// ── Auth expiry callback ─────────────────────────────────
let _onAuthExpired: (() => void) | null = null

export function setOnAuthExpired(cb: () => void) {
  _onAuthExpired = cb
}

export function clearOnAuthExpired() {
  _onAuthExpired = null
}

async function tryRefreshToken(): Promise<string | null> {
  const oldToken = getStoredToken()
  if (!oldToken) return null
  try {
    const res = await fetch(`${getApiBase()}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${oldToken}` },
    })
    if (!res.ok) return null
    const data = await res.json()
    setStoredToken(data.access_token)
    return data.access_token
  } catch {
    return null
  }
}

export const api = ky.create({
  // 必须保留末尾 /，否则相对路径「cards」会按 URL 规范替换掉「v1」段，误请求 /api/cards
  baseUrl: `${getApiBase()}/api/v1/`,
  hooks: {
    beforeRequest: [
      ({ request }) => {
        const token = getStoredToken()
        if (token) {
          request.headers.set('Authorization', `Bearer ${token}`)
        }
      },
    ],
    afterResponse: [
      async ({ request, response }) => {
        if (response.status !== 401) return response

        // 避免无限重试
        if (request.headers.get('X-Retry-Count') === '1') {
          clearStoredToken()
          _onAuthExpired?.()
          return response
        }

        const newToken = await tryRefreshToken()
        if (newToken) {
          // 用新 token 重试
          const req = new Request(request)
          req.headers.set('Authorization', `Bearer ${newToken}`)
          req.headers.set('X-Retry-Count', '1')
          return fetch(req)
        }

        // 刷新失败
        clearStoredToken()
        _onAuthExpired?.()
        return response
      },
    ],
  },
})

export function apiUrl(path: string): string {
  const p = path.replace(/^\//, '')
  return `${getApiBase()}/api/v1/${p}`
}
