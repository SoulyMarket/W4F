import { motion, useReducedMotion } from 'framer-motion'
import type { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  /** Staggers the fade-in-up entrance by index * 60ms — pass the row/card
   * position within its list (KPI cards, board columns, ...). */
  index?: number
  /** Lifts the card on hover — for a card that's also a click target. */
  interactive?: boolean
  onClick?: () => void
}

// Replaces the "rounded-xl border border-border bg-white/60 p-4 shadow-sm
// dark:bg-white/5" string that had been copy-pasted into six different
// files with small drifts between them (some had shadow-sm, some didn't;
// padding varied between p-3 and p-4).
export function Card({ children, className = '', index = 0, interactive = false, onClick }: CardProps) {
  const prefersReducedMotion = useReducedMotion()
  const Component = onClick ? motion.button : motion.div

  return (
    <Component
      type={onClick ? 'button' : undefined}
      onClick={onClick}
      initial={prefersReducedMotion ? undefined : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: prefersReducedMotion ? 0 : index * 0.06, ease: 'easeOut' }}
      whileHover={interactive && !prefersReducedMotion ? { y: -2 } : undefined}
      className={`rounded-xl border border-border bg-white/60 p-4 shadow-sm transition-shadow dark:bg-white/5 ${
        interactive ? 'cursor-pointer text-start hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-ring' : ''
      } ${className}`}
    >
      {children}
    </Component>
  )
}
