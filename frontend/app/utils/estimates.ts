export type GarageTier = 'local' | 'workshop' | 'dealer'
export type Confidence = 'high' | 'medium' | 'low' | 'insufficient'

export interface EstimateItem {
  id: number
  job_code: string
  kind: 'part' | 'labour'
  description: string
  description_bn?: string
  quantity: number
  price_min: number | null
  price_max: number | null
  price_likely?: number | null
  price_count: number
}

export interface EstimateSummary {
  id: number
  vehicle_id: number | null
  vehicle_label: string
  problem_text: string
  garage_tier: GarageTier
  total_min: number
  total_likely: number
  total_max: number
  confidence: Confidence
  method: 'ai' | 'manual'
  created_at: string
}

export interface EstimateDetail extends EstimateSummary {
  explanation: string
  warnings: string[]
  items: EstimateItem[]
  jobs?: { code: string; name_en: string; name_bn: string; safety_critical: boolean }[]
}

export interface JobOption {
  code: string
  name_en: string
  name_bn: string
  safety_critical: boolean
}

export const GARAGE_TIERS: { value: GarageTier; label: string; hint: string }[] = [
  { value: 'local', label: 'Local garage', hint: 'Roadside or neighbourhood mechanic' },
  { value: 'workshop', label: 'Workshop', hint: 'Established multi-bay workshop' },
  { value: 'dealer', label: 'Service centre', hint: 'Dealer or brand service centre' },
]

export const CONFIDENCE_TEXT: Record<Confidence, string> = {
  high: 'High confidence',
  medium: 'Medium confidence',
  low: 'Low confidence',
  insufficient: 'Not enough data',
}

export function tierLabel(tier: string) {
  return GARAGE_TIERS.find((t) => t.value === tier)?.label ?? tier
}

export function formatTaka(value: number | null | undefined) {
  if (value === null || value === undefined) return '—'
  return `৳${value.toLocaleString('en-IN')}`
}

export function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}
