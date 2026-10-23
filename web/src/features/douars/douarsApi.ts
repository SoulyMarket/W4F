import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../lib/api'

export interface DouarDto {
  id: string
  name_ar: string
  name_fr: string
  commune_id: string
  lat: number | null
  lon: number | null
  population: number | null
  families_count: number | null
  notes: string | null
}

interface DouarListDto {
  items: DouarDto[]
  total: number
  page: number
  page_size: number
}

// Simplification, documented rather than silently assumed: fetches a
// single page of up to 100 douars (the API's own max page_size) and
// builds an id→douar lookup from it, used to resolve a report's douar_id
// to a name without a dedicated "resolve one douar" round trip per row.
// Correct for this prototype's seed data (single digits of douars per
// territory); a territory with more than 100 douars would need real
// pagination here instead.
export function useDouarsLookup() {
  return useQuery({
    queryKey: ['douars', 'lookup'],
    queryFn: () => apiFetch<DouarListDto>('/douars?page_size=100'),
    select: (data) => new Map(data.items.map((douar) => [douar.id, douar])),
    staleTime: 5 * 60 * 1000,
  })
}
