export interface TokenResponse {
  access_token: string
  token_type: string
  username: string
}

export interface UserResponse {
  id: string
  username: string
  email: string | null
  is_active: boolean
  created_at: string
}

export interface AuthState {
  token: string | null
  username: string | null
  isAuthenticated: boolean
}
