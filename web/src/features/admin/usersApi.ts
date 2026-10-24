import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../lib/api'

export interface UserDto {
  id: string
  full_name: string
  email: string
  phone: string | null
  role: string
  preferred_language: string
  is_active: boolean
  last_login_at: string | null
  created_at: string
}

interface UserListDto {
  items: UserDto[]
  total: number
  page: number
  page_size: number
}

export function useUsersList() {
  return useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => apiFetch<UserListDto>('/users?page_size=100'),
  })
}

// For the audit log's actor-name column — same single-page lookup
// pattern as useDouarsLookup, reasonable at this prototype's user count.
export function useUsersLookup() {
  return useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => apiFetch<UserListDto>('/users?page_size=100'),
    select: (data) => new Map(data.items.map((user) => [user.id, user])),
    staleTime: 5 * 60 * 1000,
  })
}

export interface CreateUserInput {
  full_name: string
  email: string
  password: string
  role: string
}

export function useCreateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateUserInput) => apiFetch<UserDto>('/users', { method: 'POST', body: input }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['admin', 'users'] }),
  })
}

export function useDeactivateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) => apiFetch<UserDto>(`/users/${userId}/deactivate`, { method: 'POST' }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['admin', 'users'] }),
  })
}

export function useResetPassword() {
  return useMutation({
    mutationFn: (userId: string) =>
      apiFetch<{ temporary_password: string }>(`/users/${userId}/reset-password`, { method: 'POST' }),
  })
}
