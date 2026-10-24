import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { useLocation, useOutlet } from 'react-router-dom'

// A short cross-fade + rise between routes, keyed by pathname so
// AnimatePresence treats each page as its own exit/enter pair rather
// than diffing DOM nodes between two unrelated screens. useOutlet()
// (not <Outlet/> directly) is what lets the OLD page keep rendering
// during its own exit animation after the route has already changed.
export function PageTransition() {
  const location = useLocation()
  const outlet = useOutlet()
  const prefersReducedMotion = useReducedMotion()

  if (prefersReducedMotion) return outlet

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        transition={{ duration: 0.18, ease: 'easeOut' }}
      >
        {outlet}
      </motion.div>
    </AnimatePresence>
  )
}
