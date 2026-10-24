import { useTranslation } from 'react-i18next'
import { Button } from '../../components/Button'
import { Card } from '../../components/Card'
import { StatusBarChart, type StatusBarChartEntry } from '../../components/charts/StatusBarChart'
import type { SupportedLanguage } from '../../i18n'
import { ApiError } from '../../lib/api'
import { projectStatusLabel, reportStatusLabel } from '../../lib/statusLabels'
import { useDashboardSummary, type DouarSummaryDto } from './dashboardApi'

// Cycled by index, not tied to status meaning — each bar already carries
// its own text label, so color only needs to make adjacent bars tell
// apart at a glance (chart a11y guidance: never rely on color alone).
const CHART_PALETTE = ['#0284c7', '#06b6d4', '#0891b2', '#f59e0b', '#dc2626', '#16a34a', '#7c3aed']

function localizedDouarName(douar: DouarSummaryDto, lang: SupportedLanguage): string {
  return lang === 'ar' ? douar.name_ar : douar.name_fr
}

export function DashboardPage() {
  const { t, i18n } = useTranslation()
  const lang = i18n.language as SupportedLanguage
  const { data, isPending, isError, error, refetch } = useDashboardSummary()

  if (isPending) {
    return <p className="text-foreground">{t('common.loading')}</p>
  }

  if (isError) {
    return (
      <div className="flex flex-col items-start gap-2">
        <p className="text-destructive">{error instanceof ApiError ? error.message : t('dashboard.loading_error')}</p>
        <Button variant="secondary" onClick={() => void refetch()}>
          {t('common.retry')}
        </Button>
      </div>
    )
  }

  const reportEntries: StatusBarChartEntry[] = Object.entries(data.reports_by_status).map(
    ([status, count], index) => ({
      status,
      count,
      label: reportStatusLabel(t, status),
      color: CHART_PALETTE[index % CHART_PALETTE.length],
    }),
  )
  const projectEntries: StatusBarChartEntry[] = Object.entries(data.projects_by_status).map(
    ([status, count], index) => ({
      status,
      count,
      label: projectStatusLabel(t, status),
      color: CHART_PALETTE[index % CHART_PALETTE.length],
    }),
  )

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold tracking-tight text-foreground">{t('dashboard.title')}</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <KpiCard index={0} label={t('dashboard.total_douars')} value={data.total_douars} />
        <KpiCard index={1} label={t('dashboard.priority_douars')} value={data.priority_douars.length} />
        <KpiCard index={2} label={t('dashboard.recurring_problem_douars')} value={data.recurring_problem_douars.length} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard index={3} title={t('dashboard.reports_by_status')}>
          <StatusBarChart data={reportEntries} />
        </ChartCard>
        <ChartCard index={4} title={t('dashboard.projects_by_status')}>
          <StatusBarChart data={projectEntries} />
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <DouarListCard
          index={5}
          title={t('dashboard.priority_douars')}
          hint={t('dashboard.priority_douars_hint')}
          emptyMessage={t('dashboard.priority_douars_empty')}
          douars={data.priority_douars}
          lang={lang}
          scoreLabel={t('dashboard.score')}
          reportCountLabel={t('dashboard.report_count')}
        />
        <DouarListCard
          index={6}
          title={t('dashboard.recurring_problem_douars')}
          hint={t('dashboard.recurring_problem_douars_hint')}
          emptyMessage={t('dashboard.recurring_problem_douars_empty')}
          douars={data.recurring_problem_douars}
          lang={lang}
          scoreLabel={t('dashboard.score')}
          reportCountLabel={t('dashboard.report_count')}
        />
      </div>
    </div>
  )
}

function KpiCard({ index, label, value }: { index: number; label: string; value: number }) {
  return (
    <Card index={index}>
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-foreground">{value}</p>
    </Card>
  )
}

function ChartCard({ index, title, children }: { index: number; title: string; children: React.ReactNode }) {
  return (
    <Card index={index}>
      <h2 className="mb-3 text-sm font-semibold text-foreground">{title}</h2>
      {children}
    </Card>
  )
}

function DouarListCard({
  index,
  title,
  hint,
  emptyMessage,
  douars,
  lang,
  scoreLabel,
  reportCountLabel,
}: {
  index: number
  title: string
  hint: string
  emptyMessage: string
  douars: DouarSummaryDto[]
  lang: SupportedLanguage
  scoreLabel: string
  reportCountLabel: string
}) {
  return (
    <Card index={index}>
      <h2 className="text-sm font-semibold text-foreground">{title}</h2>
      <p className="mb-3 text-xs text-muted-foreground">{hint}</p>
      {douars.length === 0 ? (
        <p className="text-sm text-muted-foreground">{emptyMessage}</p>
      ) : (
        <ul className="flex flex-col divide-y divide-border">
          {douars.map((douar) => (
            <li key={douar.id} className="flex items-center justify-between py-2 text-sm">
              <span className="text-foreground">{localizedDouarName(douar, lang)}</span>
              <span className="text-muted-foreground">
                {scoreLabel} {douar.score} · {reportCountLabel} {douar.report_count}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
