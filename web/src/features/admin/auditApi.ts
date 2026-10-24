import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../lib/api'

export interface AuditLogEntryDto {
  id: string
  actor_id: string | null
  action: string
  entity_type: string
  entity_id: string | null
  old_value: Record<string, unknown> | null
  new_value: Record<string, unknown> | null
  ip: string | null
  user_agent: string | null
  created_at: string
}

interface AuditLogListDto {
  items: AuditLogEntryDto[]
  total: number
  page: number
  page_size: number
}

export interface AuditLogFilters {
  page: number
  pageSize: number
  entityType?: string
  action?: string
}

function buildQuery(filters: AuditLogFilters): string {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.pageSize))
  if (filters.entityType) params.set('entity_type', filters.entityType)
  if (filters.action) params.set('action', filters.action)
  return params.toString()
}

export function useAuditLog(filters: AuditLogFilters) {
  return useQuery({
    queryKey: ['admin', 'audit', filters],
    queryFn: () => apiFetch<AuditLogListDto>(`/audit?${buildQuery(filters)}`),
    placeholderData: (previous) => previous,
  })
}
