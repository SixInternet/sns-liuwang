/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 覆盖 API 根地址（不含 /api/v1），例如 https://api.example.com */
  readonly VITE_API_BASE?: string
}
