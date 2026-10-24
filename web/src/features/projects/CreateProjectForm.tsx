import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/Button'
import { inputClass, labelClass, selectClass, textareaClass } from '../../components/formStyles'
import { ApiError } from '../../lib/api'
import { solutionTypeLabel, SOLUTION_TYPES } from '../../lib/reportFieldLabels'
import { useCreateProjectFromReport } from './projectsApi'

// Only rendered for a manager on a `validated` report (backend: 409 on
// anything else — `report.status != ReportStatus.VALIDATED` in
// `routes/projects.py`), checked by the caller before mounting this.
export function CreateProjectForm({ reportId }: { reportId: string }) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const mutation = useCreateProjectFromReport(reportId)
  const [title, setTitle] = useState('')
  const [solutionType, setSolutionType] = useState('')
  const [description, setDescription] = useState('')
  const [plannedStart, setPlannedStart] = useState('')
  const [plannedEnd, setPlannedEnd] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!title || !solutionType) return
    mutation.mutate(
      {
        title,
        solution_type: solutionType,
        description: description || undefined,
        planned_start: plannedStart || undefined,
        planned_end: plannedEnd || undefined,
      },
      { onSuccess: (project) => navigate(`/projects/${project.id}`) },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      {mutation.isError && (
        <p className="text-sm text-destructive">
          {mutation.error instanceof ApiError ? mutation.error.message : t('projects.create_error')}
        </p>
      )}

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('projects.create_title_label')}</span>
        <input required value={title} onChange={(event) => setTitle(event.target.value)} className={inputClass} />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('projects.solution_type_label')}</span>
        <select
          required
          value={solutionType}
          onChange={(event) => setSolutionType(event.target.value)}
          className={selectClass}
        >
          <option value="" disabled>
            {t('projects.solution_type_label')}
          </option>
          {SOLUTION_TYPES.map((value) => (
            <option key={value} value={value}>
              {solutionTypeLabel(t, value)}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('projects.create_description_label')}</span>
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          rows={2}
          className={textareaClass}
        />
      </label>

      <div className="flex gap-3">
        <label className="flex flex-1 flex-col gap-1 text-sm">
          <span className={labelClass}>{t('projects.create_planned_start_label')}</span>
          <input
            type="date"
            value={plannedStart}
            onChange={(event) => setPlannedStart(event.target.value)}
            className={inputClass}
          />
        </label>
        <label className="flex flex-1 flex-col gap-1 text-sm">
          <span className={labelClass}>{t('projects.create_planned_end_label')}</span>
          <input
            type="date"
            value={plannedEnd}
            onChange={(event) => setPlannedEnd(event.target.value)}
            className={inputClass}
          />
        </label>
      </div>

      <Button type="submit" disabled={!title || !solutionType} isLoading={mutation.isPending} className="self-start">
        {mutation.isPending ? t('projects.create_submitting') : t('projects.create_submit')}
      </Button>
    </form>
  )
}
