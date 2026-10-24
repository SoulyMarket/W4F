import { motion, useReducedMotion } from 'framer-motion'
import { useTranslation } from 'react-i18next'

export interface StatusBarChartEntry {
  status: string
  count: number
  label: string
  color: string
}

// Previously built on Recharts (BarChart/YAxis/LabelList with a fixed
// 140px axis width) — found live at narrow widths: the value label
// rendered directly on top of the category text, because Recharts
// positions both by raw pixel offset with no awareness of the other's
// actual rendered width, and a fixed-px axis column doesn't adapt to
// either a narrower container or a longer Arabic label. Rebuilt as plain
// flex rows instead: label / bar-track / value are three real flex
// children, so the browser's own box model keeps them apart — there is
// no coordinate math left that could place two of them on top of each
// other. It also means no manual RTL mirroring logic (reversed axis,
// orientation, label position) — a flex row already reads start-to-end
// in whichever direction `dir` is, the same as any other row in the app.
export function StatusBarChart({ data }: { data: StatusBarChartEntry[] }) {
  const { t } = useTranslation()
  const prefersReducedMotion = useReducedMotion()

  if (data.length === 0) {
    return <p className="text-sm text-muted-foreground">{t('dashboard.no_data')}</p>
  }

  const max = Math.max(...data.map((entry) => entry.count), 1)

  return (
    <div className="flex flex-col gap-3">
      {data.map((entry, index) => (
        <div key={entry.status} className="flex items-center gap-3">
          <span
            className="min-w-0 shrink basis-28 truncate text-xs text-foreground"
            title={entry.label}
          >
            {entry.label}
          </span>
          <div className="h-5 min-w-0 flex-1 overflow-hidden rounded-full bg-muted">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: entry.color }}
              initial={prefersReducedMotion ? { width: `${(entry.count / max) * 100}%` } : { width: 0 }}
              animate={{ width: `${(entry.count / max) * 100}%` }}
              transition={{ duration: 0.5, delay: prefersReducedMotion ? 0 : index * 0.06, ease: 'easeOut' }}
            />
          </div>
          <span className="w-6 shrink-0 text-end text-xs font-semibold text-foreground">{entry.count}</span>
        </div>
      ))}
    </div>
  )
}
