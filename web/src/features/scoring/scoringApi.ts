import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../lib/api'

// Mirrors `backend/app/services/scoring.py`'s DEFAULT_WEIGHTS keys —
// the backend itself validates a PUT against this exact set (section
// 7's scoring config), so a web-side drift would just surface as a 422
// rather than silently accepting an unknown criterion.
export const SCORING_CRITERIA = [
  'people_affected',
  'duration',
  'frequency',
  'no_alternative',
  'distance',
  'severity',
  'water_quality_risk',
] as const
export type ScoringCriterion = (typeof SCORING_CRITERIA)[number]

export interface ScoringConfigDto {
  id: string
  weights: Record<string, number>
  is_active: boolean
  created_by: string
  created_at: string
}

export interface RecomputeResultDto {
  config: ScoringConfigDto
  reports_recomputed: number
}

export function useScoringConfig() {
  return useQuery({
    queryKey: ['scoring-config'],
    queryFn: () => apiFetch<ScoringConfigDto>('/scoring-config'),
  })
}

export function useUpdateScoringConfig() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (weights: Record<string, number>) =>
      apiFetch<RecomputeResultDto>('/scoring-config', { method: 'PUT', body: { weights } }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['scoring-config'] }),
  })
}
