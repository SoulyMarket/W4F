import { Skeleton } from './Skeleton'
import { TableContainer } from './TableContainer'

// Shared across every table-shaped list (reports/users/audit/territories)
// — same row count (5, a reasonable "about one screenful") and column
// widths loosely match a typical row (a short label, a longer one, a
// status pill, a date) without needing one bespoke skeleton per page.
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <TableContainer>
      <tbody className="divide-y divide-border">
        {Array.from({ length: rows }, (_, row) => (
          <tr key={row} aria-hidden="true">
            <td className="px-4 py-3">
              <Skeleton className="h-4 w-24" />
            </td>
            <td className="px-4 py-3">
              <Skeleton className="h-4 w-36" />
            </td>
            <td className="px-4 py-3">
              <Skeleton className="h-5 w-16 rounded-full" />
            </td>
            <td className="px-4 py-3">
              <Skeleton className="h-4 w-20" />
            </td>
          </tr>
        ))}
      </tbody>
    </TableContainer>
  )
}
