import { useTranslation } from 'react-i18next'
import { Button } from '../components/Button'
import { LanguageSwitcher } from '../components/LanguageSwitcher'
import { PageTransition } from '../components/PageTransition'
import { useAuth } from '../features/auth/AuthContext'
import { NavBar } from './NavBar'

export function AppLayout() {
  const { t } = useTranslation()
  const { user, logout } = useAuth()

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* flex-wrap, not a fixed single row: at narrow widths the title and
          the controls group fighting for the same row either overlapped
          or forced the title to break across two lines mid-word (found
          live at 375px). Wrapping lets the controls drop to their own
          row below instead, and `min-w-0 truncate` keeps the title from
          ever doing that two-line wrap itself. */}
      <header className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-b border-border bg-white/60 px-4 py-3 backdrop-blur-sm dark:bg-white/5">
        <span className="min-w-0 truncate text-base font-semibold text-foreground">{t('app.name')}</span>
        <div className="flex shrink-0 items-center gap-4">
          <LanguageSwitcher />
          {user && (
            <span className="hidden text-sm text-muted-foreground sm:inline">
              {user.fullName} — {t(`role.${user.role}`)}
            </span>
          )}
          <Button variant="secondary" size="sm" onClick={() => void logout()}>
            {t('common.logout')}
          </Button>
        </div>
      </header>
      <NavBar />
      <main className="flex-1 overflow-hidden p-4 sm:p-6">
        <PageTransition />
      </main>
    </div>
  )
}
