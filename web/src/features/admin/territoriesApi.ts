import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../lib/api'

export interface TerritoryDto {
  id: string
  name_ar: string
  name_fr: string
  level: string
  parent_id: string | null
}

export function useTerritoriesList() {
  return useQuery({
    queryKey: ['territories'],
    queryFn: () => apiFetch<TerritoryDto[]>('/territories'),
  })
}

// Same single-page lookup pattern as useDouarsLookup/useUsersLookup —
// reasonable at this prototype's territory count (a handful of
// provinces/communes).
export function useTerritoriesLookup() {
  return useQuery({
    queryKey: ['territories'],
    queryFn: () => apiFetch<TerritoryDto[]>('/territories'),
    select: (data) => new Map(data.map((territory) => [territory.id, territory])),
    staleTime: 5 * 60 * 1000,
  })
}

export interface CreateTerritoryInput {
  name_ar: string
  name_fr: string
  level: string
  parent_id?: string | null
}

export function useCreateTerritory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateTerritoryInput) =>
      apiFetch<TerritoryDto>('/territories', { method: 'POST', body: input }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['territories'] }),
  })
}

export function useUpdateTerritory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string; name_ar?: string; name_fr?: string; parent_id?: string | null }) =>
      apiFetch<TerritoryDto>(`/territories/${id}`, { method: 'PATCH', body }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['territories'] }),
  })
}

export function useSetUserTerritories() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, territoryIds }: { userId: string; territoryIds: string[] }) =>
      apiFetch<{ ok: boolean }>(`/users/${userId}/territories`, {
        method: 'PUT',
        body: { territory_ids: territoryIds },
      }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['admin', 'users'] }),
  })
}
