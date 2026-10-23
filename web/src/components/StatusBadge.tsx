// Semantic (not cycled) colors — a single badge has no neighboring bars
// to tell apart, so here the color itself should hint at meaning: red for
// a dead end, green for a positive outcome, blue for "making progress".
const REPORT_STATUS_COLOR: Record<string, string> = {
  submitted: '#64748b',
  under_review: '#f59e0b',
  recheck_requested: '#ea580c',
  validated: '#0284c7',
  rejected: '#dc2626',
  converted_to_project: '#16a34a',
}

const PROJECT_STATUS_COLOR: Record<string, string> = {
  new: '#64748b',
  in_study: '#f59e0b',
  approved: '#0284c7',
  in_preparation: '#0891b2',
  in_progress: '#2563eb',
  completed: '#16a34a',
  cancelled: '#dc2626',
}

export function StatusBadge({ status, label, kind }: { status: string; label: string; kind: 'report' | 'project' }) {
  const color = (kind === 'report' ? REPORT_STATUS_COLOR : PROJECT_STATUS_COLOR)[status] ?? '#64748b'
  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium text-white"
      style={{ backgroundColor: color }}
    >
      {label}
    </span>
  )
}
