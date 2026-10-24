import { AnimatePresence, motion } from 'framer-motion'
import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '../../components/Button'
import { inputClass, labelClass, selectClass, textareaClass } from '../../components/formStyles'
import { ApiError } from '../../lib/api'
import { PROJECT_STATUS_TRANSITIONS, projectStatusLabel, type ProjectStatus } from '../../lib/statusLabels'
import { useAddProjectUpdate } from './projectsApi'

function allowedTransitionsFor(status: string): readonly ProjectStatus[] {
  return (PROJECT_STATUS_TRANSITIONS as Record<string, readonly ProjectStatus[]>)[status] ?? []
}

// Only rendered for a manager (backend: `require_roles(MANAGER)` on
// POST /projects/{id}/updates) — the caller checks that before mounting
// this. The allowed-transitions list mirrors the backend's own state
// machine so the select never offers a move the server would 409 on.
export function ProjectStatusUpdateForm({
  projectId,
  currentStatus,
  currentProgress,
}: {
  projectId: string
  currentStatus: string
  currentProgress: number
}) {
  const { t } = useTranslation()
  const mutation = useAddProjectUpdate(projectId)
  const allowed = allowedTransitionsFor(currentStatus)
  const [newStatus, setNewStatus] = useState('')
  const [progress, setProgress] = useState(String(currentProgress))
  const [note, setNote] = useState('')

  if (allowed.length === 0) {
    return <p className="text-sm text-muted-foreground">{t('projects.no_transitions_available')}</p>
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!newStatus) return
    const progressValue = progress === '' ? undefined : Number(progress)
    mutation.mutate(
      { new_status: newStatus, progress_percent: progressValue, note: note || undefined },
      { onSuccess: () => setNote('') },
    )
    setNewStatus('')
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
            {t('projects.update_success')}
          </motion.p>
        )}
      </AnimatePresence>
      {mutation.isError && (
        <p className="text-sm text-destructive">
          {mutation.error instanceof ApiError ? mutation.error.message : t('projects.update_error')}
        </p>
      )}

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('projects.update_new_status_label')}</span>
        <select required value={newStatus} onChange={(event) => setNewStatus(event.target.value)} className={selectClass}>
          <option value="" disabled>
            {t('projects.update_new_status_placeholder')}
          </option>
          {allowed.map((status) => (
            <option key={status} value={status}>
              {projectStatusLabel(t, status)}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('projects.update_progress_label')}</span>
        <input
          type="number"
          min={0}
          max={100}
          value={progress}
          onChange={(event) => setProgress(event.target.value)}
          className={`${inputClass} w-24`}
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('projects.update_note_label')}</span>
        <textarea value={note} onChange={(event) => setNote(event.target.value)} rows={2} className={textareaClass} />
      </label>

      <Button type="submit" disabled={!newStatus} isLoading={mutation.isPending} className="self-start">
        {mutation.isPending ? t('projects.update_submitting') : t('projects.update_submit')}
      </Button>
    </form>
  )
}
