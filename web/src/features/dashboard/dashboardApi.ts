import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../lib/api'

export interface DouarSummaryDto {
  id: string
  name_ar: string
  name_fr: string
  score: number
  report_count: number
}

export interface DashboardSummaryDto {
  total_douars: number
  reports_by_status: Record<string, number>
  priority_douars: DouarSummaryDto[]
  projects_by_status: Record<string, number>
  recurring_problem_douars: DouarSummaryDto[]
}

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => apiFetch<DashboardSummaryDto>('/dashboard/summary'),
  })
}
