import { DropIcon } from '@phosphor-icons/react'
import { useTranslation } from 'react-i18next'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../features/auth/AuthContext'

export function ProtectedRoute() {
  const { t } = useTranslation()
  const { status } = useAuth()

  if (status === 'loading') {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-background text-foreground">
        <DropIcon size={32} weight="fill" className="animate-pulse text-primary" aria-hidden="true" />
        <span className="text-sm text-muted-foreground">{t('common.loading')}</span>
      </div>
    )
  }

  if (status === 'unauthenticated') return <Navigate to="/login" replace />

  return <Outlet />
}
