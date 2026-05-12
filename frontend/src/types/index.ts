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
