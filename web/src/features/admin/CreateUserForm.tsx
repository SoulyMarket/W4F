import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
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
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-xl border border-border bg-white/60 p-4 shadow-sm dark:bg-white/5">
      <h2 className="text-sm font-semibold text-foreground">{t('admin.create_form_title')}</h2>

      {mutation.isError && (
        <p className="text-sm text-destructive">
          {mutation.error instanceof ApiError ? mutation.error.message : t('admin.create_error')}
        </p>
      )}

      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-foreground">{t('admin.full_name_label')}</span>
        <input
          required
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
          className="h-10 rounded-md border border-border bg-background px-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-foreground">{t('admin.email_label')}</span>
        <input
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="h-10 rounded-md border border-border bg-background px-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-foreground">{t('admin.password_label')}</span>
        <input
          type="password"
          required
          minLength={10}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="h-10 rounded-md border border-border bg-background px-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-foreground">{t('admin.role_label')}</span>
        <select
          required
          value={role}
          onChange={(event) => setRole(event.target.value)}
          className="h-10 cursor-pointer rounded-md border border-border bg-background px-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        >
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
        <button
          type="submit"
          disabled={!fullName || !email || !password || !role || mutation.isPending}
          className="h-10 cursor-pointer rounded-md bg-primary px-4 text-sm font-semibold text-on-primary transition-opacity hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {mutation.isPending ? t('admin.create_submitting') : t('admin.create_submit')}
        </button>
        <button
          type="button"
          onClick={onDone}
          className="h-10 cursor-pointer rounded-md border border-border px-4 text-sm font-medium text-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {t('admin.close')}
        </button>
      </div>
    </form>
  )
}
