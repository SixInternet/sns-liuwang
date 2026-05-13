export interface Source {
  id: string
  title: string
  url?: string | null
  content_markdown?: string | null
  content_hash?: string | null
  diff_log?: string | null
  status: string         // pending/refined/failed
  collector?: string | null
  collected_at: string
  refined_at?: string | null
  card_count: number
}

export interface SourceListResponse {
  items: Source[]
  total: number
}

export interface InfoCard {
  id: string
  title: string
  summary?: string | null
  source_url?: string | null
  source_context?: string | null
  category?: string | null
  status: string
  collected_at: string
  source_id?: string | null
  collector?: string | null
  raw_screenshot_url?: string | null
}
