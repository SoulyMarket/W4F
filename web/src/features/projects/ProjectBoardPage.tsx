import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import type { SupportedLanguage } from '../../i18n'
import { ApiError } from '../../lib/api'
import { PROJECT_STATUSES, projectStatusLabel } from '../../lib/statusLabels'
import { useDouarsLookup } from '../douars/douarsApi'
import { useProjectsList, type ProjectDto } from './projectsApi'

// A Kanban-style board, one column per ProjectStatus in its natural
// pipeline order — a plain flex row inherits `dir` from
// `html[dir]` (set by the i18n module), so the column order flips to
// right-to-left for Arabic automatically, same as the header layout.
export function ProjectBoardPage() {
  const { t, i18n } = useTranslation()
  const lang = i18n.language as SupportedLanguage
  const navigate = useNavigate()
  const { data, isPending, isError, error, refetch } = useProjectsList()
  const douars = useDouarsLookup()

  if (isPending) return <p className="text-foreground">{t('common.loading')}</p>

  if (isError) {
    return (
      <div className="flex flex-col items-start gap-2">
        <p className="text-destructive">
          {error instanceof ApiError ? error.message : t('projects.loading_error')}
        </p>
        <button
          type="button"
          onClick={() => void refetch()}
          className="h-9 cursor-pointer rounded-md border border-border px-3 text-sm font-medium text-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {t('common.retry')}
        </button>
      </div>
    )
  }

  const byStatus = new Map<string, ProjectDto[]>()
  for (const project of data.items) {
    const list = byStatus.get(project.status) ?? []
    list.push(project)
    byStatus.set(project.status, list)
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold text-foreground">{t('projects.title')}</h1>

      <div className="flex gap-4 overflow-x-auto pb-2">
        {PROJECT_STATUSES.map((status) => {
          const projects = byStatus.get(status) ?? []
          return (
            <div key={status} className="flex w-64 shrink-0 flex-col gap-2 rounded-xl border border-border bg-white/40 p-3 dark:bg-white/5">
              <h2 className="text-sm font-semibold text-foreground">
                {projectStatusLabel(t, status)} <span className="text-muted-foreground">({projects.length})</span>
              </h2>
              {projects.length === 0 ? (
                <p className="text-xs text-muted-foreground">{t('projects.empty_column')}</p>
              ) : (
                projects.map((project) => {
                  const douar = douars.data?.get(project.douar_id)
                  const douarName = douar ? (lang === 'ar' ? douar.name_ar : douar.name_fr) : project.douar_id
                  return (
                    <button
                      key={project.id}
                      type="button"
                      onClick={() => navigate(`/projects/${project.id}`)}
                      className="cursor-pointer rounded-lg border border-border bg-white/70 p-3 text-start shadow-sm transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring dark:bg-white/10"
                    >
                      <p className="text-sm font-medium text-foreground">{project.title}</p>
                      <p className="text-xs text-muted-foreground">{douarName}</p>
                      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{ width: `${project.progress_percent}%` }}
                        />
                      </div>
                    </button>
                  )
                })
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
