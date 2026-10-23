import { useTranslation } from 'react-i18next'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../features/auth/AuthContext'

export function ProtectedRoute() {
  const { t } = useTranslation()
  const { status } = useAuth()

  if (status === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-foreground">
        {t('common.loading')}
      </div>
    )
  }

  if (status === 'unauthenticated') return <Navigate to="/login" replace />

  return <Outlet />
}
