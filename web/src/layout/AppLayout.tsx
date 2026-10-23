import { useTranslation } from 'react-i18next'
import { Outlet } from 'react-router-dom'
import { LanguageSwitcher } from '../components/LanguageSwitcher'
import { useAuth } from '../features/auth/AuthContext'

export function AppLayout() {
  const { t } = useTranslation()
  const { user, logout } = useAuth()

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="flex items-center justify-between border-b border-border bg-white/60 px-4 py-3 dark:bg-white/5">
        <span className="text-base font-semibold text-foreground">{t('app.name')}</span>
        <div className="flex items-center gap-4">
          <LanguageSwitcher />
          {user && (
            <span className="hidden text-sm text-muted-foreground sm:inline">
              {user.fullName} — {t(`role.${user.role}`)}
            </span>
          )}
          <button
            type="button"
            onClick={() => void logout()}
            className="h-9 cursor-pointer rounded-md border border-border px-3 text-sm font-medium text-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {t('common.logout')}
          </button>
        </div>
      </header>
      <main className="flex-1 p-4 sm:p-6">
        <Outlet />
      </main>
    </div>
  )
}
