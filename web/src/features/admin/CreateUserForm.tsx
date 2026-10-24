import { motion } from 'framer-motion'
import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '../../components/Button'
import { inputClass, labelClass, selectClass } from '../../components/formStyles'
import { ApiError } from '../../lib/api'
import { useCreateUser } from './usersApi'

const ROLES = ['admin', 'manager', 'expert', 'moqaddem']

export function CreateUserForm({ onDone }: { onDone: () => void }) {
  const { t } = useTranslation()
  const mutation = useCreateUser()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!fullName || !email || !password || !role) return
    mutation.mutate(
      { full_name: fullName, email, password, role },
      { onSuccess: () => onDone() },
    )
  }

  return (
    <motion.form
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      onSubmit={handleSubmit}
      className="flex flex-col gap-3 rounded-xl border border-border bg-white/60 p-4 shadow-sm dark:bg-white/5"
    >
      <h2 className="text-sm font-semibold text-foreground">{t('admin.create_form_title')}</h2>

      {mutation.isError && (
        <p className="text-sm text-destructive">
          {mutation.error instanceof ApiError ? mutation.error.message : t('admin.create_error')}
        </p>
      )}

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('admin.full_name_label')}</span>
        <input required value={fullName} onChange={(event) => setFullName(event.target.value)} className={inputClass} />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('admin.email_label')}</span>
        <input
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className={inputClass}
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('admin.password_label')}</span>
        <input
          type="password"
          required
          minLength={10}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className={inputClass}
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className={labelClass}>{t('admin.role_label')}</span>
        <select required value={role} onChange={(event) => setRole(event.target.value)} className={selectClass}>
          <option value="" disabled>
            {t('admin.role_placeholder')}
          </option>
          {ROLES.map((value) => (
            <option key={value} value={value}>
              {t(`role.${value}`)}
            </option>
          ))}
        </select>
      </label>

      <div className="flex gap-2">
        <Button type="submit" disabled={!fullName || !email || !password || !role} isLoading={mutation.isPending}>
          {mutation.isPending ? t('admin.create_submitting') : t('admin.create_submit')}
        </Button>
        <Button type="button" variant="secondary" onClick={onDone}>
          {t('admin.close')}
        </Button>
      </div>
    </motion.form>
  )
}
