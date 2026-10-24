import { motion, useReducedMotion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/Button'
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
  const prefersReducedMotion = useReducedMotion()
  const { data, isPending, isError, error, refetch } = useProjectsList()
  const douars = useDouarsLookup()

  if (isPending) return <p className="text-foreground">{t('common.loading')}</p>

  if (isError) {
    return (
      <div className="flex flex-col items-start gap-2">
        <p className="text-destructive">
          {error instanceof ApiError ? error.message : t('projects.loading_error')}
        </p>
        <Button variant="secondary" onClick={() => void refetch()}>
          {t('common.retry')}
        </Button>
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
      <h1 className="text-2xl font-bold tracking-tight text-foreground">{t('projects.title')}</h1>

      <div className="flex gap-4 overflow-x-auto pb-2">
        {PROJECT_STATUSES.map((status, columnIndex) => {
          const projects = byStatus.get(status) ?? []
          return (
            <motion.div
              key={status}
              initial={prefersReducedMotion ? undefined : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: prefersReducedMotion ? 0 : columnIndex * 0.05 }}
              className="flex w-64 shrink-0 flex-col gap-2 rounded-xl border border-border bg-white/40 p-3 dark:bg-white/5"
            >
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
                    <motion.button
                      key={project.id}
                      type="button"
                      onClick={() => navigate(`/projects/${project.id}`)}
                      whileHover={prefersReducedMotion ? undefined : { y: -2, scale: 1.01 }}
                      whileTap={prefersReducedMotion ? undefined : { scale: 0.98 }}
                      className="cursor-pointer rounded-lg border border-border bg-white/70 p-3 text-start shadow-sm transition-shadow hover:shadow-md focus:outline-none focus:ring-2 focus:ring-ring dark:bg-white/10"
                    >
                      <p className="break-words text-sm font-medium text-foreground">{project.title}</p>
                      <p className="truncate text-xs text-muted-foreground">{douarName}</p>
                      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                        <motion.div
                          className="h-full rounded-full bg-primary"
                          initial={{ width: 0 }}
                          animate={{ width: `${project.progress_percent}%` }}
                          transition={{ duration: 0.5, ease: 'easeOut' }}
                        />
                      </div>
                    </motion.button>
                  )
                })
              )}
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
