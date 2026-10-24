import { useTranslation } from 'react-i18next'
import { Link, useParams } from 'react-router-dom'
import { StatusBadge } from '../../components/StatusBadge'
import { useAuth } from '../auth/AuthContext'
import { useDouarsLookup } from '../douars/douarsApi'
import { CreateProjectForm } from '../projects/CreateProjectForm'
import { useProjectForReport } from '../projects/projectsApi'
import type { SupportedLanguage } from '../../i18n'
import { ApiError } from '../../lib/api'
import { formatDate } from '../../lib/formatDate'
import { formatPoints } from '../../lib/formatNumber'
import { frequencyLabel, problemTypeLabel, severityLabel, waterSourceLabel } from '../../lib/reportFieldLabels'
import { reportStatusLabel, validationDecisionLabel } from '../../lib/statusLabels'
import { useReportDetail } from './reportsApi'
import { ValidationForm } from './ValidationForm'

// Section 5: only REJECTED/CONVERTED_TO_PROJECT block a new validation
// server-side (`_TERMINAL_STATUSES` in `backend/app/api/routes/
// validations.py`) — mirrored here so the form simply doesn't render
// instead of being submitted and bouncing off a 409.
const TERMINAL_REPORT_STATUSES = new Set(['rejected', 'converted_to_project'])

export function ReportDetailPage() {
  const { t, i18n } = useTranslation()
  const lang = i18n.language as SupportedLanguage
  const { user } = useAuth()
  const { reportId } = useParams<{ reportId: string }>()
  const { data: report, isPending, isError, error, refetch } = useReportDetail(reportId ?? '')
  const douars = useDouarsLookup()
  const linkedProject = useProjectForReport(reportId ?? '', report?.status === 'converted_to_project')

  if (isPending) return <p className="text-foreground">{t('common.loading')}</p>

  if (isError) {
    return (
      <div className="flex flex-col items-start gap-2">
        <p className="text-destructive">
          {error instanceof ApiError ? error.message : t('reports.detail_loading_error')}
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

  const douar = douars.data?.get(report.douar_id)
  const douarName = douar ? (lang === 'ar' ? douar.name_ar : douar.name_fr) : report.douar_id

  return (
    <div className="flex flex-col gap-6">
      <Link to="/reports" className="text-sm text-primary hover:underline">
        {t('reports.back_to_list')}
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold text-foreground">{t('reports.detail_title')}</h1>
          <p className="text-sm text-muted-foreground">{douarName}</p>
        </div>
        <StatusBadge status={report.status} label={reportStatusLabel(t, report.status)} kind="report" />
      </div>

      <Section title={t('reports.section_data')}>
        <dl className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
          <Field label={t('reports.water_source_label')} value={waterSourceLabel(t, report.water_source)} />
          <Field label={t('reports.problem_type_label')} value={problemTypeLabel(t, report.problem_type)} />
          <Field label={t('reports.frequency_label')} value={frequencyLabel(t, report.interruption_frequency)} />
          <Field label={t('reports.severity_label')} value={severityLabel(t, report.severity_reported)} />
          <Field label={t('reports.problem_started_on_label')} value={formatDate(report.problem_started_on)} />
          <Field label={t('reports.duration_days_label')} value={String(report.duration_days)} />
          <Field
            label={t('reports.alternative_source_label')}
            value={
              report.has_alternative_source
                ? t('reports.alternative_source_yes', { km: report.alternative_distance_km ?? '—' })
                : t('reports.alternative_source_no')
            }
          />
          <Field
            label={t('reports.water_quality_risk_label')}
            value={report.water_quality_risk ? t('reports.yes') : t('reports.no')}
          />
          <Field label={t('reports.affected_families_label')} value={String(report.affected_families)} />
          <Field label={t('reports.affected_people_label')} value={String(report.affected_people)} />
          {report.observations && (
            <div className="sm:col-span-2">
              <Field label={t('reports.observations_label')} value={report.observations} />
            </div>
          )}
        </dl>
      </Section>

      <Section title={t('reports.section_media')}>
        {report.media.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('reports.no_media')}</p>
        ) : (
          <div className="flex flex-wrap gap-3">
            {report.media.map((media) => (
              <div key={media.id} className="h-24 w-24 overflow-hidden rounded-lg border border-border bg-muted">
                {media.download_url && media.kind === 'photo' ? (
                  <img src={media.download_url} alt="" className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full w-full items-center justify-center p-2 text-center text-xs text-muted-foreground">
                    {media.download_url ? media.kind : t('reports.media_pending')}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title={t('reports.section_priority')}>
        {report.priority === null ? (
          <p className="text-sm text-muted-foreground">{t('reports.no_priority')}</p>
        ) : (
          <div className="flex flex-col gap-3">
            <p className="text-2xl font-semibold text-foreground">{report.priority.score}</p>
            <h3 className="text-sm font-semibold text-foreground">{t('reports.why_priority')}</h3>
            <table className="w-full text-start text-sm">
              <thead className="border-b border-border text-xs text-muted-foreground">
                <tr>
                  <th className="px-2 py-1 text-start font-medium">{t('reports.breakdown_criterion')}</th>
                  <th className="px-2 py-1 text-start font-medium">{t('reports.breakdown_points')}</th>
                  <th className="px-2 py-1 text-start font-medium">{t('reports.breakdown_reason')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {report.priority.breakdown.map((entry) => (
                  <tr key={entry.criterion}>
                    <td className="px-2 py-1.5 text-foreground">{entry.criterion}</td>
                    <td className="px-2 py-1.5 text-foreground">{formatPoints(entry.points)}</td>
                    <td className="px-2 py-1.5 text-foreground">{entry.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {user?.role === 'expert' && !TERMINAL_REPORT_STATUSES.has(report.status) && (
        <Section title={t('reports.validation_form_title')}>
          <ValidationForm reportId={report.id} />
        </Section>
      )}

      {user?.role === 'manager' && report.status === 'validated' && (
        <Section title={t('projects.create_form_title')}>
          <CreateProjectForm reportId={report.id} />
        </Section>
      )}

      {report.status === 'converted_to_project' && linkedProject.data && (
        <Link
          to={`/projects/${linkedProject.data.id}`}
          className="self-start text-sm text-primary hover:underline"
        >
          {t('projects.view_project')}
        </Link>
      )}

      <Section title={t('reports.section_validations')}>
        {report.validations.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('reports.no_validations')}</p>
        ) : (
          <ul className="flex flex-col gap-3">
            {report.validations.map((validation) => (
              <li key={validation.id} className="rounded-lg border border-border p-3">
                <div className="flex items-center justify-between gap-2">
                  <StatusBadge
                    status={validation.decision}
                    label={validationDecisionLabel(t, validation.decision)}
                    kind="report"
                  />
                  <span className="text-xs text-muted-foreground">{formatDate(validation.created_at)}</span>
                </div>
                {validation.comment && (
                  <Field label={t('reports.validation_comment_label')} value={validation.comment} compact />
                )}
                {validation.proposed_solution && (
                  <Field
                    label={t('reports.validation_proposed_solution_label')}
                    value={validation.proposed_solution}
                    compact
                  />
                )}
                {validation.urgency_opinion && (
                  <Field
                    label={t('reports.validation_urgency_label')}
                    value={severityLabel(t, validation.urgency_opinion)}
                    compact
                  />
                )}
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

function Field({ label, value, compact }: { label: string; value: string; compact?: boolean }) {
  return (
    <div className={compact ? 'mt-2' : undefined}>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm text-foreground">{value}</dd>
    </div>
  )
}
