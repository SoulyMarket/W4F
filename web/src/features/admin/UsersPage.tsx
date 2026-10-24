import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ApiError } from '../../lib/api'
import { formatDate } from '../../lib/formatDate'
import { CreateUserForm } from './CreateUserForm'
import { useDeactivateUser, useResetPassword, useUsersList, type UserDto } from './usersApi'

type ConfirmingAction = { userId: string; kind: 'deactivate' | 'reset' } | null

export function UsersPage() {
  const { t } = useTranslation()
  const { data, isPending, isError, error, refetch } = useUsersList()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [temporaryPassword, setTemporaryPassword] = useState<string | null>(null)
  // An in-app two-step confirm instead of window.confirm(): a native
  // dialog isn't part of the DOM (untestable, unstyleable, and in one
  // live check here it simply auto-dismissed instead of prompting,
  // silently no-opping the action) — this stays in the page itself.
  const [confirming, setConfirming] = useState<ConfirmingAction>(null)
  const deactivateMutation = useDeactivateUser()
  const resetPasswordMutation = useResetPassword()

  function handleConfirm(user: UserDto, kind: 'deactivate' | 'reset') {
    setConfirming(null)
    if (kind === 'deactivate') {
      deactivateMutation.mutate(user.id)
    } else {
      resetPasswordMutation.mutate(user.id, {
        onSuccess: (result) => setTemporaryPassword(result.temporary_password),
      })
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-foreground">{t('admin.users_title')}</h1>
        {!showCreateForm && (
          <button
            type="button"
            onClick={() => setShowCreateForm(true)}
            className="h-9 cursor-pointer rounded-md bg-primary px-3 text-sm font-semibold text-on-primary transition-opacity hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            {t('admin.new_user_button')}
          </button>
        )}
      </div>

      {temporaryPassword && (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-primary/40 bg-primary/10 p-3 text-sm">
          <span className="text-foreground">
            {t('admin.temporary_password_label')}: <strong className="font-mono">{temporaryPassword}</strong> —{' '}
            {t('admin.temporary_password_notice')}
          </span>
          <button
            type="button"
            onClick={() => setTemporaryPassword(null)}
            className="cursor-pointer text-primary hover:underline"
          >
            {t('admin.close')}
          </button>
        </div>
      )}

      {showCreateForm && <CreateUserForm onDone={() => setShowCreateForm(false)} />}

      {isPending ? (
        <p className="text-foreground">{t('common.loading')}</p>
      ) : isError ? (
        <div className="flex flex-col items-start gap-2">
          <p className="text-destructive">
            {error instanceof ApiError ? error.message : t('admin.users_loading_error')}
          </p>
          <button
            type="button"
            onClick={() => void refetch()}
            className="h-9 cursor-pointer rounded-md border border-border px-3 text-sm font-medium text-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {t('common.retry')}
          </button>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-border bg-white/60 shadow-sm dark:bg-white/5">
          <table className="w-full text-start text-sm">
            <thead className="border-b border-border text-xs text-muted-foreground">
              <tr>
                <th className="px-4 py-2 text-start font-medium">{t('admin.column_name')}</th>
                <th className="px-4 py-2 text-start font-medium">{t('admin.column_email')}</th>
                <th className="px-4 py-2 text-start font-medium">{t('admin.column_role')}</th>
                <th className="px-4 py-2 text-start font-medium">{t('admin.column_status')}</th>
                <th className="px-4 py-2 text-start font-medium">{t('admin.column_last_login')}</th>
                <th className="px-4 py-2 text-start font-medium" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data.items.map((user) => (
                <tr key={user.id}>
                  <td className="px-4 py-2.5 text-foreground">{user.full_name}</td>
                  <td className="px-4 py-2.5 text-foreground">{user.email}</td>
                  <td className="px-4 py-2.5 text-foreground">{t(`role.${user.role}`)}</td>
                  <td className="px-4 py-2.5">
                    <span className={user.is_active ? 'text-green-700 dark:text-green-400' : 'text-muted-foreground'}>
                      {user.is_active ? t('admin.status_active') : t('admin.status_inactive')}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-foreground">
                    {user.last_login_at ? formatDate(user.last_login_at) : t('admin.never_logged_in')}
                  </td>
                  <td className="px-4 py-2.5">
                    {confirming?.userId === user.id ? (
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          {confirming.kind === 'deactivate'
                            ? t('admin.deactivate_confirm')
                            : t('admin.reset_password_confirm')}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleConfirm(user, confirming.kind)}
                          className="cursor-pointer text-xs font-semibold text-destructive hover:underline"
                        >
                          {t('common.confirm')}
                        </button>
                        <button
                          type="button"
                          onClick={() => setConfirming(null)}
                          className="cursor-pointer text-xs font-medium text-foreground hover:underline"
                        >
                          {t('common.cancel')}
                        </button>
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => setConfirming({ userId: user.id, kind: 'reset' })}
                          className="cursor-pointer text-xs font-medium text-primary hover:underline"
                        >
                          {t('admin.reset_password_button')}
                        </button>
                        {user.is_active && (
                          <button
                            type="button"
                            onClick={() => setConfirming({ userId: user.id, kind: 'deactivate' })}
                            className="cursor-pointer text-xs font-medium text-destructive hover:underline"
                          >
                            {t('admin.deactivate_button')}
                          </button>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
