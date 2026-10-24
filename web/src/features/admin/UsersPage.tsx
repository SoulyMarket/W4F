import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '../../components/Button'
import { Card } from '../../components/Card'
import { TableContainer } from '../../components/TableContainer'
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
        <h1 className="text-2xl font-bold tracking-tight text-foreground">{t('admin.users_title')}</h1>
        {!showCreateForm && (
          <Button size="sm" onClick={() => setShowCreateForm(true)}>
            {t('admin.new_user_button')}
          </Button>
        )}
      </div>

      <AnimatePresence>
        {temporaryPassword && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-primary/40 bg-primary/10 p-3 text-sm"
          >
            <span className="min-w-0 break-all text-foreground">
              {t('admin.temporary_password_label')}: <strong className="font-mono">{temporaryPassword}</strong> —{' '}
              {t('admin.temporary_password_notice')}
            </span>
            <button
              type="button"
              onClick={() => setTemporaryPassword(null)}
              className="shrink-0 cursor-pointer text-primary hover:underline"
            >
              {t('admin.close')}
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>{showCreateForm && <CreateUserForm onDone={() => setShowCreateForm(false)} />}</AnimatePresence>

      {isPending ? (
        <p className="text-foreground">{t('common.loading')}</p>
      ) : isError ? (
        <div className="flex flex-col items-start gap-2">
          <p className="text-destructive">
            {error instanceof ApiError ? error.message : t('admin.users_loading_error')}
          </p>
          <Button variant="secondary" onClick={() => void refetch()}>
            {t('common.retry')}
          </Button>
        </div>
      ) : (
        <>
          {/* Below `sm`, 6 columns (name/email/role/status/last-login/
              actions) can't fit a 375px frame without either clipping or
              scrolling past content with no visible affordance — same
              reasoning as the reports list. */}
          <div className="flex flex-col gap-2 sm:hidden">
            {data.items.map((user, index) => (
              <Card key={user.id} index={Math.min(index, 8)}>
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="truncate font-medium text-foreground">{user.full_name}</p>
                    <p className="truncate text-sm text-muted-foreground">{user.email}</p>
                  </div>
                  <span
                    className={`shrink-0 text-xs font-medium ${user.is_active ? 'text-green-700 dark:text-green-400' : 'text-muted-foreground'}`}
                  >
                    {user.is_active ? t('admin.status_active') : t('admin.status_inactive')}
                  </span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {t(`role.${user.role}`)} ·{' '}
                  {user.last_login_at ? formatDate(user.last_login_at) : t('admin.never_logged_in')}
                </p>
                <div className="mt-2">
                  <UserRowActions
                    user={user}
                    confirming={confirming}
                    onReset={() => setConfirming({ userId: user.id, kind: 'reset' })}
                    onDeactivate={() => setConfirming({ userId: user.id, kind: 'deactivate' })}
                    onConfirm={handleConfirm}
                    onCancel={() => setConfirming(null)}
                  />
                </div>
              </Card>
            ))}
          </div>

          <div className="hidden sm:block">
            <TableContainer>
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
                {data.items.map((user, index) => (
                  <motion.tr
                    key={user.id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2, delay: Math.min(index, 10) * 0.03 }}
                  >
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
                      <UserRowActions
                        user={user}
                        confirming={confirming}
                        onReset={() => setConfirming({ userId: user.id, kind: 'reset' })}
                        onDeactivate={() => setConfirming({ userId: user.id, kind: 'deactivate' })}
                        onConfirm={handleConfirm}
                        onCancel={() => setConfirming(null)}
                      />
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </TableContainer>
          </div>
        </>
      )}
    </div>
  )
}

function UserRowActions({
  user,
  confirming,
  onReset,
  onDeactivate,
  onConfirm,
  onCancel,
}: {
  user: UserDto
  confirming: ConfirmingAction
  onReset: () => void
  onDeactivate: () => void
  onConfirm: (user: UserDto, kind: 'deactivate' | 'reset') => void
  onCancel: () => void
}) {
  const { t } = useTranslation()

  if (confirming?.userId === user.id) {
    return (
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-muted-foreground">
          {confirming.kind === 'deactivate' ? t('admin.deactivate_confirm') : t('admin.reset_password_confirm')}
        </span>
        <button
          type="button"
          onClick={() => onConfirm(user, confirming.kind)}
          className="cursor-pointer text-xs font-semibold text-destructive hover:underline"
        >
          {t('common.confirm')}
        </button>
        <button type="button" onClick={onCancel} className="cursor-pointer text-xs font-medium text-foreground hover:underline">
          {t('common.cancel')}
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-wrap gap-3">
      <button type="button" onClick={onReset} className="cursor-pointer text-xs font-medium text-primary hover:underline">
        {t('admin.reset_password_button')}
      </button>
      {user.is_active && (
        <button
          type="button"
          onClick={onDeactivate}
          className="cursor-pointer text-xs font-medium text-destructive hover:underline"
        >
          {t('admin.deactivate_button')}
        </button>
      )}
    </div>
  )
}
