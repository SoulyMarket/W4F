import { motion, useReducedMotion } from 'framer-motion'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/Button'
import { Card } from '../../components/Card'
import { selectClass } from '../../components/formStyles'
import { StatusBadge } from '../../components/StatusBadge'
import { TableContainer } from '../../components/TableContainer'
import { useDouarsLookup } from '../douars/douarsApi'
import type { SupportedLanguage } from '../../i18n'
import { ApiError } from '../../lib/api'
import { formatDate } from '../../lib/formatDate'
import { problemTypeLabel } from '../../lib/reportFieldLabels'
import { reportStatusLabel, REPORT_STATUSES } from '../../lib/statusLabels'
import { useReportsList, type ReportDto } from './reportsApi'

const PAGE_SIZE = 20

export function ReportsListPage() {
  const { t, i18n } = useTranslation()
  const lang = i18n.language as SupportedLanguage
  const navigate = useNavigate()
  const prefersReducedMotion = useReducedMotion()

  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')
  const [sortByScore, setSortByScore] = useState(false)

  const { data, isPending, isError, error, refetch, isPlaceholderData } = useReportsList({
    page,
    pageSize: PAGE_SIZE,
    status: status || undefined,
    sortByScore,
  })
  const douars = useDouarsLookup()

  function updateStatus(value: string) {
    setStatus(value)
    setPage(1)
  }

  function douarNameFor(report: ReportDto): string {
    const douar = douars.data?.get(report.douar_id)
    return douar ? (lang === 'ar' ? douar.name_ar : douar.name_fr) : report.douar_id
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold tracking-tight text-foreground">{t('reports.title')}</h1>

      <div className="flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2 text-sm text-foreground">
          {t('reports.filter_status')}
          <select value={status} onChange={(event) => updateStatus(event.target.value)} className={selectClass}>
            <option value="">{t('reports.filter_all_statuses')}</option>
            {REPORT_STATUSES.map((value) => (
              <option key={value} value={value}>
                {reportStatusLabel(t, value)}
              </option>
            ))}
          </select>
        </label>

        <label className="flex items-center gap-2 text-sm text-foreground">
          <input
            type="checkbox"
            checked={sortByScore}
            onChange={(event) => {
              setSortByScore(event.target.checked)
              setPage(1)
            }}
            className="h-4 w-4 cursor-pointer accent-primary"
          />
          {t('reports.sort_by_score')}
        </label>
      </div>

      {isPending ? (
        <p className="text-foreground">{t('common.loading')}</p>
      ) : isError ? (
        <div className="flex flex-col items-start gap-2">
          <p className="text-destructive">
            {error instanceof ApiError ? error.message : t('reports.loading_error')}
          </p>
          <Button variant="secondary" onClick={() => void refetch()}>
            {t('common.retry')}
          </Button>
        </div>
      ) : data.items.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t('reports.empty')}</p>
      ) : (
        <div style={{ opacity: isPlaceholderData ? 0.6 : 1 }} className="transition-opacity">
          {/* Below `sm`, a 5-column table has no honest way to fit a
              375px frame — even with horizontal scroll, the first thing
              a viewer sees is a column cut off mid-word with no visible
              scroll affordance (found live). A stacked card per report
              is the standard responsive-table pattern instead of forcing
              a scroll no one would think to try. */}
          <div className="flex flex-col gap-2 sm:hidden">
            {data.items.map((report, index) => (
              <Card key={report.id} index={Math.min(index, 8)} interactive onClick={() => navigate(`/reports/${report.id}`)}>
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="truncate font-medium text-foreground">{douarNameFor(report)}</p>
                    <p className="truncate text-sm text-muted-foreground">{problemTypeLabel(t, report.problem_type)}</p>
                  </div>
                  <StatusBadge status={report.status} label={reportStatusLabel(t, report.status)} kind="report" />
                </div>
                <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                  <span>{t('reports.column_score')}: {report.score ?? '—'}</span>
                  <span>{formatDate(report.collected_at)}</span>
                </div>
              </Card>
            ))}
          </div>

          <div className="hidden sm:block">
            <TableContainer>
              <thead className="border-b border-border text-xs text-muted-foreground">
                <tr>
                  <th className="px-4 py-2 text-start font-medium">{t('reports.column_douar')}</th>
                  <th className="px-4 py-2 text-start font-medium">{t('reports.column_problem')}</th>
                  <th className="px-4 py-2 text-start font-medium">{t('reports.column_status')}</th>
                  <th className="px-4 py-2 text-start font-medium">{t('reports.column_score')}</th>
                  <th className="px-4 py-2 text-start font-medium">{t('reports.column_date')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.items.map((report, index) => {
                  const douarName = douarNameFor(report)
                  return (
                    <motion.tr
                      key={report.id}
                      initial={prefersReducedMotion ? undefined : { opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2, delay: prefersReducedMotion ? 0 : Math.min(index, 10) * 0.03 }}
                      onClick={() => navigate(`/reports/${report.id}`)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault()
                          navigate(`/reports/${report.id}`)
                        }
                      }}
                      role="button"
                      tabIndex={0}
                      aria-label={`${douarName} — ${problemTypeLabel(t, report.problem_type)}`}
                      className="cursor-pointer transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-inset focus:ring-ring"
                    >
                      <td className="px-4 py-2.5 text-foreground">{douarName}</td>
                      <td className="px-4 py-2.5 text-foreground">{problemTypeLabel(t, report.problem_type)}</td>
                      <td className="px-4 py-2.5">
                        <StatusBadge status={report.status} label={reportStatusLabel(t, report.status)} kind="report" />
                      </td>
                      <td className="px-4 py-2.5 text-foreground">{report.score ?? '—'}</td>
                      <td className="px-4 py-2.5 text-foreground">{formatDate(report.collected_at)}</td>
                    </motion.tr>
                  )
                })}
              </tbody>
            </TableContainer>
          </div>
        </div>
      )}

      {data && data.total > 0 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            {t('reports.page_info', {
              page: data.page,
              totalPages: Math.max(1, Math.ceil(data.total / data.page_size)),
              total: data.total,
            })}
          </span>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              {t('reports.previous_page')}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={page * data.page_size >= data.total}
              onClick={() => setPage((p) => p + 1)}
            >
              {t('reports.next_page')}
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
