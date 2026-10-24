import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../lib/api'

export interface ProjectDto {
  id: string
  report_id: string
  douar_id: string
  title: string
  solution_type: string
  description: string | null
  status: string
  owner_id: string
  planned_start: string | null
  planned_end: string | null
  actual_start: string | null
  actual_end: string | null
  progress_percent: number
  created_at: string
}

interface ProjectListDto {
  items: ProjectDto[]
  total: number
  page: number
  page_size: number
}

export interface ProjectUpdateDto {
  id: string
  project_id: string
  author_id: string
  old_status: string | null
  new_status: string | null
  progress_percent: number | null
  note: string | null
  created_at: string
}

export interface ProjectDetailDto extends ProjectDto {
  updates: ProjectUpdateDto[]
}

// The board shows every project at once grouped into status columns, so
// it fetches the API's own max page_size rather than paginating — a
// reasonable match for this prototype's seed data (same scale as the
// douars lookup), revisit if a territory ever has more than 100 at once.
export function useProjectsList() {
  return useQuery({
    queryKey: ['projects', 'list'],
    queryFn: () => apiFetch<ProjectListDto>('/projects?page_size=100'),
  })
}

// Section 8 (Android's own dossier detail): a report's "linked project"
// is resolved via /projects?report_id=, not a field on the report itself
// — `report_id` is unique on `projects`, so this is at most one project.
export function useProjectForReport(reportId: string, enabled: boolean) {
  return useQuery({
    queryKey: ['projects', 'for-report', reportId],
    queryFn: () => apiFetch<ProjectListDto>(`/projects?report_id=${reportId}`),
    select: (data) => data.items[0] ?? null,
    enabled,
  })
}

export function useProjectDetail(projectId: string) {
  return useQuery({
    queryKey: ['projects', 'detail', projectId],
    queryFn: () => apiFetch<ProjectDetailDto>(`/projects/${projectId}`),
  })
}

export interface CreateProjectInput {
  title: string
  solution_type: string
  description?: string
  planned_start?: string
  planned_end?: string
}

export function useCreateProjectFromReport(reportId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateProjectInput) =>
      apiFetch<ProjectDto>(`/reports/${reportId}/project`, { method: 'POST', body: input }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['reports', 'detail', reportId] })
      void queryClient.invalidateQueries({ queryKey: ['reports', 'list'] })
      void queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export interface AddProjectUpdateInput {
  new_status: string
  progress_percent?: number
  note?: string
}

export function useAddProjectUpdate(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: AddProjectUpdateInput) =>
      apiFetch<ProjectUpdateDto>(`/projects/${projectId}/updates`, { method: 'POST', body: input }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['projects', 'detail', projectId] })
      void queryClient.invalidateQueries({ queryKey: ['projects', 'list'] })
    },
  })
}
