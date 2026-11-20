import { motion } from 'framer-motion'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '../../components/Button'
import { ApiError } from '../../lib/api'
import { useSetUserTerritories, useTerritoriesList } from './territoriesApi'
import type { UserDto } from './usersApi'

export function UserTerritoriesEditor({ user, onDone }: { user: UserDto; onDone: () => void }) {
  const { t } = useTranslation()
  const { data: territories, isPending } = useTerritoriesList()
  const mutation = useSetUserTerritories()
  const [selected, setSelected] = useState<Set<string>>(new Set(user.territory_ids))

  function toggle(territoryId: string) {
    setSelected((current) => {
      const next = new Set(current)
      if (next.has(territoryId)) next.delete(territoryId)
      else next.add(territoryId)
      return next
    })
  }

  function handleSave() {
    mutation.mutate({ userId: user.id, territoryIds: [...selected] }, { onSuccess: () => onDone() })
  }

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      className="flex flex-col gap-3 rounded-xl border border-border bg-white/60 p-4 shadow-sm dark:bg-white/5"
    >
      <h2 className="text-sm font-semibold text-foreground">
        {t('user_territories.title')} — {user.full_name}
      </h2>

      {mutation.isError && (
        <p className="text-sm text-destructive">
          {mutation.error instanceof ApiError ? mutation.error.message : t('user_territories.save_error')}
        </p>
      )}

      {isPending ? (
        <p className="text-sm text-muted-foreground">{t('common.loading')}</p>
      ) : (territories ?? []).length === 0 ? (
        <p className="text-sm text-muted-foreground">{t('user_territories.none_assigned')}</p>
      ) : (
        <div className="flex max-h-64 flex-col gap-1 overflow-y-auto">
          {(territories ?? []).map((territory) => (
            <label key={territory.id} className="flex cursor-pointer items-center gap-2 rounded px-1 py-1 text-sm hover:bg-muted">
              <input
                type="checkbox"
                checked={selected.has(territory.id)}
                onChange={() => toggle(territory.id)}
                className="cursor-pointer accent-primary"
              />
              <span className="text-foreground">
                {territory.name_fr} ({t(`territories.level_${territory.level}`)})
              </span>
            </label>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <Button onClick={handleSave} isLoading={mutation.isPending}>
          {mutation.isPending ? t('user_territories.saving') : t('user_territories.save_button')}
        </Button>
        <Button type="button" variant="secondary" onClick={onDone}>
          {t('user_territories.close')}
        </Button>
      </div>
    </motion.div>
  )
}
