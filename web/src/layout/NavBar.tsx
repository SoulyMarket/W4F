import {
  ClipboardTextIcon,
  ClockCounterClockwiseIcon,
  GaugeIcon,
  KanbanIcon,
  MapPinIcon,
  MapTrifoldIcon,
  SlidersHorizontalIcon,
  UsersIcon,
  type Icon,
} from '@phosphor-icons/react'
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
    // flex-wrap so tabs wrap as whole units onto a new line at narrow
    // widths, instead of each tab's own text breaking mid-word (found
    // live: "Journal d'audit" split as "Journal d" / "audit") — each
    // NavItem is `whitespace-nowrap` so a tab's label is always one of
    // the two outcomes: full width on its line, or wrapped as a whole to
    // the next line, never broken partway through.
    <nav className="flex flex-wrap items-center gap-1 border-b border-border bg-white/40 px-4 py-2 dark:bg-white/5">
      {user.role === 'manager' && (
        <NavItem to="/" end icon={GaugeIcon} label={t('dashboard.title')} />
      )}
      <NavItem to="/reports" icon={ClipboardTextIcon} label={t('reports.title')} />
      {(user.role === 'manager' || user.role === 'admin') && (
        <NavItem to="/projects" icon={KanbanIcon} label={t('projects.title')} />
      )}
      {user.role === 'manager' && (
        <>
          <NavItem to="/map" icon={MapTrifoldIcon} label={t('map.title')} />
          <NavItem to="/scoring" icon={SlidersHorizontalIcon} label={t('scoring.title')} />
        </>
      )}
      {user.role === 'admin' && (
        <>
          <NavItem to="/admin/users" icon={UsersIcon} label={t('admin.users_title')} />
          <NavItem to="/admin/audit" icon={ClockCounterClockwiseIcon} label={t('admin.audit_title')} />
          <NavItem to="/admin/territories" icon={MapPinIcon} label={t('territories.title')} />
        </>
      )}
    </nav>
  )
}

function NavItem({ to, label, end, icon: IconComponent }: { to: string; label: string; end?: boolean; icon: Icon }) {
  return (
    <NavLink
      to={to}
      end={end}
      className="relative flex items-center gap-1.5 whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-colors hover:bg-muted"
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
              className="absolute inset-0 rounded-md bg-gradient-to-b from-primary to-primary/90 shadow-soft"
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            />
          )}
          <IconComponent
            size={16}
            weight={isActive ? 'fill' : 'regular'}
            className={`relative z-10 shrink-0 transition-colors ${isActive ? 'text-on-primary' : 'text-muted-foreground'}`}
          />
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
