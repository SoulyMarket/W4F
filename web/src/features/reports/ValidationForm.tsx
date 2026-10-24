import { AnimatePresence, motion } from 'framer-motion'
import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '../../components/Button'
import { labelClass, selectClass, textareaClass } from '../../components/formStyles'
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
      <AnimatePresence mode="wait">
        {mutation.isSuccess && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="text-sm text-green-700 dark:text-green-400"
          >
            {t('reports.validation_success')}
          </motion.p>
        )}
      </AnimatePresence>
      {mutation.isError && (
        <p className="text-sm text-destructive">
          {mutation.error instanceof ApiError ? mutation.error.message : t('reports.validation_error')}
        </p>
      )}

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('reports.validation_decision_label')}</span>
        <select required value={decision} onChange={(event) => setDecision(event.target.value)} className={selectClass}>
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
        <span className={labelClass}>{t('reports.validation_comment_label')}</span>
        <textarea value={comment} onChange={(event) => setComment(event.target.value)} rows={2} className={textareaClass} />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('reports.validation_proposed_solution_label')}</span>
        <textarea
          value={proposedSolution}
          onChange={(event) => setProposedSolution(event.target.value)}
          rows={2}
          className={textareaClass}
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('reports.validation_urgency_label')}</span>
        <select value={urgency} onChange={(event) => setUrgency(event.target.value)} className={selectClass}>
          <option value="">{t('reports.validation_urgency_placeholder')}</option>
          {SEVERITIES.map((value) => (
            <option key={value} value={value}>
              {severityLabel(t, value)}
            </option>
          ))}
        </select>
      </label>

      <Button type="submit" disabled={!decision} isLoading={mutation.isPending} className="self-start">
        {mutation.isPending ? t('reports.validation_submitting') : t('reports.validation_submit')}
      </Button>
    </form>
  )
}
