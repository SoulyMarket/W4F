import { Card } from './Card'
import { Skeleton } from './Skeleton'

// Shared by ReportDetailPage and ProjectDetailPage — both are "back
// link, title, a data card of label/value pairs, a second section card"
// in shape, so one skeleton serves both instead of two near-duplicates.
export function DetailPageSkeleton() {
  return (
    <div className="flex flex-col gap-4" aria-hidden="true">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-8 w-56" />
      <Card>
        <Skeleton className="mb-4 h-4 w-24" />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {Array.from({ length: 6 }, (_, i) => (
            <div key={i} className="flex flex-col gap-1.5">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-4 w-32" />
            </div>
          ))}
        </div>
      </Card>
      <Card index={1}>
        <Skeleton className="mb-4 h-4 w-24" />
        <Skeleton className="h-16 w-full" />
      </Card>
    </div>
  )
}
