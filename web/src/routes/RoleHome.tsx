import { useTranslation } from 'react-i18next'
import { Card } from '../components/Card'
import { useAuth } from '../features/auth/AuthContext'
import { DashboardPage } from '../features/dashboard/DashboardPage'

// Placeholder landing content, replaced screen-by-screen as Phase 3's
// real pages are built (reports list for expert, users/territories/audit
// for admin — manager's own landing is now the real dashboard, step
// 3.2). Section 1: the moqaddem role has no web screens at all — "Uses
// the Android app only" — so it gets a permanent notice instead of a
// placeholder that will later become a real page.
export function RoleHome() {
  const { t } = useTranslation()
  const { user } = useAuth()
  if (!user) return null

  if (user.role === 'manager') return <DashboardPage />

  if (user.role === 'moqaddem') {
    return (
      <Card className="max-w-md">
        <p className="text-foreground">{t('home.moqaddem_notice')}</p>
      </Card>
    )
  }

  return (
    <Card className="max-w-md">
      <p className="text-lg font-semibold text-foreground">{t('home.welcome', { name: user.fullName })}</p>
      <p className="text-sm text-muted-foreground">{t('home.role_label', { role: t(`role.${user.role}`) })}</p>
    </Card>
  )
}
