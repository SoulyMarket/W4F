import type { Icon } from '@phosphor-icons/react'
import { TrayIcon } from '@phosphor-icons/react'

interface EmptyStateProps {
  message: string
  icon?: Icon
  className?: string
}

// Every "no results" message across the app (reports/users/territories/
// audit/dashboard douar lists) was a single muted `<p>` — correct, but
// reads as bare/unfinished next to the rest of the premium pass. One
// shared icon-plus-message treatment instead, `TrayIcon` by default
// (a generic "nothing here yet" mark), overridable per call site.
export function EmptyState({ message, icon: IconComponent = TrayIcon, className = '' }: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center gap-2 py-8 text-center ${className}`}>
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
        <IconComponent size={22} aria-hidden="true" />
      </span>
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  )
}
