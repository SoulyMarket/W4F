import { useTranslation } from 'react-i18next'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../features/auth/AuthContext'

// Section: "every role sees only their allowed menus and data" — built up
// screen-by-screen as Phase 3 proceeds; a role only gets a link once the
// screen it points to actually exists for that role.
export function NavBar() {
  const { t } = useTranslation()
  const { user } = useAuth()
  if (!user || user.role === 'moqaddem') return null

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
      isActive ? 'bg-primary text-on-primary' : 'text-foreground hover:bg-muted'
    }`

  return (
    <nav className="flex items-center gap-2 border-b border-border bg-white/40 px-4 py-2 dark:bg-white/5">
      {user.role === 'manager' && (
        <NavLink to="/" end className={linkClass}>
          {t('dashboard.title')}
        </NavLink>
      )}
      <NavLink to="/reports" className={linkClass}>
        {t('reports.title')}
      </NavLink>
      {(user.role === 'manager' || user.role === 'admin') && (
        <NavLink to="/projects" className={linkClass}>
          {t('projects.title')}
        </NavLink>
      )}
    </nav>
  )
}
