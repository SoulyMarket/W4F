import { useTranslation } from 'react-i18next'
import { Link, useParams } from 'react-router-dom'
import { StatusBadge } from '../../components/StatusBadge'
import { useAuth } from '../auth/AuthContext'
import { useDouarsLookup } from '../douars/douarsApi'
import type { SupportedLanguage } from '../../i18n'
import { ApiError } from '../../lib/api'
import { formatDate } from '../../lib/formatDate'
import { solutionTypeLabel } from '../../lib/reportFieldLabels'
import { projectStatusLabel } from '../../lib/statusLabels'
import { useProjectDetail } from './projectsApi'
import { ProjectStatusUpdateForm } from './ProjectStatusUpdateForm'

export function ProjectDetailPage() {
  const { t, i18n } = useTranslation()
  const lang = i18n.language as SupportedLanguage
  const { user } = useAuth()
  const { projectId } = useParams<{ projectId: string }>()
  const { data: project, isPending, isError, error, refetch } = useProjectDetail(projectId ?? '')
  const douars = useDouarsLookup()

  if (isPending) return <p className="text-foreground">{t('common.loading')}</p>

  if (isError) {
    return (
      <div className="flex flex-col items-start gap-2">
        <p className="text-destructive">
          {error instanceof ApiError ? error.message : t('projects.detail_loading_error')}
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

  const douar = douars.data?.get(project.douar_id)
  const douarName = douar ? (lang === 'ar' ? douar.name_ar : douar.name_fr) : project.douar_id

  return (
    <div className="flex flex-col gap-6">
      <Link to="/projects" className="text-sm text-primary hover:underline">
        {t('projects.back_to_board')}
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold text-foreground">{project.title}</h1>
          <p className="text-sm text-muted-foreground">{douarName}</p>
        </div>
        <StatusBadge status={project.status} label={projectStatusLabel(t, project.status)} kind="project" />
      </div>

      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary" style={{ width: `${project.progress_percent}%` }} />
      </div>
      <p className="-mt-4 text-xs text-muted-foreground">
        {t('projects.progress_label', { percent: project.progress_percent })}
      </p>

      <Section title={t('projects.section_data')}>
        <dl className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
          <Field label={t('projects.solution_type_label')} value={solutionTypeLabel(t, project.solution_type)} />
          {project.description && <Field label={t('projects.description_label')} value={project.description} />}
          {project.planned_start && (
            <Field label={t('projects.planned_start_label')} value={formatDate(project.planned_start)} />
          )}
          {project.planned_end && (
            <Field label={t('projects.planned_end_label')} value={formatDate(project.planned_end)} />
          )}
          {project.actual_start && (
            <Field label={t('projects.actual_start_label')} value={formatDate(project.actual_start)} />
          )}
          {project.actual_end && (
            <Field label={t('projects.actual_end_label')} value={formatDate(project.actual_end)} />
          )}
        </dl>
      </Section>

      {user?.role === 'manager' && (
        <Section title={t('projects.update_form_title')}>
          <ProjectStatusUpdateForm
            projectId={project.id}
            currentStatus={project.status}
            currentProgress={project.progress_percent}
          />
        </Section>
      )}

      <Section title={t('projects.section_updates')}>
        {project.updates.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('projects.no_updates')}</p>
        ) : (
          <ul className="flex flex-col gap-3">
            {project.updates.map((update) => (
              <li key={update.id} className="rounded-lg border border-border p-3">
                <div className="flex items-center justify-between gap-2">
                  {update.new_status && (
                    <StatusBadge status={update.new_status} label={projectStatusLabel(t, update.new_status)} kind="project" />
                  )}
                  <span className="text-xs text-muted-foreground">{formatDate(update.created_at)}</span>
                </div>
                {update.progress_percent !== null && (
                  <p className="mt-2 text-sm text-foreground">
                    {t('projects.progress_label', { percent: update.progress_percent })}
                  </p>
                )}
                {update.note && <p className="mt-1 text-sm text-foreground">{update.note}</p>}
              </li>
            ))}
          </ul>
        )}
      </Section>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-white/60 p-4 shadow-sm dark:bg-white/5">
      <h2 className="mb-3 text-sm font-semibold text-foreground">{title}</h2>
      {children}
    </div>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm text-foreground">{value}</dd>
    </div>
  )
}
