import { HTTPError } from 'ky'

/** Resolve ky HTTPError or generic Error to a user-facing Chinese message */
export async function resolveErrorMessage(err: unknown): Promise<string> {
  if (err instanceof HTTPError) {
    try {
      const body = (await err.response.json()) as { detail?: unknown }
      const d = body.detail
      if (typeof d === 'string') return d
      if (Array.isArray(d))
        return d.map((x) => (typeof x === 'object' ? JSON.stringify(x) : String(x))).join('；')
    } catch {
      /* ignore parse failure */
    }
  }
  return err instanceof Error ? err.message : '操作失败，请稍后重试'
}
