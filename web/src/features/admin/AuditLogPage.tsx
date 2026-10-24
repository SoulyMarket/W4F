import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ApiError } from '../../lib/api'
import { formatDate } from '../../lib/formatDate'
import { AUDIT_ACTIONS, auditActionLabel } from '../../lib/statusLabels'
import { useAuditLog } from './auditApi'
import { useUsersLookup } from './usersApi'

const PAGE_SIZE = 20

export function AuditLogPage() {
  const { t } = useTranslation()
  const [page, setPage] = useState(1)
  const [entityType, setEntityType] = useState('')
  const [action, setAction] = useState('')
  const { data, isPending, isError, error, refetch, isPlaceholderData } = useAuditLog({
    page,
    pageSize: PAGE_SIZE,
    entityType: entityType || undefined,
    action: action || undefined,
  })
  const users = useUsersLookup()

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold text-foreground">{t('admin.audit_title')}</h1>

      <div className="flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2 text-sm text-foreground">
          {t('admin.audit_filter_entity_type')}
          <input
            value={entityType}
            onChange={(event) => {
              setEntityType(event.target.value)
              setPage(1)
            }}
            placeholder="report, project, user…"
            className="h-9 rounded-md border border-border bg-background px-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </label>

        <label className="flex items-center gap-2 text-sm text-foreground">
          {t('admin.audit_filter_action')}
          <select
            value={action}
            onChange={(event) => {
              setAction(event.target.value)
              setPage(1)
            }}
            className="h-9 cursor-pointer rounded-md border border-border bg-background px-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">{t('admin.audit_filter_all')}</option>
            {AUDIT_ACTIONS.map((value) => (
              <option key={value} value={value}>
                {auditActionLabel(t, value)}
              </option>
            ))}
          </select>
        </label>
      </div>

      {isPending ? (
        <p className="text-foreground">{t('common.loading')}</p>
      ) : isError ? (
        <div className="flex flex-col items-start gap-2">
          <p className="text-destructive">
            {error instanceof ApiError ? error.message : t('admin.audit_loading_error')}
          </p>
          <button
            type="button"
            onClick={() => void refetch()}
            className="h-9 cursor-pointer rounded-md border border-border px-3 text-sm font-medium text-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {t('common.retry')}
          </button>
        </div>
      ) : data.items.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t('admin.audit_empty')}</p>
      ) : (
        <div
          className="overflow-hidden rounded-xl border border-border bg-white/60 shadow-sm transition-opacity dark:bg-white/5"
          style={{ opacity: isPlaceholderData ? 0.6 : 1 }}
        >
          <table className="w-full text-start text-sm">
            <thead className="border-b border-border text-xs text-muted-foreground">
              <tr>
                <th className="px-4 py-2 text-start font-medium">{t('admin.audit_column_date')}</th>
                <th className="px-4 py-2 text-start font-medium">{t('admin.audit_column_actor')}</th>
                <th className="px-4 py-2 text-start font-medium">{t('admin.audit_column_action')}</th>
                <th className="px-4 py-2 text-start font-medium">{t('admin.audit_column_entity')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data.items.map((entry) => {
                const actor = entry.actor_id ? users.data?.get(entry.actor_id) : null
                return (
                  <tr key={entry.id}>
                    <td className="px-4 py-2.5 text-foreground">{formatDate(entry.created_at)}</td>
                    <td className="px-4 py-2.5 text-foreground">
                      {actor ? actor.full_name : entry.actor_id ? entry.actor_id : t('admin.audit_system_actor')}
                    </td>
                    <td className="px-4 py-2.5 text-foreground">{auditActionLabel(t, entry.action)}</td>
                    <td className="px-4 py-2.5 text-foreground">
                      {entry.entity_type}
                      {entry.entity_id ? ` · ${entry.entity_id.slice(0, 8)}` : ''}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {data && data.total > 0 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            {t('common.page_info', {
              page: data.page,
              totalPages: Math.max(1, Math.ceil(data.total / data.page_size)),
              total: data.total,
            })}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="h-9 cursor-pointer rounded-md border border-border px-3 font-medium text-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t('reports.previous_page')}
            </button>
            <button
              type="button"
              disabled={page * data.page_size >= data.total}
              onClick={() => setPage((p) => p + 1)}
              className="h-9 cursor-pointer rounded-md border border-border px-3 font-medium text-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t('reports.next_page')}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
