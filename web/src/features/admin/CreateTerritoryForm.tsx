import { motion } from 'framer-motion'
import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '../../components/Button'
import { inputClass, labelClass, selectClass } from '../../components/formStyles'
import { ApiError } from '../../lib/api'
import { useCreateTerritory, useTerritoriesList, type TerritoryDto } from './territoriesApi'

const LEVELS = ['province', 'commune'] as const

export function CreateTerritoryForm({ onDone }: { onDone: () => void }) {
  const { t } = useTranslation()
  const mutation = useCreateTerritory()
  const { data: territories } = useTerritoriesList()
  const [nameAr, setNameAr] = useState('')
  const [nameFr, setNameFr] = useState('')
  const [level, setLevel] = useState('')
  const [parentId, setParentId] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!nameAr || !nameFr || !level) return
    mutation.mutate(
      { name_ar: nameAr, name_fr: nameFr, level, parent_id: parentId || null },
      { onSuccess: () => onDone() },
    )
  }

  // A commune needs a parent province; a province is itself the root, so
  // offering a parent for it would let it become a child of another
  // province for no reason this prototype's data model has a use for —
  // only provinces are offered as parent options.
  const provinceOptions: TerritoryDto[] = (territories ?? []).filter((territory) => territory.level === 'province')

  return (
    <motion.form
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      onSubmit={handleSubmit}
      className="flex flex-col gap-3 rounded-xl border border-border bg-white/60 p-4 shadow-sm dark:bg-white/5"
    >
      <h2 className="text-sm font-semibold text-foreground">{t('territories.create_form_title')}</h2>

      {mutation.isError && (
        <p className="text-sm text-destructive">
          {mutation.error instanceof ApiError ? mutation.error.message : t('territories.create_error')}
        </p>
      )}

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('territories.name_ar_label')}</span>
        <input required value={nameAr} onChange={(event) => setNameAr(event.target.value)} className={inputClass} dir="rtl" />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('territories.name_fr_label')}</span>
        <input required value={nameFr} onChange={(event) => setNameFr(event.target.value)} className={inputClass} dir="ltr" />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('territories.level_label')}</span>
        <select required value={level} onChange={(event) => setLevel(event.target.value)} className={selectClass}>
          <option value="" disabled>
            {t('territories.level_placeholder')}
          </option>
          {LEVELS.map((value) => (
            <option key={value} value={value}>
              {t(`territories.level_${value}`)}
            </option>
          ))}
        </select>
      </label>

      {level === 'commune' && (
        <label className="flex flex-col gap-1 text-sm">
          <span className={labelClass}>{t('territories.parent_label')}</span>
          <select required value={parentId} onChange={(event) => setParentId(event.target.value)} className={selectClass}>
            <option value="" disabled>
              {t('territories.parent_placeholder')}
            </option>
            {provinceOptions.map((province) => (
              <option key={province.id} value={province.id}>
                {province.name_fr}
              </option>
            ))}
          </select>
        </label>
      )}

      <div className="flex gap-2">
        <Button
          type="submit"
          disabled={!nameAr || !nameFr || !level || (level === 'commune' && !parentId)}
          isLoading={mutation.isPending}
        >
          {mutation.isPending ? t('territories.create_submitting') : t('territories.create_submit')}
        </Button>
        <Button type="button" variant="secondary" onClick={onDone}>
          {t('territories.close')}
        </Button>
      </div>
    </motion.form>
  )
}
