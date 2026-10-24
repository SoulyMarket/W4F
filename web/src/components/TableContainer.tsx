import type { ReactNode } from 'react'

interface TableContainerProps {
  children: ReactNode
  /** CSS opacity for the placeholder-data (page-changing) dim effect. */
  opacity?: number
}

// The framed/rounded wrapper around every data table in the app
// (reports, users, audit log) used a single `overflow-hidden` div —
// which keeps the rounded corners, but also means a table wider than its
// container gets its extra columns silently *clipped*, not scrolled:
// found live at 375px width, where the reports table's last column was
// cut off entirely with no way to reach it. `overflow-hidden` now lives
// only on the outer (corner-rounding) wrapper; a nested `overflow-x-auto`
// div handles actual horizontal scrolling, and the table gets a
// min-width so columns compress gracefully down to that point and then
// scroll instead of overlapping/illegible squishing.
export function TableContainer({ children, opacity = 1 }: TableContainerProps) {
  return (
    <div
      className="overflow-hidden rounded-xl border border-border bg-white/60 shadow-sm transition-opacity dark:bg-white/5"
      style={{ opacity }}
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-start text-sm">{children}</table>
      </div>
    </div>
  )
}
