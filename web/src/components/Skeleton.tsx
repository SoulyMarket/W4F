// A plain "جارٍ التحميل…" line was every page's loading state — correct,
// but it tells the viewer nothing about what's about to appear and reads
// as the least-finished part of the screen. A shaped skeleton (matching
// the real content's layout) instead reserves the right space (no layout
// shift once data arrives, pre-delivery checklist's CLS guidance) and
// reads as considerably more premium — this is the single highest-
// leverage "perceived performance" change from the ui-ux-pro-max pass.
export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-muted ${className}`} aria-hidden="true" />
}

export function SkeletonText({ className = '' }: { className?: string }) {
  return <Skeleton className={`h-4 w-full ${className}`} />
}
