import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '../../components/Button'
import { Card } from '../../components/Card'
import { Skeleton } from '../../components/Skeleton'
import { ApiError } from '../../lib/api'
import { scoringCriterionLabel } from '../../lib/statusLabels'
import { SCORING_CRITERIA, useScoringConfig, useUpdateScoringConfig, type ScoringConfigDto } from './scoringApi'

// Section 1: "edit scoring weights" is listed only under manager — this
// page is reached through a manager-only nav link and `RequireManager`
// route guard, matching the backend's own `require_roles(MANAGER)` on
// the write side (the read side allows every role, but no other role has
// a reason to land on this specific page).
export function ScoringWeightsPage() {
  const { t } = useTranslation()
  const { data, isPending, isError, error, refetch } = useScoringConfig()
  const mutation = useUpdateScoringConfig()
  const [weights, setWeights] = useState<Record<string, number> | null>(null)
  const [savedMessage, setSavedMessage] = useState<string | null>(null)
  // Tracks which server payload `weights` was last seeded from — adjusting
  // state during render (React's own recommended alternative to a
  // useEffect here) instead of re-syncing on every background refetch,
  // which would otherwise wipe in-progress edits.
  const [seededFrom, setSeededFrom] = useState<ScoringConfigDto | null>(null)

  if (data && data !== seededFrom && weights === null) {
    setSeededFrom(data)
    setWeights(data.weights)
  }

  if (isPending || weights === null) {
    return <ScoringWeightsSkeleton />
  }

  if (isError) {
    return (
      <div className="flex flex-col items-start gap-2">
        <p className="text-destructive">{error instanceof ApiError ? error.message : t('scoring.loading_error')}</p>
        <Button variant="secondary" onClick={() => void refetch()}>
          {t('common.retry')}
        </Button>
      </div>
    )
  }

  const isDirty = JSON.stringify(weights) !== JSON.stringify(data.weights)

  function handleSave() {
    if (weights === null) return
    setSavedMessage(null)
    mutation.mutate(weights, {
      onSuccess: (result) => {
        setSavedMessage(t('scoring.save_success', { count: result.reports_recomputed }))
      },
    })
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold tracking-tight text-foreground font-heading">{t('scoring.title')}</h1>
      <p className="text-sm text-muted-foreground">{t('scoring.hint')}</p>

      {mutation.isError && (
        <p className="text-sm text-destructive">
          {mutation.error instanceof ApiError ? mutation.error.message : t('scoring.save_error')}
        </p>
      )}

      <AnimatePresence>
        {savedMessage && (
          <motion.p
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="rounded-lg border border-primary/40 bg-primary/10 p-3 text-sm text-foreground"
          >
            {savedMessage}
          </motion.p>
        )}
      </AnimatePresence>

      <Card className="max-w-xl">
        <div className="flex flex-col gap-4">
          {SCORING_CRITERIA.map((criterion) => (
            <div key={criterion} className="flex flex-col gap-1">
              <div className="flex items-center justify-between gap-3">
                <label htmlFor={`weight-${criterion}`} className="text-sm font-medium text-foreground">
                  {scoringCriterionLabel(t, criterion)}
                </label>
                <span className="w-10 shrink-0 text-end text-sm font-semibold text-foreground">
                  {weights[criterion]}
                </span>
              </div>
              <input
                id={`weight-${criterion}`}
                type="range"
                min={0}
                max={100}
                step={1}
                value={weights[criterion]}
                onChange={(event) => {
                  setSavedMessage(null)
                  setWeights((current) => ({ ...(current ?? {}), [criterion]: Number(event.target.value) }))
                }}
                className="w-full cursor-pointer accent-primary"
              />
            </div>
          ))}
        </div>
      </Card>

      <div className="flex gap-2">
        <Button onClick={handleSave} disabled={!isDirty} isLoading={mutation.isPending}>
          {mutation.isPending ? t('scoring.saving') : t('scoring.save_button')}
        </Button>
        {isDirty && (
          <Button variant="secondary" onClick={() => setWeights(data.weights)}>
            {t('scoring.reset_button')}
          </Button>
        )}
      </div>
    </div>
  )
}

function ScoringWeightsSkeleton() {
  return (
    <div className="flex flex-col gap-4" aria-hidden="true">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-4 w-80" />
      <Card className="max-w-xl">
        <div className="flex flex-col gap-4">
          {Array.from({ length: SCORING_CRITERIA.length }, (_, i) => (
            <div key={i} className="flex flex-col gap-1">
              <div className="flex items-center justify-between gap-3">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-4 w-8" />
              </div>
              <Skeleton className="h-2 w-full rounded-full" />
            </div>
          ))}
        </div>
      </Card>
      <Skeleton className="h-10 w-40" />
    </div>
  )
}
