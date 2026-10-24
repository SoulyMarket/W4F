import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { ApiError } from '../../lib/api'
import { severityLabel } from '../../lib/reportFieldLabels'
import { VALIDATION_DECISIONS, validationDecisionLabel } from '../../lib/statusLabels'
import { useCreateValidation } from './reportsApi'

const SEVERITIES = ['low', 'medium', 'high', 'critical']

// Section 5: only an expert may validate (backend: `require_roles(EXPERT)`)
// — the caller only renders this once that's already confirmed, and only
// while the report isn't in a terminal status (rejected/converted — the
// backend 409s on either).
export function ValidationForm({ reportId }: { reportId: string }) {
  const { t } = useTranslation()
  const mutation = useCreateValidation(reportId)
  const [decision, setDecision] = useState('')
  const [comment, setComment] = useState('')
  const [proposedSolution, setProposedSolution] = useState('')
  const [urgency, setUrgency] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!decision) return
    mutation.mutate(
      {
        decision,
        comment: comment || undefined,
        proposed_solution: proposedSolution || undefined,
        urgency_opinion: urgency || undefined,
      },
      {
        onSuccess: () => {
          setDecision('')
          setComment('')
          setProposedSolution('')
          setUrgency('')
        },
      },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      {mutation.isSuccess && <p className="text-sm text-green-700 dark:text-green-400">{t('reports.validation_success')}</p>}
      {mutation.isError && (
        <p className="text-sm text-destructive">
          {mutation.error instanceof ApiError ? mutation.error.message : t('reports.validation_error')}
        </p>
      )}

      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-foreground">{t('reports.validation_decision_label')}</span>
        <select
          required
          value={decision}
          onChange={(event) => setDecision(event.target.value)}
          className="h-10 cursor-pointer rounded-md border border-border bg-background px-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="" disabled>
            {t('reports.validation_decision_placeholder')}
          </option>
          {VALIDATION_DECISIONS.map((value) => (
            <option key={value} value={value}>
              {validationDecisionLabel(t, value)}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-foreground">{t('reports.validation_comment_label')}</span>
        <textarea
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          rows={2}
          className="rounded-md border border-border bg-background px-2 py-1.5 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-foreground">{t('reports.validation_proposed_solution_label')}</span>
        <textarea
          value={proposedSolution}
          onChange={(event) => setProposedSolution(event.target.value)}
          rows={2}
          className="rounded-md border border-border bg-background px-2 py-1.5 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-foreground">{t('reports.validation_urgency_label')}</span>
        <select
          value={urgency}
          onChange={(event) => setUrgency(event.target.value)}
          className="h-10 cursor-pointer rounded-md border border-border bg-background px-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">{t('reports.validation_urgency_placeholder')}</option>
          {SEVERITIES.map((value) => (
            <option key={value} value={value}>
              {severityLabel(t, value)}
            </option>
          ))}
        </select>
      </label>

      <button
        type="submit"
        disabled={!decision || mutation.isPending}
        className="h-10 cursor-pointer self-start rounded-md bg-primary px-4 text-sm font-semibold text-on-primary transition-opacity hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {mutation.isPending ? t('reports.validation_submitting') : t('reports.validation_submit')}
      </button>
    </form>
  )
}
