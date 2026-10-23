import { useTranslation } from 'react-i18next'
import { useAuth } from '../features/auth/AuthContext'

// Placeholder landing content, replaced screen-by-screen as Phase 3's
// real pages are built (dashboard summary for manager, reports list for
// expert, users/territories/audit for admin). Section 1: the moqaddem
// role has no web screens at all — "Uses the Android app only" — so it
// gets a permanent notice instead of a placeholder that will later
// become a real page.
export function RoleHome() {
  const { t } = useTranslation()
  const { user } = useAuth()
  if (!user) return null

  if (user.role === 'moqaddem') {
    return <p className="text-foreground">{t('home.moqaddem_notice')}</p>
  }

  return (
    <div className="text-foreground">
      <p className="text-lg font-medium">{t('home.welcome', { name: user.fullName })}</p>
      <p className="text-sm text-muted-foreground">{t('home.role_label', { role: t(`role.${user.role}`) })}</p>
    </div>
  )
}
