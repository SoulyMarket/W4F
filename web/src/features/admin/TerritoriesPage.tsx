import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '../../components/Button'
import { Card } from '../../components/Card'
import { inputClass } from '../../components/formStyles'
import { TableContainer } from '../../components/TableContainer'
import { ApiError } from '../../lib/api'
import { CreateTerritoryForm } from './CreateTerritoryForm'
import { useTerritoriesList, useUpdateTerritory, type TerritoryDto } from './territoriesApi'

export function TerritoriesPage() {
  const { t } = useTranslation()
  const { data, isPending, isError, error, refetch } = useTerritoriesList()
  const [showCreateForm, setShowCreateForm] = useState(false)

  if (isPending) return <p className="text-foreground">{t('common.loading')}</p>

  if (isError) {
    return (
      <div className="flex flex-col items-start gap-2">
        <p className="text-destructive">{error instanceof ApiError ? error.message : t('territories.loading_error')}</p>
        <Button variant="secondary" onClick={() => void refetch()}>
          {t('common.retry')}
        </Button>
      </div>
    )
  }

  const byId = new Map(data.map((territory) => [territory.id, territory]))
  // Provinces first, each immediately followed by its own communes —
  // reads as a two-level tree without needing an actual tree widget for
  // a hierarchy that's never more than two levels deep (section 4's
  // Territory model: province → commune, nothing nested further).
  const provinces = data.filter((territory) => territory.level === 'province')
  const communesByParent = new Map<string, TerritoryDto[]>()
  for (const territory of data) {
    if (territory.level !== 'commune' || !territory.parent_id) continue
    const siblings = communesByParent.get(territory.parent_id) ?? []
    siblings.push(territory)
    communesByParent.set(territory.parent_id, siblings)
  }
  const orphanCommunes = data.filter(
    (territory) => territory.level === 'commune' && (!territory.parent_id || !byId.has(territory.parent_id)),
  )
  const orderedRows: TerritoryDto[] = []
  for (const province of provinces) {
    orderedRows.push(province)
    orderedRows.push(...(communesByParent.get(province.id) ?? []))
  }
  orderedRows.push(...orphanCommunes)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">{t('territories.title')}</h1>
        {!showCreateForm && (
          <Button size="sm" onClick={() => setShowCreateForm(true)}>
            {t('territories.new_button')}
          </Button>
        )}
      </div>

      <AnimatePresence>{showCreateForm && <CreateTerritoryForm onDone={() => setShowCreateForm(false)} />}</AnimatePresence>

      {orderedRows.length === 0 ? (
        <Card className="max-w-md">
          <p className="text-sm text-muted-foreground">{t('territories.empty')}</p>
        </Card>
      ) : (
        <TableContainer>
          <thead className="border-b border-border text-xs text-muted-foreground">
            <tr>
              <th className="px-4 py-2 text-start font-medium">{t('territories.column_name_ar')}</th>
              <th className="px-4 py-2 text-start font-medium">{t('territories.column_name_fr')}</th>
              <th className="px-4 py-2 text-start font-medium">{t('territories.column_level')}</th>
              <th className="px-4 py-2 text-start font-medium">{t('territories.column_parent')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {orderedRows.map((territory, index) => (
              <motion.tr
                key={territory.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: Math.min(index, 10) * 0.03 }}
              >
                <td className="px-4 py-2.5">
                  <EditableName territory={territory} field="name_ar" dir="rtl" />
                </td>
                <td className="px-4 py-2.5">
                  <EditableName territory={territory} field="name_fr" dir="ltr" />
                </td>
                <td className="px-4 py-2.5 text-foreground">{t(`territories.level_${territory.level}`)}</td>
                <td className="px-4 py-2.5 text-muted-foreground">
                  {territory.parent_id
                    ? (byId.get(territory.parent_id)?.name_fr ?? territory.parent_id)
                    : t('territories.no_parent')}
                </td>
              </motion.tr>
            ))}
          </tbody>
        </TableContainer>
      )}
    </div>
  )
}

// Click-to-edit instead of a separate "edit" form: there are only two
// renameable fields per row, so a dedicated modal/form would be more
// ceremony than the task warrants — same reasoning as the admin users
// page's inline two-step confirm for a small, contained interaction.
function EditableName({
  territory,
  field,
  dir,
}: {
  territory: TerritoryDto
  field: 'name_ar' | 'name_fr'
  dir: 'rtl' | 'ltr'
}) {
  const { t } = useTranslation()
  const mutation = useUpdateTerritory()
  const [isEditing, setIsEditing] = useState(false)
  const [value, setValue] = useState(territory[field])

  if (!isEditing) {
    return (
      <button
        type="button"
        onClick={() => {
          setValue(territory[field])
          setIsEditing(true)
        }}
        className="cursor-pointer rounded px-1 text-start text-foreground hover:bg-muted"
      >
        {territory[field]}
      </button>
    )
  }

  function commit() {
    const trimmed = value.trim()
    if (!trimmed || trimmed === territory[field]) {
      setIsEditing(false)
      return
    }
    mutation.mutate({ id: territory.id, [field]: trimmed }, { onSuccess: () => setIsEditing(false) })
  }

  return (
    <div className="flex flex-col gap-1">
      <input
        autoFocus
        dir={dir}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onBlur={commit}
        onKeyDown={(event) => {
          if (event.key === 'Enter') commit()
          if (event.key === 'Escape') setIsEditing(false)
        }}
        className={`${inputClass} h-8`}
      />
      {mutation.isError && (
        <span className="text-xs text-destructive">
          {mutation.error instanceof ApiError ? mutation.error.message : t('territories.rename_error')}
        </span>
      )}
    </div>
  )
}
