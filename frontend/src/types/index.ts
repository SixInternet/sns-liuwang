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

/* ── Search Source ─────────────────────────── */

export interface SearchSource {
  id: string
  title: string
  base_url: string
  created_at?: string | null
}

export interface SearchSourceListResponse {
  items: SearchSource[]
  total: number
}

export interface PaginatedSearchSources {
  items: SearchSource[]
  total: number
  page: number
  page_size: number
}

/* ── Topic ─────────────────────────────────── */

export interface TopicItem {
  id: string
  name: string
  description?: string | null
  keywords?: string[] | null
  search_depth?: number | null
  schedule_type?: string | null
  schedule_times?: string[] | null
  auto_refine?: boolean | null
  enabled?: boolean | null
  search_sources?: SearchSource[] | null
  created_at?: string | null
  updated_at?: string | null
}

export interface TopicListResponse {
  items: TopicItem[]
  total: number
}

export interface TopicCreateRequest {
  name: string
  description?: string
  keywords?: string[]
  search_depth?: number
  schedule_type?: string
  schedule_times?: string[]
  auto_refine?: boolean
  enabled?: boolean
  search_source_ids?: string[]
}

/* ── Sources Grouped ────────────────────────── */

export interface SourceGroupItem {
  search_source: {
    id: string
    title: string
    base_url: string
    domain: string
  }
  sources: Source[]
  total: number
  page: number
  page_size: number
}

export interface SourcesGroupedResponse {
  groups: SourceGroupItem[]
  uncategorized: { sources: Source[]; total: number; page: number; page_size: number } | null
  total_groups: number
}

/* ── Collection Run ────────────────────────── */

export interface CollectionRun {
  id: string
  topic_id?: string | null
  topic_name?: string | null
  status: string
  started_at?: string | null
  finished_at?: string | null
}

export interface CollectionRunListResponse {
  items: CollectionRun[]
  total: number
}

export interface CollectionProgress {
  run_id: string
  progress_type: string
  progress_pct: number
  step_text?: string | null
  estimated_remaining?: string | null
  created_at?: string | null
}
