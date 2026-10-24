import { motion } from 'framer-motion'
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

  return (
    <nav className="flex items-center gap-1 border-b border-border bg-white/40 px-4 py-2 dark:bg-white/5">
      {user.role === 'manager' && (
        <NavItem to="/" end label={t('dashboard.title')} />
      )}
      <NavItem to="/reports" label={t('reports.title')} />
      {(user.role === 'manager' || user.role === 'admin') && (
        <NavItem to="/projects" label={t('projects.title')} />
      )}
      {user.role === 'admin' && (
        <>
          <NavItem to="/admin/users" label={t('admin.users_title')} />
          <NavItem to="/admin/audit" label={t('admin.audit_title')} />
        </>
      )}
    </nav>
  )
}

function NavItem({ to, label, end }: { to: string; label: string; end?: boolean }) {
  return (
    <NavLink
      to={to}
      end={end}
      className="relative rounded-md px-3 py-1.5 text-sm font-medium transition-colors hover:bg-muted"
    >
      {({ isActive }) => (
        <>
          {/* A single shared layoutId across every NavItem instance: when
              the active one changes, framer-motion animates this pill
              sliding from its old position to its new one instead of
              popping, the same "sliding tab indicator" pattern as most
              native tab bars. */}
          {isActive && (
            <motion.span
              layoutId="nav-active-pill"
              className="absolute inset-0 rounded-md bg-primary"
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            />
          )}
          <span
            className={`relative z-10 transition-colors ${
              isActive ? 'text-on-primary' : 'text-foreground hover:text-primary'
            }`}
          >
            {label}
          </span>
        </>
      )}
    </NavLink>
  )
}
