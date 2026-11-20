import { BuildingsIcon, TrendUpIcon, WarningCircleIcon, type Icon } from '@phosphor-icons/react'
import { useTranslation } from 'react-i18next'
import { Button } from '../../components/Button'
import { Card } from '../../components/Card'
import { StatusBarChart, type StatusBarChartEntry } from '../../components/charts/StatusBarChart'
import { EmptyState } from '../../components/EmptyState'
import { Skeleton } from '../../components/Skeleton'
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
    return <DashboardSkeleton />
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
      <h1 className="text-2xl font-bold tracking-tight text-foreground font-heading">{t('dashboard.title')}</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <KpiCard index={0} icon={BuildingsIcon} label={t('dashboard.total_douars')} value={data.total_douars} />
        <KpiCard
          index={1}
          icon={WarningCircleIcon}
          tone="destructive"
          label={t('dashboard.priority_douars')}
          value={data.priority_douars.length}
        />
        <KpiCard
          index={2}
          icon={TrendUpIcon}
          tone="accent"
          label={t('dashboard.recurring_problem_douars')}
          value={data.recurring_problem_douars.length}
        />
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

function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-6" aria-hidden="true">
      <Skeleton className="h-8 w-48" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <Card key={i} index={i}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex flex-col gap-2">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-8 w-16" />
              </div>
              <Skeleton className="h-10 w-10 shrink-0 rounded-full" />
            </div>
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {[3, 4].map((i) => (
          <Card key={i} index={i}>
            <Skeleton className="mb-4 h-4 w-40" />
            <div className="flex flex-col gap-3">
              {[0, 1, 2].map((row) => (
                <div key={row} className="flex items-center gap-3">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-5 flex-1 rounded-full" />
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {[5, 6].map((i) => (
          <Card key={i} index={i}>
            <Skeleton className="mb-1 h-4 w-40" />
            <Skeleton className="mb-4 h-3 w-56" />
            <div className="flex flex-col gap-3">
              {[0, 1, 2].map((row) => (
                <Skeleton key={row} className="h-5 w-full" />
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}

const KPI_TONE_CLASSES = {
  primary: 'bg-primary/10 text-primary',
  destructive: 'bg-destructive/10 text-destructive',
  accent: 'bg-accent/10 text-accent',
} as const

function KpiCard({
  index,
  icon: IconComponent,
  tone = 'primary',
  label,
  value,
}: {
  index: number
  icon: Icon
  tone?: keyof typeof KPI_TONE_CLASSES
  label: string
  value: number
}) {
  return (
    <Card index={index}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="mt-1 font-heading text-3xl font-semibold text-foreground">{value}</p>
        </div>
        <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${KPI_TONE_CLASSES[tone]}`}>
          <IconComponent size={20} weight="bold" aria-hidden="true" />
        </span>
      </div>
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
        <EmptyState message={emptyMessage} />
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
