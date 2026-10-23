import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../lib/api'

export interface ReportDto {
  id: string
  douar_id: string
  moqaddem_id: string
  water_source: string
  problem_type: string
  problem_started_on: string
  duration_days: number
  interruption_frequency: string
  has_alternative_source: boolean
  alternative_distance_km: number | null
  severity_reported: string
  water_quality_risk: boolean
  affected_families: number
  affected_people: number
  observations: string | null
  lat: number | null
  lon: number | null
  location_accuracy_m: number | null
  collected_at: string
  synced_at: string | null
  status: string
  version: number
  score: number | null
}

export interface ReportListDto {
  items: ReportDto[]
  total: number
  page: number
  page_size: number
}

export interface ReportMediaDto {
  id: string
  kind: string
  mime_type: string
  upload_status: string
  download_url: string | null
}

export interface PriorityBreakdownEntryDto {
  criterion: string
  value: unknown
  weight: number
  points: number
  reason_key: string
  reason_params: Record<string, unknown>
  reason: string
}

export interface PriorityDto {
  score: number
  breakdown: PriorityBreakdownEntryDto[]
  computed_at: string
}

export interface ValidationDto {
  id: string
  expert_id: string
  decision: string
  comment: string | null
  proposed_solution: string | null
  urgency_opinion: string | null
  created_at: string
}

export interface ReportDetailDto extends ReportDto {
  media: ReportMediaDto[]
  priority: PriorityDto | null
  validations: ValidationDto[]
}

export interface ReportListFilters {
  status?: string
  page: number
  pageSize: number
  sortByScore: boolean
}

function buildQuery(filters: ReportListFilters): string {
  const params = new URLSearchParams()
  if (filters.status) params.set('status', filters.status)
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.pageSize))
  if (filters.sortByScore) params.set('sort_by_score', 'true')
  return params.toString()
}

export function useReportsList(filters: ReportListFilters) {
  return useQuery({
    queryKey: ['reports', 'list', filters],
    queryFn: () => apiFetch<ReportListDto>(`/reports?${buildQuery(filters)}`),
    placeholderData: (previous) => previous,
  })
}

export function useReportDetail(reportId: string) {
  return useQuery({
    queryKey: ['reports', 'detail', reportId],
    queryFn: () => apiFetch<ReportDetailDto>(`/reports/${reportId}`),
  })
}
